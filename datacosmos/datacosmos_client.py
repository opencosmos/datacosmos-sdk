"""Client to interact with the Datacosmos API with authentication and request handling."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from requests_oauthlib import OAuth2Session

from datacosmos.config.config import Config
from datacosmos.exceptions.datacosmos_exception import DatacosmosException


class DatacosmosClient:
    """Client to interact with the Datacosmos API with authentication and request handling."""

    def __init__(
        self,
        config: Optional[Config | Any] = None,
        http_session: Optional[requests.Session | OAuth2Session] = None,
    ):
        """Initialize the DatacosmosClient.

        Args:
            config: SDK configuration (if omitted, Config() loads YAML + env).
            http_session: Pre-authenticated session (OAuth2Session or requests.Session
                          with 'Authorization: Bearer ...').
        """
        self.config = self._coerce_config(config)
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        if http_session is not None:
            self._init_with_injected_session(http_session)
            return

        self._owns_session = True
        self._http_client = self._authenticate_and_initialize_client()

    # --------------------------- init helpers ---------------------------

    def _coerce_config(self, cfg: Optional[Config | Any]) -> Config:
        """Normalize various config inputs into a Config instance."""
        if cfg is None:
            return Config()
        if isinstance(cfg, Config):
            return cfg
        if isinstance(cfg, dict):
            return Config(**cfg)
        try:
            return Config.model_validate(cfg)  # pydantic v2
        except Exception as e:
            raise DatacosmosException(
                "Invalid config provided to DatacosmosClient"
            ) from e

    def _init_with_injected_session(
        self, http_session: requests.Session | OAuth2Session
    ) -> None:
        """Adopt a caller-provided session and extract token/expiry."""
        self._http_client = http_session
        self._owns_session = False

        token_data = self._extract_token_data(http_session)
        self.token = token_data.get("access_token")
        if not self.token:
            raise DatacosmosException(
                "Failed to extract access token from injected session"
            )

        self.token_expiry = self._compute_expiry(
            token_data.get("expires_at"),
            token_data.get("expires_in"),
        )

    def _extract_token_data(
        self, http_session: requests.Session | OAuth2Session
    ) -> dict:
        """Return {'access_token', 'expires_at'?, 'expires_in'?} from the session."""
        if isinstance(http_session, OAuth2Session):
            return getattr(http_session, "token", {}) or {}

        if isinstance(http_session, requests.Session):
            auth_header = http_session.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise DatacosmosException(
                    "Injected requests.Session must include a 'Bearer' token in its headers"
                )
            return {"access_token": auth_header.split(" ", 1)[1]}

        raise DatacosmosException(f"Unsupported session type: {type(http_session)}")

    def _compute_expiry(
        self,
        expires_at: Optional[datetime | int | float],
        expires_in: Optional[int | float],
    ) -> Optional[datetime]:
        """Normalize expiry inputs to an absolute UTC datetime (or None)."""
        if isinstance(expires_at, datetime):
            return expires_at
        if isinstance(expires_at, (int, float)):
            return datetime.fromtimestamp(expires_at, tz=timezone.utc)
        if expires_in is not None:
            try:
                return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            except (TypeError, ValueError):
                return None
        return None

    # --------------------------- auth/session ---------------------------

    def _authenticate_and_initialize_client(self) -> requests.Session:
        """Authenticate and initialize the HTTP client with a valid token."""
        auth = self.config.authentication
        auth_type = getattr(auth, "type", "m2m")

        if auth_type == "m2m":
            return self.__build_m2m_session()

        if auth_type == "local":
            return self.__build_local_session()

        raise DatacosmosException(f"Unsupported authentication type: {auth_type}")

    def _refresh_token_if_needed(self):
        """Refresh the token if it has expired (only if SDK created it)."""
        if not getattr(self, "_owns_session", False):
            return
        now = datetime.now(timezone.utc)
        # Treat missing token or missing expiry as 'needs refresh'
        if (
            (not self.token)
            or (self.token_expiry is None)
            or (self.token_expiry <= now)
        ):
            self._http_client = self._authenticate_and_initialize_client()

    def __build_m2m_session(self) -> requests.Session:
        """Client Credentials (M2M) flow using requests-oauthlib."""
        auth = self.config.authentication
        try:
            client = BackendApplicationClient(client_id=auth.client_id)
            oauth_session = OAuth2Session(client=client)

            token_response = oauth_session.fetch_token(
                token_url=auth.token_url,
                client_id=auth.client_id,
                client_secret=auth.client_secret,
                audience=auth.audience,
            )

            self.token = token_response["access_token"]
            expires_at = token_response.get("expires_at")
            if isinstance(expires_at, (int, float)):
                self.token_expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            else:
                self.token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=int(token_response.get("expires_in", 3600))
                )

            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {self.token}"})
            return http_client

        except (HTTPError, ConnectionError, Timeout) as e:
            raise DatacosmosException(f"Authentication failed: {e}") from e
        except RequestException as e:
            raise DatacosmosException(
                f"Unexpected request failure during authentication: {e}"
            ) from e

    def __build_local_session(self) -> requests.Session:
        """Interactive local login via LocalTokenFetcher (cached + refresh)."""
        auth = self.config.authentication
        try:
            from datacosmos.auth.local_token_fetcher import LocalTokenFetcher

            fetcher = LocalTokenFetcher(
                client_id=auth.client_id,
                authorization_endpoint=auth.authorization_endpoint,
                token_endpoint=auth.token_endpoint,
                redirect_port=int(auth.redirect_port),
                audience=auth.audience,
                scopes=auth.scopes,
                token_file=Path(auth.cache_file).expanduser(),
            )
            tok = fetcher.get_token()
        except Exception as e:
            raise DatacosmosException(f"Local authentication failed: {e}") from e

        self.token = tok.access_token
        self.token_expiry = datetime.fromtimestamp(tok.expires_at, tz=timezone.utc)

        http_client = requests.Session()
        http_client.headers.update({"Authorization": f"Bearer {self.token}"})

        # keep for potential reuse in refresh path (optional)
        self._local_token_fetcher = fetcher
        return http_client

    # --------------------------- request API ---------------------------

    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> requests.Response:
        """Send an HTTP request using the authenticated session."""
        self._refresh_token_if_needed()
        try:
            response = self._http_client.request(method, url, *args, **kwargs)
            response.raise_for_status()
            return response
        except HTTPError as e:
            raise DatacosmosException(
                f"HTTP error during {method.upper()} request to {url}",
                response=e.response,
            ) from e
        except ConnectionError as e:
            raise DatacosmosException(
                f"Connection error during {method.upper()} request to {url}: {str(e)}"
            ) from e
        except Timeout as e:
            raise DatacosmosException(
                f"Request timeout during {method.upper()} request to {url}: {str(e)}"
            ) from e
        except RequestException as e:
            raise DatacosmosException(
                f"Unexpected request failure during {method.upper()} request to {url}: {str(e)}"
            ) from e

    def get(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """Send a GET request using the authenticated session."""
        return self.request("GET", url, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """Send a POST request using the authenticated session."""
        return self.request("POST", url, *args, **kwargs)

    def put(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """Send a PUT request using the authenticated session."""
        return self.request("PUT", url, *args, **kwargs)

    def patch(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """Send a PATCH request using the authenticated session."""
        return self.request("PATCH", url, *args, **kwargs)

    def delete(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """Send a DELETE request using the authenticated session."""
        return self.request("DELETE", url, *args, **kwargs)

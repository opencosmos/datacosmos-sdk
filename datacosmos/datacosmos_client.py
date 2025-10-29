"""Client to interact with the Datacosmos API with authentication and request handling."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, List, Optional

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from requests_oauthlib import OAuth2Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from datacosmos.auth.base_authenticator import BaseAuthenticator
from datacosmos.auth.local_authenticator import LocalAuthenticator
from datacosmos.auth.m2m_authenticator import M2MAuthenticator
from datacosmos.config.config import Config
from datacosmos.exceptions.datacosmos_error import DatacosmosError

_log = logging.getLogger(__name__)

RequestHook = Callable[[str, str, Any, Any], None]
ResponseHook = Callable[[requests.Response], None]


class DatacosmosClient:
    """Client to interact with the Datacosmos API with authentication and request handling."""

    TOKEN_EXPIRY_SKEW_SECONDS = 60

    def __init__(
        self,
        config: Optional[Config | Any] = None,
        http_session: Optional[requests.Session | OAuth2Session] = None,
        request_hooks: Optional[List[RequestHook]] = None,
        response_hooks: Optional[List[ResponseHook]] = None,
    ):
        """Initialize the DatacosmosClient.

        Args:
            config (Optional[Config]): Configuration object (only needed when SDK creates its own session).
            http_session (Optional[requests.Session]): Pre-authenticated session.
            request_hooks (Optional[List[RequestHook]]): A list of functions to be called before each request.
            response_hooks (Optional[List[ResponseHook]]): A list of functions to be called after each successful response.
        """
        self.config = self._coerce_config(config)
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self._refresh_lock = threading.Lock()
        self._authenticator: Optional[BaseAuthenticator] = None
        self._request_hooks = request_hooks or []
        self._response_hooks = response_hooks or []

        if http_session is not None:
            self._init_with_injected_session(http_session)
            return

        self._owns_session = True
        self._http_client = self._authenticate_and_initialize_client()

    # --------------------------- init helpers ---------------------------

    def _coerce_config(self, cfg: Optional[Config | Any]) -> Config:
        if cfg is None:
            return Config()
        if isinstance(cfg, Config):
            return cfg
        if isinstance(cfg, dict):
            return Config(**cfg)
        try:
            return Config.model_validate(cfg)
        except Exception as e:
            raise DatacosmosError("Invalid config provided to DatacosmosClient") from e

    def _init_with_injected_session(
        self, http_session: requests.Session | OAuth2Session
    ) -> None:
        self._http_client = http_session
        self._owns_session = False

        token_data = self._extract_token_data(http_session)
        self.token = token_data.get("access_token")
        if not self.token:
            raise DatacosmosError(
                "Failed to extract access token from injected session"
            )
        self.token_expiry = self._compute_expiry(
            token_data.get("expires_at"), token_data.get("expires_in")
        )

    def _extract_token_data(
        self, http_session: requests.Session | OAuth2Session
    ) -> dict:
        if isinstance(http_session, OAuth2Session):
            return getattr(http_session, "token", {}) or {}
        if isinstance(http_session, requests.Session):
            auth_header = http_session.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise DatacosmosError(
                    "Injected requests.Session must include a 'Bearer' token in its headers"
                )
            return {"access_token": auth_header.split(" ", 1)[1]}
        raise DatacosmosError(f"Unsupported session type: {type(http_session)}")

    def _compute_expiry(
        self,
        expires_at: Optional[datetime | int | float],
        expires_in: Optional[int | float],
    ) -> Optional[datetime]:
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

    # --------------------------- auth/session (refactored) ---------------------------

    def _authenticate_and_initialize_client(self) -> requests.Session:
        auth_type = getattr(self.config.authentication, "type", "m2m")
        if auth_type == "m2m":
            self._authenticator = M2MAuthenticator(self.config)
        elif auth_type == "local":
            self._authenticator = LocalAuthenticator(self.config)
        else:
            raise DatacosmosError(f"Unsupported authentication type: {auth_type}")

        auth_result = self._authenticator.authenticate_and_build_session()
        self.token = auth_result.token
        self.token_expiry = auth_result.token_expiry
        return auth_result.http_client

    # --------------------------- refresh logic (refactored) ---------------------------

    def _needs_refresh(self) -> bool:
        if not getattr(self, "_owns_session", False):
            return False
        if not self.token or self.token_expiry is None:
            return True
        return (self.token_expiry - datetime.now(timezone.utc)) <= timedelta(
            seconds=self.TOKEN_EXPIRY_SKEW_SECONDS
        )

    def _refresh_now(self) -> None:
        """Force refresh using the delegated authenticator."""
        with self._refresh_lock:
            if not self._needs_refresh():
                return

            if self._authenticator:
                auth_result = self._authenticator.refresh_token()
                self.token = auth_result.token
                self.token_expiry = auth_result.token_expiry
                self._http_client.headers.update(
                    {"Authorization": f"Bearer {self.token}"}
                )
            else:
                raise DatacosmosError(
                    "Cannot refresh token, no authenticator initialized."
                )

    def _refresh_token_if_needed(self) -> None:
        if self._needs_refresh():
            self._refresh_now()

    # --------------------------- request API ---------------------------

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        retry=retry_if_exception_type((ConnectionError, Timeout)),
    )
    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> requests.Response:
        """Send an HTTP request using the authenticated session (with auto-refresh and retries).

        Args:
            method (str): The HTTP method (e.g., "GET", "POST").
            url (str): The URL for the request.
            *args: Positional arguments for requests.request().
            **kwargs: Keyword arguments for requests.request().

        Returns:
            requests.Response: The HTTP response.

        Raises:
            DatacosmosError: For any HTTP or request-related errors.
        """
        self._refresh_token_if_needed()

        # Call pre-request hooks
        for hook in self._request_hooks:
            try:
                hook(method, url, *args, **kwargs)
            except Exception:
                _log.error("Request hook failed.", exc_info=True)

        try:
            response = self._http_client.request(method, url, *args, **kwargs)
            response.raise_for_status()

            # Call post-response hooks on success
            for hook in self._response_hooks:
                try:
                    hook(response)
                except Exception:
                    _log.error("Response hook failed.", exc_info=True)

            return response
        except HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403) and getattr(self, "_owns_session", False):
                self._refresh_now()
                retry_response = self._http_client.request(method, url, *args, **kwargs)
                try:
                    retry_response.raise_for_status()
                    return retry_response
                except HTTPError as e:
                    raise DatacosmosError(
                        f"HTTP error during {method.upper()} request to {url} after refresh",
                        response=e.response,
                    ) from e
            raise DatacosmosError(
                f"HTTP error during {method.upper()} request to {url}",
                response=getattr(e, "response", None),
            ) from e
        except RequestException as e:
            raise DatacosmosError(
                f"Unexpected request failure during {method.upper()} request to {url}: {e}"
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

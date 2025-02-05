"""DatacosmosClient handles authenticated interactions with the Datacosmos API.

Automatically manages token refreshing and provides HTTP convenience
methods.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from requests_oauthlib import OAuth2Session

from config.config import Config
from datacosmos.exceptions.datacosmos_exception import DatacosmosException


class DatacosmosClient:
    """Client to interact with the Datacosmos API with authentication and request handling."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the DatacosmosClient.

        Args:
            config (Optional[Config]): Configuration object.
        """
        if config:
            self.config = config
        else:
            try:
                self.config = Config.from_yaml()
            except ValueError:
                self.config = Config.from_env()

        self.token = None
        self.token_expiry = None
        self._http_client = self._authenticate_and_initialize_client()

    def _authenticate_and_initialize_client(self) -> requests.Session:
        """Authenticate and initialize the HTTP client with a valid token."""
        try:
            client = BackendApplicationClient(
                client_id=self.config.authentication.client_id
            )
            oauth_session = OAuth2Session(client=client)

            token_response = oauth_session.fetch_token(
                token_url=self.config.authentication.token_url,
                client_id=self.config.authentication.client_id,
                client_secret=self.config.authentication.client_secret,
                audience=self.config.authentication.audience,
            )

            self.token = token_response["access_token"]
            self.token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=token_response.get("expires_in", 3600)
            )

            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {self.token}"})
            return http_client
        except (HTTPError, ConnectionError, Timeout) as e:
            raise DatacosmosException(f"Authentication failed: {str(e)}") from e
        except RequestException as e:
            raise DatacosmosException(
                f"Unexpected request failure during authentication: {str(e)}"
            ) from e

    def _refresh_token_if_needed(self):
        """Refresh the token if it has expired."""
        if not self.token or self.token_expiry <= datetime.now(timezone.utc):
            self._http_client = self._authenticate_and_initialize_client()

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

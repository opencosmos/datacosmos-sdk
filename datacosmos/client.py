import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import RequestException

from config.config import Config


class DatacosmosClient:
    """
    DatacosmosClient handles authenticated interactions with the Datacosmos API.
    Automatically manages token refreshing and provides HTTP convenience methods.
    """

    def __init__(
        self, config: Optional[Config] = None, config_file: str = "config/config.yaml"
    ):
        """
        Initialize the DatacosmosClient.

        If no configuration is provided, it will load from the specified YAML file
        or fall back to environment variables.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.config = config or self._load_config(config_file)
        self.token = None
        self.token_expiry = None
        self._http_client = self._authenticate_and_initialize_client()

    def _load_config(self, config_file: str) -> Config:
        """
        Load configuration from the YAML file. Fall back to environment variables if the file is missing.
        """
        try:
            if os.path.exists(config_file):
                self.logger.info(f"Loading configuration from {config_file}")
                return Config.from_yaml(config_file)
            self.logger.info("Loading configuration from environment variables")
            return Config.from_env()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _authenticate_and_initialize_client(self) -> requests.Session:
        """
        Authenticate and initialize the HTTP client with a valid token.
        """
        try:
            self.logger.info("Authenticating with the token endpoint")
            client = BackendApplicationClient(client_id=self.config.client_id)
            oauth_session = OAuth2Session(client=client)

            # Fetch the token using client credentials
            token_response = oauth_session.fetch_token(
                token_url=self.config.token_url,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                audience=self.config.audience,
            )

            self.token = token_response["access_token"]
            self.token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=token_response.get("expires_in", 3600)
            )
            self.logger.info("Authentication successful, token obtained")

            # Initialize the HTTP session with the Authorization header
            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {self.token}"})
            return http_client
        except RequestException as e:
            self.logger.error(f"Request failed during authentication: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            raise

    def _refresh_token_if_needed(self):
        """
        Refresh the token if it has expired.
        """
        if not self.token or self.token_expiry <= datetime.now(timezone.utc):
            self.logger.info("Token expired or missing, refreshing token")
            self._http_client = self._authenticate_and_initialize_client()

    def get_http_client(self) -> requests.Session:
        """
        Return the authenticated HTTP client, refreshing the token if necessary.
        """
        self._refresh_token_if_needed()
        return self._http_client

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Send an HTTP request using the authenticated session.
        Logs request and response details.
        """
        self._refresh_token_if_needed()
        try:
            self.logger.info(f"Making {method.upper()} request to {url}")
            response = self._http_client.request(method, url, *args, **kwargs)
            response.raise_for_status()
            self.logger.info(f"Request to {url} succeeded with status {response.status_code}")
            return response
        except RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during HTTP request: {e}")
            raise

    def get(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Send a GET request using the authenticated session.
        """
        return self.request("GET", url, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Send a POST request using the authenticated session.
        """
        return self.request("POST", url, *args, **kwargs)

    def put(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Send a PUT request using the authenticated session.
        """
        return self.request("PUT", url, *args, **kwargs)

    def delete(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Send a DELETE request using the authenticated session.
        """
        return self.request("DELETE", url, *args, **kwargs)

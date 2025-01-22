import os

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from config.config import Config


class DatacosmosClient:
    def __init__(self, config: Optional[Config] = None, config_file: str = "config/config.yaml"):
        self.config = config or self._load_config(config_file)
        self.token = None
        self.token_expiry = None
        self._http_client = self._authenticate_and_initialize_client()

    def _load_config(self, config_file: str) -> Config:
        if os.path.exists(config_file):
            return Config.from_yaml(config_file)
        return Config.from_env()

    def _authenticate_and_initialize_client(self) -> requests.Session:
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
        self.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=token_response.get("expires_in", 3600))

        # Initialize the HTTP session with the Authorization header
        http_client = requests.Session()
        http_client.headers.update({"Authorization": f"Bearer {self.token}"})

        return http_client

    def _refresh_token_if_needed(self):
        """
        Refreshes the token if it has expired.
        """
        if not self.token or self.token_expiry <= datetime.now(timezone.utc):
            self._http_client = self._authenticate_and_initialize_client()

    def get_http_client(self) -> requests.Session:
        """
        Returns the authenticated HTTP client, refreshing the token if necessary.
        """
        self._refresh_token_if_needed()
        return self._http_client

    # Proxy HTTP methods to the underlying authenticated session
    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        """
        Proxy method to send HTTP requests using the authenticated session.
        """
        self._refresh_token_if_needed()
        return self._http_client.request(method, url, *args, **kwargs)

    def get(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, *args, **kwargs)

    def put(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self.request("PUT", url, *args, **kwargs)

    def delete(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", url, *args, **kwargs)

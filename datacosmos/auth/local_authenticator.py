"""Local (interactive/cached) authenticator for DatacosmosClient."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from datacosmos.auth.base_authenticator import AuthResult, BaseAuthenticator
from datacosmos.auth.local_token_fetcher import LocalTokenFetcher
from datacosmos.exceptions.datacosmos_error import DatacosmosError


class LocalAuthenticator(BaseAuthenticator):
    """Handles authentication via the interactive local login flow."""

    def __init__(self, config: Any):
        """Initializes a LocalAuthenticator instance.

        Args:
            config (Any): Configuration object containing authentication settings.
        """
        super().__init__(config)
        self._local_token_fetcher = self._init_fetcher()

    def _init_fetcher(self) -> LocalTokenFetcher:
        """Initializes the LocalTokenFetcher."""
        auth = self.config.authentication
        try:
            return LocalTokenFetcher(
                client_id=auth.client_id,
                authorization_endpoint=auth.authorization_endpoint,
                token_endpoint=auth.token_endpoint,
                redirect_port=int(auth.redirect_port),
                audience=auth.audience,
                scopes=auth.scopes,
                token_file=Path(auth.cache_file).expanduser(),
            )
        except Exception as e:
            raise DatacosmosError(f"Failed to initialize LocalTokenFetcher: {e}") from e

    def authenticate_and_build_session(self) -> AuthResult:
        """Builds an authenticated session using the local token fetcher."""
        try:
            tok = self._local_token_fetcher.get_token()
            token = tok.access_token
            token_expiry = datetime.fromtimestamp(tok.expires_at, tz=timezone.utc)
            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {token}"})
            return AuthResult(
                http_client=http_client, token=token, token_expiry=token_expiry
            )
        except Exception as e:
            raise DatacosmosError(f"Local authentication failed: {e}") from e

    def refresh_token(self) -> AuthResult:
        """Refreshes the local token non-interactively."""
        try:
            tok = self._local_token_fetcher.get_token()
            token = tok.access_token
            token_expiry = datetime.fromtimestamp(tok.expires_at, tz=timezone.utc)

            # Create a new session with the new token
            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {token}"})

            return AuthResult(
                http_client=http_client, token=token, token_expiry=token_expiry
            )
        except Exception as e:
            raise DatacosmosError(f"Local token refresh failed: {e}") from e

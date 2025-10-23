"""M2M (Machine-to-Machine) authenticator for DatacosmosClient."""
from datetime import datetime, timedelta, timezone

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from requests_oauthlib import OAuth2Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from datacosmos.auth.base_authenticator import AuthResult, BaseAuthenticator
from datacosmos.exceptions.datacosmos_error import DatacosmosError


class M2MAuthenticator(BaseAuthenticator):
    """Handles authentication using the Client Credentials (M2M) flow."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, Timeout)),
    )
    def authenticate_and_build_session(self) -> AuthResult:
        """Builds an authenticated session using the M2M flow."""
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
            token = token_response["access_token"]
            expires_at = token_response.get("expires_at")
            if isinstance(expires_at, (int, float)):
                token_expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            else:
                expires_in = int(token_response.get("expires_in", 3600))
                token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )

            http_client = requests.Session()
            http_client.headers.update({"Authorization": f"Bearer {token}"})
            return AuthResult(
                http_client=http_client, token=token, token_expiry=token_expiry
            )
        except (HTTPError, ConnectionError, Timeout) as e:
            raise DatacosmosError(f"M2M authentication failed: {e}") from e
        except RequestException as e:
            raise DatacosmosError(
                f"Unexpected request failure during M2M authentication: {e}"
            ) from e

    def refresh_token(self) -> AuthResult:
        """Refreshes the M2M token by re-running the authentication flow."""
        return self.authenticate_and_build_session()

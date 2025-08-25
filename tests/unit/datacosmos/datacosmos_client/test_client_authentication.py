from unittest.mock import Mock, patch

import pytest
import requests

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient


@pytest.mark.usefixtures("mock_fetch_token", "mock_auth_client")
class TestClientAuthentication:
    """Test suite for DatacosmosClient authentication."""

    @pytest.fixture
    def mock_fetch_token(self):
        """Fixture to mock OAuth2 token fetch."""
        with patch("datacosmos.datacosmos_client.OAuth2Session.fetch_token") as mock:
            mock.return_value = {
                "access_token": "mock-access-token",
                "expires_in": 3600,
            }
            yield mock

    @pytest.fixture
    def mock_auth_client(self, mock_fetch_token):
        """Fixture to mock the authentication client initialization."""
        with patch(
            "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client",
            autospec=True,
        ) as mock:

            def mock_authenticate(self):
                """Simulate authentication by setting token values."""
                token_response = mock_fetch_token.return_value
                self.token = token_response["access_token"]
                self.token_expiry = "mock-expiry"

            mock.side_effect = mock_authenticate
            yield mock

    def test_authentication_with_explicit_config(self):
        """Test authentication when explicitly providing Config."""
        config = Config(
            authentication=M2MAuthenticationConfig(
                type="m2m",
                client_id="test-client-id",
                client_secret="test-client-secret",
                token_url="https://mock.token.url/oauth/token",
                audience="https://mock.audience",
            )
        )

        client = DatacosmosClient(config=config)

        assert client.token == "mock-access-token"
        assert client.token_expiry == "mock-expiry"

    def test_injected_http_session_is_used_and_not_reauthenticated(self):
        """Test that providing a pre-authenticated session skips SDK auth flow."""
        config = Config(
            authentication=M2MAuthenticationConfig(
                type="m2m",
                client_id="test-client-id",
                client_secret="test-client-secret",
                token_url="https://mock.token.url/oauth/token",
                audience="https://mock.audience",
            )
        )
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer injected-token"})

        # 2) Patch the SDK's internal auth method to fail if called
        with patch.object(
            DatacosmosClient,
            "_authenticate_and_initialize_client",
            side_effect=AssertionError("Should not re-authenticate"),
        ):
            client = DatacosmosClient(http_session=session, config=config)

        assert client._owns_session is False
        assert client.token == "injected-token"
        assert client.token_expiry is None

        mock_response = Mock(spec=requests.Response)
        mock_response.raise_for_status.return_value = None
        session.request = Mock(return_value=mock_response)

        result = client.request("GET", "https://example.com")
        assert result is mock_response

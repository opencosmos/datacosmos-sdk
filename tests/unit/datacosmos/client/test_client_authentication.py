from unittest.mock import patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient


@patch("datacosmos.client.OAuth2Session.fetch_token")
@patch(
    "datacosmos.client.DatacosmosClient._authenticate_and_initialize_client",
    autospec=True,
)
def test_client_authentication(mock_auth_client, mock_fetch_token):
    """Test that the client correctly fetches a token during authentication."""
    # Mock the token response from OAuth2Session
    mock_fetch_token.return_value = {
        "access_token": "mock-access-token",
        "expires_in": 3600,
    }

    # Simulate _authenticate_and_initialize_client calling fetch_token
    def mock_authenticate_and_initialize_client(self):
        # Call the real fetch_token (simulated by the mock)
        token_response = mock_fetch_token(
            token_url=self.config.authentication.token_url,
            client_id=self.config.authentication.client_id,
            client_secret=self.config.authentication.client_secret,
            audience=self.config.authentication.audience,
        )
        self.token = token_response["access_token"]
        self.token_expiry = "mock-expiry"

    # Attach the side effect to the mock
    mock_auth_client.side_effect = mock_authenticate_and_initialize_client

    # Create a mock configuration
    config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://mock.token.url/oauth/token",
            audience="https://mock.audience",
        )
    )

    # Initialize the client
    client = DatacosmosClient(config=config)

    # Assertions
    assert client.token == "mock-access-token"
    assert client.token_expiry == "mock-expiry"
    mock_fetch_token.assert_called_once_with(
        token_url="https://mock.token.url/oauth/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        audience="https://mock.audience",
    )
    mock_auth_client.assert_called_once_with(client)
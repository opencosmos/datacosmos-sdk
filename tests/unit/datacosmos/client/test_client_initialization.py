from unittest.mock import MagicMock, patch

from config.config import Config
from datacosmos.client import DatacosmosClient


@patch(
    "datacosmos.client.DatacosmosClient._authenticate_and_initialize_client"
)
@patch("os.path.exists", return_value=False)
@patch("config.Config.from_env")
def test_client_initialization(mock_from_env, mock_exists, mock_auth_client):
    """Test that the client initializes correctly with environment variables
    and mocks the HTTP client."""
    mock_config = Config(
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://mock.token.url/oauth/token",
        audience="https://mock.audience",
    )
    mock_from_env.return_value = mock_config
    mock_auth_client.return_value = MagicMock()  # Mock the HTTP client

    client = DatacosmosClient()

    assert client.config == mock_config
    assert client._http_client is not None  # Ensure the HTTP client is mocked
    mock_exists.assert_called_once_with("config/config.yaml")
    mock_from_env.assert_called_once()
    mock_auth_client.assert_called_once()

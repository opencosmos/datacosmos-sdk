from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient


@patch("datacosmos.client.DatacosmosClient._authenticate_and_initialize_client")
def test_client_initialization(mock_auth_client):
    """Test that the client initializes correctly with environment variables
    and mocks the HTTP client."""
    mock_config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="zCeZWJamwnb8ZIQEK35rhx0hSAjsZI4D",
            token_url="https://login.open-cosmos.com/oauth/token",
            audience="https://test.beeapp.open-cosmos.com",
            client_secret="tAeaSgLds7g535ofGq79Zm2DSbWMCOsuRyY5lbyObJe9eAeSN_fxoy-5kaXnVSYa",
        )
    )
    mock_auth_client.return_value = MagicMock()  # Mock the HTTP client

    client = DatacosmosClient()

    assert client.config == mock_config
    assert client._http_client is not None  # Ensure the HTTP client is mocked
    mock_auth_client.assert_called_once()
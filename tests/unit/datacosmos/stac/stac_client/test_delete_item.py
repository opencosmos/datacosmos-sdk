from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "delete")
@patch("datacosmos.stac.stac_client.check_api_response")
def test_delete_item(mock_check_api_response, mock_delete, mock_fetch_token):
    """Test deleting a STAC item."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 204  # Successful deletion
    mock_delete.return_value = mock_response

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
    stac_client = STACClient(client)

    stac_client.delete_item("item-1", "test-collection")

    mock_delete.assert_called_once()
    mock_check_api_response.assert_called_once()

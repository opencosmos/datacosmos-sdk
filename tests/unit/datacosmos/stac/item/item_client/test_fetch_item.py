from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.item.item_client.check_api_response")
@patch.object(DatacosmosClient, "get")
def test_fetch_item(mock_get, mock_check_api_response, mock_fetch_token):
    """Test fetching a single STAC item by ID."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "item-1",
        "collection": "test-collection",
        "type": "Feature",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {"datetime": "2023-12-01T12:00:00Z"},
        "assets": {},
        "links": [],
    }
    mock_get.return_value = mock_response

    mock_check_api_response.return_value = None

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
    stac_client = ItemClient(client)

    item = stac_client.fetch_item("item-1", "test-collection")

    assert item.id == "item-1"
    assert item.properties["datetime"] == "2023-12-01T12:00:00Z"
    mock_get.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)

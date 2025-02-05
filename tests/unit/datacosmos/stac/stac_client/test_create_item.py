from unittest.mock import MagicMock, patch

from pystac import Item

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "post")
@patch("datacosmos.stac.stac_client.check_api_response")
def test_create_item(mock_check_api_response, mock_post, mock_fetch_token):
    """Test creating a new STAC item."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
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
    mock_post.return_value = mock_response

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

    item = Item.from_dict(mock_response.json())
    created_item = stac_client.create_item("test-collection", item)

    assert created_item.id == "item-1"
    assert created_item.properties["datetime"] == "2023-12-01T12:00:00Z"
    mock_post.assert_called_once()
    mock_check_api_response.assert_called_once()

from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient
from datacosmos.stac.models.item_update import ItemUpdate
from datacosmos.stac.stac_client import STACClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "patch")
@patch("datacosmos.stac.stac_client.check_api_response")
def test_update_item(mock_check_api_response, mock_patch, mock_fetch_token):
    """Test updating an existing STAC item."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "item-1",
        "collection": "test-collection",
        "type": "Feature",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {"datetime": "2023-12-01T12:00:00Z", "new_property": "value"},
        "assets": {},
        "links": [],
    }
    mock_patch.return_value = mock_response

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

    update_data = ItemUpdate(properties={"new_property": "value"})
    updated_item = stac_client.update_item("item-1", "test-collection", update_data)

    assert updated_item.id == "item-1"
    assert updated_item.properties["new_property"] == "value"
    mock_patch.assert_called_once()
    mock_check_api_response.assert_called_once()

from unittest.mock import MagicMock, patch
from datacosmos.client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient
from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "get")
def test_fetch_item(mock_get, mock_fetch_token):
    """Test fetching a single STAC item by ID."""
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
    mock_get.return_value = mock_response

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

    item = stac_client.fetch_item("item-1", "test-collection")

    assert item.id == "item-1"
    assert item.properties["datetime"] == "2023-12-01T12:00:00Z"
    mock_get.assert_called_once()

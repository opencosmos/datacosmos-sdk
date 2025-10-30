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
        "id": "S2B_MSIL1C_20230101T103009_N0509_R065_T31TEJ_20230101T115310",
        "type": "Feature",
        "stac_version": "1.0.0",
        "stac_extensions": [
            "https://stac-extensions.github.io/sat/v1.0.0/schema.json",
            "https://stac-extensions.github.io/processing/v1.0.0/schema.json",
        ],
        "collection": "sentinel-2-l1c",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[2.1, 42.0], [2.1, 42.5], [2.6, 42.5], [2.6, 42.0], [2.1, 42.0]]
            ],
        },
        "bbox": [2.1, 42.0, 2.6, 42.5],
        "properties": {
            "datetime": "2023-01-01T10:30:09Z",
            "processing:level": "L1C",
            "sat:platform_international_designator": "2017-038A",
            "mission": "Sentinel-2",
            "cloud_cover": 0.5,
        },
        "links": [
            {
                "rel": "self",
                "href": "https://example.com/stac/items/S2B_MSIL1C_20230101T103009_N0509_R065_T31TEJ_20230101T115310.json",
                "type": "application/json",
            },
            {
                "rel": "parent",
                "href": "https://example.com/stac/collections/sentinel-2-l1c",
                "type": "application/json",
            },
        ],
        "assets": {
            "visual": {
                "href": "https://example.com/data/S2B_MSIL1C/visual.tif",
                "type": "image/tiff; application=geotiff",
                "title": "True Color Visual",
                "description": "A true-color composite derived from bands B4, B3, and B2.",
                "roles": ["visual", "data"],
            }
        },
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

    assert item.id == "S2B_MSIL1C_20230101T103009_N0509_R065_T31TEJ_20230101T115310"
    assert item.properties["datetime"] == "2023-01-01T10:30:09Z"
    mock_get.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)

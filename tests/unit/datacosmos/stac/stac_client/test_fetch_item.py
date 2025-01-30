from unittest.mock import patch, MagicMock
from datacosmos.stac.stac_client import STACClient
from datacosmos.client import DatacosmosClient


@patch.object(DatacosmosClient, "get")
def test_fetch_item(mock_get):
    """Test fetching a single STAC item by ID."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "item-1",
        "collection": "test-collection",
        "type": "Feature",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {
            "datetime": "2023-12-01T12:00:00Z"
        },
        "assets": {},
        "links": []
    }
    mock_get.return_value = mock_response

    client = DatacosmosClient()
    stac_client = STACClient(client)

    item = stac_client.fetch_item("item-1", "test-collection")

    assert item.id == "item-1"
    assert item.properties["datetime"] == "2023-12-01T12:00:00Z"
    mock_get.assert_called_once()

from unittest.mock import patch, MagicMock
from datacosmos.stac.stac_client import STACClient
from datacosmos.stac.models.search_parameters import SearchParameters
from datacosmos.client import DatacosmosClient


@patch.object(DatacosmosClient, "post")
def test_search_items(mock_post):
    """Test searching STAC items with filters and pagination."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
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
        ],
        "links": []
    }
    mock_post.return_value = mock_response

    client = DatacosmosClient()
    stac_client = STACClient(client)
    parameters = SearchParameters(collections=["test-collection"])

    results = list(stac_client.search_items(parameters))

    assert len(results) == 1
    assert results[0].id == "item-1"
    mock_post.assert_called_once()

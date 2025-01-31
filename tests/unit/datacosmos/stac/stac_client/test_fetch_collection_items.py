from unittest.mock import MagicMock, patch

from datacosmos.client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient


@patch.object(STACClient, "search_items")
def test_fetch_collection_items(mock_search_items):
    """Test fetching all items in a collection."""
    mock_search_items.return_value = iter(
        [
            MagicMock(id="item-1"),
            MagicMock(id="item-2"),
        ]
    )

    client = DatacosmosClient()
    stac_client = STACClient(client)

    results = list(stac_client.fetch_collection_items("test-collection"))

    assert len(results) == 2
    assert results[0].id == "item-1"
    assert results[1].id == "item-2"
    mock_search_items.assert_called_once()

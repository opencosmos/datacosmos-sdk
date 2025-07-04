"""Unified interface for STAC API, combining Item & Collection operations."""

from datacosmos.stac.collection.collection_client import CollectionClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.storage.storage_client import StorageClient


class STACClient(ItemClient, CollectionClient, StorageClient):
    """Unified interface for STAC API, combining Item & Collection operations."""

    def __init__(self, client):
        """Initialize the STACClient with a DatacosmosClient."""
        ItemClient.__init__(self, client)
        CollectionClient.__init__(self, client)
        StorageClient.__init__(self, client)

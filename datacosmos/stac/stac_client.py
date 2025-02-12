"""Unified interface for STAC API, combining Item & Collection operations."""

from datacosmos.stac.collection.collection_client import CollectionClient
from datacosmos.stac.item.item_client import ItemClient


class STACClient(ItemClient, CollectionClient):
    """Unified interface for STAC API, combining Item & Collection operations."""

    def __init__(self, client):
        """Initialize the STACClient with a DatacosmosClient."""
        super().__init__(client)

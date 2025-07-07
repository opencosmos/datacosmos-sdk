"""Generic StorageClient for all storage operations (upload, download, etc.)."""

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.storage.uploader import Uploader


class StorageClient:
    """Generic StorageClient for all storage operations (upload, download, etc.)."""

    def __init__(self, client: DatacosmosClient):
        """Generic StorageClient for all storage operations (upload, download, etc.)."""
        self.client = client
        self.uploader = Uploader(client)

    def upload_item(self, *args, **kwargs):
        """Proxy to Uploader.upload_item, without needing to pass client each call."""
        return self.uploader.upload_item(*args, **kwargs)

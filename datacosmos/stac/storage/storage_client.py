"""Generic StorageClient for all storage operations (upload, download, etc.)."""

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.uploader import Uploader


class StorageClient:
    """Generic StorageClient for all storage operations (upload, download, etc.)."""

    def __init__(self, client: DatacosmosClient):
        """Generic StorageClient for all storage operations (upload, download, etc.)."""
        self.client = client
        self.uploader = Uploader(client)

    def upload_item(
        self,
        item: DatacosmosItem,
        assets_path: str | None = None,
        included_assets: list[str] | bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
    ) -> DatacosmosItem:
        """Proxy to Uploader.upload_item, without needing to pass client each call."""
        return self.uploader.upload_item(
            item=item,
            assets_path=assets_path,
            included_assets=included_assets,
            max_workers=max_workers,
            time_out=time_out,
        )

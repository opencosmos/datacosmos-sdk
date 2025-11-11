"""Generic StorageClient for all storage operations (upload, download, etc.)."""

from typing import Any, Callable, Optional

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.upload_result import UploadResult
from datacosmos.stac.storage.downloader import Downloader
from datacosmos.stac.storage.uploader import Uploader


class StorageClient:
    """Generic StorageClient for all storage operations (upload, download, etc.)."""

    def __init__(self, client: DatacosmosClient):
        """Generic StorageClient for all storage operations (upload, download, etc.)."""
        self.client = client
        self.uploader = Uploader(client)
        self.downloader = Downloader(client)

    def upload_item(
        self,
        item: DatacosmosItem,
        project_id: str,
        assets_path: str | None = None,
        included_assets: list[str] | bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
        on_error: Optional[Callable[[Asset, Exception], None]] = None,
    ) -> UploadResult:
        """Proxy to Uploader.upload_item, without needing to pass client each call."""
        return self.uploader.upload_item(
            item=item,
            project_id=project_id,
            assets_path=assets_path,
            included_assets=included_assets,
            max_workers=max_workers,
            time_out=time_out,
            on_error=on_error,
        )

    def download_assets(
        self,
        item: str,
        collection_id: str,
        target_path: str | None = None,
        included_assets: list[str] | bool = True,
        overwrite: bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
    ) -> tuple[DatacosmosItem, list[dict[str, str]], list[dict[str, Any]]]:
        """Proxy to Downloader.download_assets, without needing to pass client each call."""
        return self.downloader.download_assets(
            item=item,
            collection_id=collection_id,
            target_path=target_path,
            included_assets=included_assets,
            overwrite=overwrite,
            max_workers=max_workers,
            time_out=time_out,
        )

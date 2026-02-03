"""Generic StorageClient for all storage operations (upload, download, delete)."""

from typing import Any, Callable, Optional

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.delete_error import DeleteError
from datacosmos.exceptions.item_error import ItemNotFoundError
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.delete_result import DeleteResult
from datacosmos.stac.storage.dataclasses.upload_result import UploadResult
from datacosmos.stac.storage.downloader import Downloader
from datacosmos.stac.storage.uploader import Uploader


class StorageClient:
    """Generic StorageClient for all storage operations (upload, download, delete)."""

    def __init__(self, client: DatacosmosClient):
        """Generic StorageClient for all storage operations (upload, download, delete)."""
        self.client = client
        self.uploader = Uploader(client)
        self.downloader = Downloader(client)
        self._item_client = ItemClient(client)

    def upload_item(
        self,
        item: DatacosmosItem,
        project_id: str | None = None,
        collection_id: str | None = None,
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
            collection_id=collection_id,
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

    def delete_file(self, path: str) -> None:
        """Delete a file from Datacosmos storage.

        Args:
            path: The storage path or full URL of the file to delete.

        Raises:
            StorageError: If the delete operation fails.
        """
        # Use uploader's base class method (StorageBase.delete_file)
        self.uploader.delete_file(path)

    def delete_item_with_assets(
        self,
        item_id: str,
        collection_id: str,
        delete_from_storage: bool = True,
        max_workers: int = 4,
    ) -> DeleteResult:
        """Delete a STAC item and optionally its assets from storage.

        This method performs the following steps:
        1. Fetches the item to get asset URLs
        2. Deletes each asset file from storage (if delete_from_storage=True)
        3. Deletes the STAC item metadata from the catalog

        Args:
            item_id: The ID of the item to delete.
            collection_id: The ID of the collection containing the item.
            delete_from_storage: Whether to delete asset files from storage.
                Defaults to True.
            max_workers: Maximum number of parallel threads for asset deletion.

        Returns:
            DeleteResult: Contains the deleted item, success/failure status for
                item and each asset.

        Raises:
            ItemNotFoundError: If the item does not exist.
            DeleteError: If the item metadata deletion fails.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from requests.exceptions import HTTPError

        # Step 1: Fetch the item to get asset URLs
        try:
            item = self._item_client.fetch_item(item_id, collection_id)
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                raise ItemNotFoundError(
                    message="Item not found",
                    item_id=item_id,
                    collection_id=collection_id,
                    response=e.response,
                ) from e
            raise

        successful_assets: list[str] = []
        failed_assets: list[dict[str, Any]] = []

        # Step 2: Delete assets from storage (if requested)
        if delete_from_storage and item.assets:

            def delete_asset(asset_key: str, asset: Asset) -> str:
                self.delete_file(asset.href)
                return asset_key

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_key = {
                    executor.submit(delete_asset, key, asset): key
                    for key, asset in item.assets.items()
                }

                for future in as_completed(future_to_key):
                    asset_key = future_to_key[future]
                    try:
                        future.result()
                        successful_assets.append(asset_key)
                    except Exception as e:
                        failed_assets.append({
                            "asset_key": asset_key,
                            "error": str(e),
                            "exception": e,
                        })

        # Step 3: Delete item metadata
        item_deleted = False
        try:
            self._item_client.delete_item(item_id, collection_id)
            item_deleted = True
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                # Item already deleted, consider it a success
                item_deleted = True
            else:
                raise DeleteError(
                    message="Failed to delete item metadata",
                    item_id=item_id,
                    collection_id=collection_id,
                    failed_assets=failed_assets,
                    response=e.response,
                ) from e

        return DeleteResult(
            item=item,
            item_deleted=item_deleted,
            successful_assets=successful_assets,
            failed_assets=failed_assets,
        )

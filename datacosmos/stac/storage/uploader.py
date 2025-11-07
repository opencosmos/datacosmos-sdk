"""Handles uploading files to Datacosmos storage and registering STAC items."""

from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import TypeAdapter

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.upload_path import UploadPath
from datacosmos.stac.storage.dataclasses.upload_result import UploadResult
from datacosmos.stac.storage.storage_base import StorageBase

AssetErrorCallback = Callable[[Asset, Exception], None]


class Uploader(StorageBase):
    """Upload a STAC item and its assets to Datacosmos storage and register the item in the STAC API."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the uploader.

        Args:
            client (DatacosmosClient): Pre-configured DatacosmosClient.
        """
        super().__init__(client)
        self.item_client = ItemClient(client)

    def upload_item(
        self,
        item: DatacosmosItem | str,
        project_id: str,
        assets_path: str | None = None,
        included_assets: list[str] | bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
        on_error: Optional[AssetErrorCallback] = None,
    ) -> UploadResult:
        """Upload a STAC item (and optionally its assets) to Datacosmos in parallel threads.

        Args:
            item (DatacosmosItem | str):
                - a DatacosmosItem instance, or
                - the path to an item JSON file on disk.
            project_id (str): The project ID to upload assets to.
            assets_path (str | None): Base directory where local asset files are located.
            included_assets (list[str] | bool):
                - True → upload every asset in the item.
                - list[str] → upload only the asset keys in that list.
                - False → skip asset upload; just register the item.
            max_workers (int): Maximum number of parallel threads for asset upload.
            time_out (float): Timeout in seconds for the entire asset batch upload.
            on_error: (Optional[Callable[[Asset, Exception], None]]): Optional callback function
                      invoked for each failed asset upload, receiving the failed Asset object and
                      the Exception that caused the failure.

        Returns:
            UploadResult: The final item, along with lists of successful and failed asset keys.
        """
        if not assets_path and not isinstance(item, str):
            raise ValueError(
                "assets_path must be provided if item is not the path to an item file."
            )

        if isinstance(item, str):
            item_filename = item
            item = self._load_item(item_filename)
            assets_path = assets_path or str(Path(item_filename).parent)

        if not isinstance(item, DatacosmosItem):
            raise TypeError(f"item must be a DatacosmosItem, got {type(item).__name__}")

        assets_path = assets_path or str(Path.cwd())

        upload_assets = self._resolve_upload_assets(item, included_assets)

        jobs = [
            (item, asset_key, assets_path, project_id) for asset_key in upload_assets
        ]

        if not jobs:
            self.item_client.add_item(item)
            return UploadResult(item=item, successful_assets=[], failed_assets=[])

        successful_keys, raw_failures = self.run_in_threads(
            self._upload_asset, jobs, max_workers, time_out
        )

        self._process_failures(item, raw_failures, on_error)

        if successful_keys:
            self.item_client.add_item(item)

        return UploadResult(
            item=item,
            successful_assets=successful_keys,
            failed_assets=raw_failures,
        )

    def _resolve_upload_assets(
        self, item: DatacosmosItem, included_assets: list[str] | bool
    ) -> list[str]:
        """Resolves the final list of asset keys to be uploaded based on included_assets."""
        if included_assets is False:
            return []
        elif included_assets is True:
            return list(item.assets.keys())
        elif isinstance(included_assets, list):
            return included_assets
        else:
            return []

    def _process_failures(
        self,
        item: DatacosmosItem,
        raw_failures: list[dict[str, Any]],
        on_error: Optional[AssetErrorCallback],
    ) -> None:
        """Executes the on_error callback for each failed asset."""
        if on_error:
            for failure in raw_failures:
                job_args = failure.get("job_args") or ()
                asset_key_failed = job_args[1] if len(job_args) > 1 else None
                exception = failure.get("exception")

                if asset_key_failed and exception:
                    asset_failed = item.assets.get(asset_key_failed)

                    if asset_failed:
                        on_error(asset_failed, exception)

    @staticmethod
    def _load_item(item_json_file_path: str) -> DatacosmosItem:
        """Load a DatacosmosItem from a JSON file on disk."""
        with open(item_json_file_path, "rb") as file:
            data = file.read().decode("utf-8")
        return TypeAdapter(DatacosmosItem).validate_json(data)

    def upload_from_file(
        self, src: str, dst: str, mime_type: str | None = None
    ) -> None:
        """Upload a single file to the specified destination path in storage."""
        url = self.base_url.with_suffix(dst)
        mime = mime_type or self._guess_mime(src)
        headers = {"Content-Type": mime}
        with open(src, "rb") as f:
            response = self.client.put(url, data=f, headers=headers)
        response.raise_for_status()

    def _upload_asset(
        self, item: DatacosmosItem, asset_key: str, assets_path: str, project_id: str
    ) -> str:
        """Upload a single asset file and update its href inside the item object.

        Returns:
            str: The asset_key upon successful upload.
        """
        asset = item.assets[asset_key]

        # Build storage key: project/<project_id>/<item_id>/<asset_name>
        upload_path = UploadPath.from_item_path(
            item,
            project_id,
            Path(asset.href).name,
        )

        local_src = Path(assets_path) / asset.href
        if local_src.exists():
            src = str(local_src)
            asset.href = f"file:///{upload_path}"
        else:
            # fallback: try matching just the filename inside assets_path
            src = str(Path(assets_path) / Path(asset.href).name)

        self._update_asset_href(asset)  # turn href into public URL
        self.upload_from_file(src, str(upload_path), mime_type=asset.type)

        return asset_key

    def _update_asset_href(self, asset: Asset) -> None:
        """Convert the storage key to a public HTTPS URL."""
        try:
            url = self.client.config.datacosmos_public_cloud_storage.as_domain_url()
            new_href = url.with_base(asset.href)  # type: ignore
            asset.href = str(new_href)
        except ValueError:
            pass

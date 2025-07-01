"""Module for uploading files to Datacosmos cloud storage and registering STAC items."""

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.uploader.dataclasses.upload_path import UploadPath


class DatacosmosUploader:
    """Handles uploading files to Datacosmos storage and registering STAC items."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the uploader with DatacosmosClient."""
        self.datacosmos_client = client
        self.item_client = ItemClient(client)
        self.base_url = client.config.datacosmos_cloud_storage.as_domain_url()

    def upload_item(
        self,
        item: Any,
        assets_path: str | None = None,
        included_assets: list[str] | bool = True,
        overwrite: bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
    ) -> Any:
        """Load the item to data cosmos.

        Assets can contain a remote path (href) or a local path.
        If the asset has a local path, it will be uploaded from that path.
        If the asset has a remote path, it will be uploaded from the assets_path.

        In both cases, the asset href will be updated to point to the current environment data cosmos storage.

        Args:
            item: The item to upload (if it is a string it will load from the file pointed by the string)
            assets_path: The path to the assets (if None, current working directory is used)
            included_assets: Either a list of asset keys to include or True to include all
            overwrite: Whether to overwrite existing files
            max_workers: Max workers to use in multithreading
            time_out: time out value to be used
        Returns:
            The uploaded item (might have changed due to links and asset hrefs)
        """
        if not assets_path and not isinstance(item, str):
            raise ValueError(
                "assets_path must be provided if item is not the path to an item file."
            )

        # loads the item from the path if it is a string
        if isinstance(item, str):
            item_filename = item
            item = self._load_item(item_filename)

            if not assets_path:
                assets_path = str(Path(item_filename).parent)

        assets_path = assets_path if assets_path else str(Path.cwd())

        upload_assets = (
            included_assets
            if isinstance(included_assets, list)
            else item.assets.keys()
            if included_assets is True
            else []
        )

        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for asset_key in upload_assets:
                futures.append(
                    executor.submit(
                        self._upload_asset,
                        item,
                        asset_key,
                        assets_path,
                        overwrite=overwrite,
                    )
                )

        done, not_done = wait(futures, timeout=time_out)

        self.item_client.add_item(item)

        # delay failure as much as possible
        self._handle_futures(done, not_done)

        return item

    def upload_file(self, src: str, dst: str) -> None:
        """Uploads a single file to the specified destination path."""
        url = self.base_url.with_suffix(dst)

        with open(src, "rb") as f:
            response = self.datacosmos_client.put(url, data=f)
        response.raise_for_status()

    @staticmethod
    def _load_item(item_json_file_path: str) -> DatacosmosItem:
        """Loads and validates the STAC item from a JSON file."""
        with open(item_json_file_path, "rb") as file:
            data = file.read().decode("utf-8")
        return TypeAdapter(DatacosmosItem).validate_json(data)

    @staticmethod
    def _handle_futures(
        done: set,
        not_done: set,
        results: list | None = None,
        errors: list | None = None,
    ) -> None:
        """Handle the futures that have completed and those that didn't complete in time."""
        # Handle completed futures
        errors = []
        for future in done:
            try:
                r = future.result()
                if results is not None:
                    results.append(r)
            except Exception as e:
                errors.append(e)

        # Handle futures that didn't complete in time
        for future in not_done:
            future.cancel()
        # Raise the first error if any
        if errors:
            if errors is None:
                raise errors[0]
            errors = errors

    def _upload_asset(
        self, item: DatacosmosItem, asset_key: str, assets_path: str
    ) -> None:
        """Upload an asset to data cosmos.

        Should an asset have a local path (href) it will be used directly,
        otherwise it will be uploaded from the assets_path.

        The local file is understood to be either relative to the CWD or to the assets_path.

        Args:
            item: The item the asset belongs to
            asset_key: The asset key to upload the artifact to
            assets_path: The base path to the asset file
        """
        asset = item.assets[asset_key]
        mission_name = ""
        upload_path = UploadPath.from_item_path(
            item, mission_name, Path(asset.href).name
        )
        if (Path(assets_path) / asset.href).exists():
            src = str(Path(assets_path) / asset.href)
            asset.href = "file:///" + str(upload_path)
        else:
            src = str(Path(assets_path) / Path(asset.href).name)
        self._update_asset_href(asset)
        self.upload_file(src, upload_path, mime_type=asset.type)

    def _update_asset_href(self, asset: Asset) -> None:
        try:
            url = (
                self.datacosmos_client.config.datacosmos_public_cloud_storage.as_domain_url()
            )
            new_href = url.with_base(asset.href)  # type: ignore
            asset.href = str(new_href)
        except ValueError:
            pass

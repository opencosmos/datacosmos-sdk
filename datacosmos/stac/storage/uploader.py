"""Handles uploading files to Datacosmos storage and registering STAC items."""

from pathlib import Path

from pydantic import TypeAdapter

from datacosmos.config.models.url import URL
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.upload_path import UploadPath
from datacosmos.stac.storage.storage_base import StorageBase


class Uploader(StorageBase):
    """Handles uploading files to Datacosmos storage and registering STAC items."""

    def __init__(self, client: DatacosmosClient):
        """Handles uploading files to Datacosmos storage and registering STAC items."""
        super().__init__(client)
        self.item_client = ItemClient(client)

    def upload_item(
        self,
        item: DatacosmosItem,
        assets_path: str | None = None,
        included_assets: list[str] | bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
    ) -> DatacosmosItem:
        """Upload a STAC item and its assets to Datacosmos."""
        if not assets_path and not isinstance(item, str):
            raise ValueError(
                "assets_path must be provided if item is not the path to an item file."
            )

        if isinstance(item, str):
            item_filename = item
            item = self._load_item(item_filename)
            if not assets_path:
                assets_path = str(Path(item_filename).parent)

        assets_path = assets_path or str(Path.cwd())

        upload_assets = (
            included_assets
            if isinstance(included_assets, list)
            else item.assets.keys()
            if included_assets is True
            else []
        )

        jobs = [(item, asset_key, assets_path) for asset_key in upload_assets]

        self._run_in_threads(self._upload_asset, jobs, max_workers, time_out)

        self.item_client.add_item(item)

        return item

    def upload_from_file(
        self, src: str, dst: str, mime_type: str | None = None
    ) -> None:
        """Uploads a single file to the specified destination path."""
        url = self.base_url.with_suffix(dst)
        mime = mime_type or self._guess_mime(src)
        headers = {"Content-Type": mime}
        with open(src, "rb") as f:
            response = self.client.put(url, data=f, headers=headers)
        response.raise_for_status()

    @staticmethod
    def _load_item(item_json_file_path: str) -> DatacosmosItem:
        with open(item_json_file_path, "rb") as file:
            data = file.read().decode("utf-8")
        return TypeAdapter(DatacosmosItem).validate_json(data)

    def _upload_asset(
        self, item: DatacosmosItem, asset_key: str, assets_path: str
    ) -> None:
        asset = item.assets[asset_key]
        upload_path = UploadPath.from_item_path(item, "", Path(asset.href).name)
        local_src = Path(assets_path) / asset.href
        if local_src.exists():
            src = str(local_src)
            asset.href = f"file:///{upload_path}"
        else:
            src = str(Path(assets_path) / Path(asset.href).name)
        self._update_asset_href(asset)
        self.upload_from_file(src, str(upload_path), mime_type=asset.type)

    def _update_asset_href(self, asset: Asset) -> None:
        try:
            url = (
                self.client.config.datacosmos_public_cloud_storage.as_domain_url()
                if isinstance(self.client.config.datacosmos_public_cloud_storage, URL)
                else self.client.config.datacosmos_public_cloud_storage
            )
            new_href = url.with_base(asset.href)  # type: ignore
            asset.href = str(new_href)
        except ValueError:
            pass

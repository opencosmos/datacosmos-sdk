"""Module for uploading files to Datacosmos cloud storage and registering STAC items."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import TypeAdapter

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.uploader.dataclasses.upload_path import UploadPath
from datacosmos.utils.missions import get_mission_name


class DatacosmosUploader:
    """Handles uploading files to Datacosmos storage and registering STAC items."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the uploader with DatacosmosClient."""
        mission_id = client.config.mission_id
        environment = client.config.environment

        self.datacosmos_client = client
        self.item_client = ItemClient(client)
        self.mission_name = (
            get_mission_name(mission_id, environment) if mission_id != 0 else ""
        )
        self.base_url = client.config.datacosmos_cloud_storage.as_domain_url()

    def upload_and_register_item(self, item_json_file_path: str) -> None:
        """Uploads files to Datacosmos storage and registers a STAC item.

        Args:
            item_json_file_path (str): Path to the STAC item JSON file.
        """
        item = self._load_item(item_json_file_path)
        collection_id, item_id = item.collection, item.id
        dirname = str(Path(item_json_file_path).parent / Path(item_json_file_path).stem)

        self._delete_existing_item(collection_id, item_id)
        upload_path = self._get_upload_path(item)
        self.upload_from_folder(dirname, upload_path)

        self._update_item_assets(item)

        self.item_client.create_item(collection_id, item)

    def upload_file(self, src: str, dst: str) -> None:
        """Uploads a single file to the specified destination path."""
        url = self.base_url.with_suffix(str(dst))

        with open(src, "rb") as f:
            response = self.datacosmos_client.put(url, data=f)
        response.raise_for_status()

    def upload_from_folder(self, src: str, dst: UploadPath, workers: int = 4) -> None:
        """Uploads all files from a folder to the destination path in parallel."""
        if Path(dst.path).is_file():
            raise ValueError(f"Destination path should not be a file path {dst}")

        if Path(src).is_file():
            raise ValueError(f"Source path should not be a file path {src}")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for file in Path(src).rglob("*"):
                if file.is_file():
                    dst = UploadPath(
                        mission=dst.mission,
                        level=dst.level,
                        day=dst.day,
                        month=dst.month,
                        year=dst.year,
                        id=dst.id,
                        path=str(file.relative_to(src)),
                    )
                    futures.append(executor.submit(self.upload_file, str(file), dst))
            for future in futures:
                future.result()

    @staticmethod
    def _load_item(item_json_file_path: str) -> DatacosmosItem:
        """Loads and validates the STAC item from a JSON file."""
        with open(item_json_file_path, "rb") as file:
            data = file.read().decode("utf-8")
        return TypeAdapter(DatacosmosItem).validate_json(data)

    def _delete_existing_item(self, collection_id: str, item_id: str) -> None:
        """Deletes an existing item if it already exists."""
        try:
            self.item_client.delete_item(item_id, collection_id)
        except Exception:  # nosec
            pass  # Ignore if item doesn't exist

    def _get_upload_path(self, item: DatacosmosItem) -> str:
        """Constructs the storage upload path based on the item and mission name."""
        return UploadPath.from_item_path(item, self.mission_name, "")

    def _update_item_assets(self, item: DatacosmosItem) -> None:
        """Updates the item's assets with uploaded file URLs."""
        for asset in item.assets.values():
            try:
                url = self.base_url
                asset.href = url.with_base(asset.href)  # type: ignore
            except ValueError:
                pass

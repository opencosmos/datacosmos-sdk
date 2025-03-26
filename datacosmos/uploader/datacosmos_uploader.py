from pydantic import TypeAdapter
from pathlib import Path
from datacosmos.stac.item.models.item import Item
from datacosmos.stac.item.models.asset import Asset
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.storage.storage_client import StorageClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.uploader.dataclasses.upload_path import UploadPath
from datacosmos.utils.missions import get_mission_name


class DatacosmosUploader:
    """Handles uploading files to Datacosmos storage and registering STAC items."""

    def __init__(self, client: DatacosmosClient, mission_id: int, environment: str):
        """Initialize the uploader with required clients and mission info."""
        self.storage_client = StorageClient(client)
        self.item_client = ItemClient(client)
        self.mission_name = get_mission_name(mission_id, environment) if mission_id != 0 else ""

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
        self.storage_client.upload_from_folder(dirname, upload_path)

        self._update_item_assets(item)
        self.item_client.create_item(collection_id, item)

    def _load_item(self, item_json_file_path: str) -> Item:
        """Loads and validates the STAC item from a JSON file."""
        with open(item_json_file_path, "rb") as file:
            data = file.read().decode("utf-8")
        return TypeAdapter(Item).validate_json(data)

    def _delete_existing_item(self, collection_id: str, item_id: str) -> None:
        """Deletes an existing item if it already exists."""
        try:
            self.item_client.delete_item(item_id, collection_id)
        except Exception:
            pass  # Ignore if item doesn't exist

    def _get_upload_path(self, item: Item) -> str:
        """Constructs the storage upload path based on the item and mission name."""
        return UploadPath.from_item_path(item, self.mission_name, "")

    def _update_item_assets(self, item: Item) -> None:
        """Updates the item's assets with uploaded file URLs."""
        for asset in item.assets.values():
            try:
                url = self.storage_client.base_url
                asset.href = url.with_base(asset.href)  # type: ignore
            except ValueError:
                pass

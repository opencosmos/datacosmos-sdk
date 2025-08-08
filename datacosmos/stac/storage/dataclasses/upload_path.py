"""Dataclass for generating the upload key of an asset."""

from dataclasses import dataclass
from pathlib import Path

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


@dataclass
class UploadPath:
    """Storage key in the form: project/<project-id>/<item-id>/<asset-name>."""

    project_id: str
    item_id: str
    asset_name: str

    def __str__(self) -> str:
        """Path in the form: project/<project-id>/<item-id>/<asset-name>."""
        return f"project/{self.project_id}/{self.item_id}/{self.asset_name}".rstrip("/")

    @classmethod
    def from_item_path(
        cls,
        item: DatacosmosItem,
        project_id: str,
        asset_name: str,
    ) -> "UploadPath":
        """Create an UploadPath for the given item/asset."""
        return cls(project_id=project_id, item_id=item.id, asset_name=asset_name)

    @classmethod
    def from_path(cls, path: str) -> "UploadPath":
        """Reverse-parse a storage key back into its components."""
        parts = Path(path).parts
        if len(parts) < 4 or parts[0] != "project":
            raise ValueError(f"Invalid path: {path}")

        project_id, item_id, *rest = parts[1:]
        asset_name = "/".join(rest)
        if not asset_name:
            raise ValueError(f"Asset name is missing in path: {path}")
        return cls(project_id=project_id, item_id=item_id, asset_name=asset_name)

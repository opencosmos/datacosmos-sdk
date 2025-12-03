"""Dataclass for generating the upload key of an asset."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


@dataclass
class UploadPath:
    """Storage key. Path structure varies based on project_id/collection_id presence."""

    project_id: str | None
    collection_id: str | None
    item_id: str
    asset_name: str
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None

    def __str__(self) -> str:
        """Path structure: project/... OR catalog/<collection-id>/<Y/M/D>/..."""
        if self.project_id:
            return f"project/{self.project_id}/{self.item_id}/{self.asset_name}".rstrip(
                "/"
            )
        elif self.collection_id and self.year and self.month and self.day:
            return f"catalog/{self.collection_id}/{self.year}/{self.month}/{self.day}/{self.item_id}/{self.asset_name}".rstrip(
                "/"
            )
        else:
            # Fallback path if insufficient data
            return f"{self.item_id}/{self.asset_name}".rstrip("/")

    @classmethod
    def from_item_path(
        cls,
        item: DatacosmosItem,
        project_id: str | None,
        collection_id: str | None,
        asset_name: str,
    ) -> "UploadPath":
        """Create an UploadPath for the given item/asset, extracting date components from the item's datetime property."""
        if project_id is None and collection_id is None:
            raise ValueError(
                "Either project_id or collection_id must be provided for asset upload path construction."
            )

        try:
            dt: datetime = item.properties["datetime"]
            year = dt.strftime("%Y")
            month = dt.strftime("%m")
            day = dt.strftime("%d")
        except Exception:
            year, month, day = None, None, None

        return cls(
            project_id=project_id,
            collection_id=collection_id,
            item_id=item.id,
            asset_name=asset_name,
            year=year,
            month=month,
            day=day,
        )

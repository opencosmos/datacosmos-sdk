"""Dataclass for generating the upload key of an asset."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem

_log = logging.getLogger(__name__)


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
            # Normalize collection_id by stripping --qa suffix for storage path
            # The catalog API expects assets to be stored under the base collection name
            normalized_collection = self.collection_id.removesuffix("--qa")
            return f"catalog/{normalized_collection}/{self.year}/{self.month}/{self.day}/{self.item_id}/{self.asset_name}".rstrip(
                "/"
            )
        else:
            _log.warning(
                f"Catalog path could not be constructed for item {self.item_id}. "
                f"Missing date components or collection_id. Using generic fallback path."
            )
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

        year, month, day = None, None, None
        try:
            dt: str = item.properties["datetime"]
            format_string = "%Y-%m-%dT%H:%M:%SZ"
            date_object = datetime.strptime(dt, format_string)
            year = date_object.strftime("%Y")
            month = date_object.strftime("%m")
            day = date_object.strftime("%d")
        except Exception as e:
            _log.warning(
                f"Failed to extract date components from item.datetime for upload path: {e}"
            )
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

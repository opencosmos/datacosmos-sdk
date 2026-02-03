"""Structured result containing the status of a delete operation."""

from dataclasses import dataclass
from typing import Any

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


@dataclass
class DeleteResult:
    """Structured result containing the status of an item and assets delete operation."""

    # The item that was deleted (fetched before deletion for reference)
    item: DatacosmosItem

    # Whether the item metadata was successfully deleted from the catalog
    item_deleted: bool

    # List of asset keys that were successfully deleted from storage
    successful_assets: list[str]

    # List of dictionaries with 'asset_key', 'error', and 'exception' for failed deletions
    failed_assets: list[dict[str, Any]]

    @property
    def all_assets_deleted(self) -> bool:
        """Check if all assets were successfully deleted."""
        return len(self.failed_assets) == 0

    @property
    def fully_deleted(self) -> bool:
        """Check if both item and all assets were successfully deleted."""
        return self.item_deleted and self.all_assets_deleted

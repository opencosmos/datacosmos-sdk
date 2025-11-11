"""Structured result containing the status of a batch asset upload operation."""

from dataclasses import dataclass
from typing import Any

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


@dataclass
class UploadResult:
    """Structured result containing the status of a batch asset upload operation."""

    # The final STAC item with updated asset hrefs
    item: DatacosmosItem

    # list of asset keys (str) that were successfully uploaded
    successful_assets: list[str]

    # list of dictionaries, each containing 'error', 'exception', and 'job_args'
    failed_assets: list[dict[str, Any]]

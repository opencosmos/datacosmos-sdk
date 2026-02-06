"""Model representing a STAC 1.1.0 item asset definition.

Used for collection-level asset definitions in the item_assets field.
Spec: https://github.com/stac-extensions/item-assets
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

from datacosmos.stac.item.models.statistics import Statistics


class ItemAssetDefinition(BaseModel):
    """Model representing a STAC 1.1.0 item asset definition.

    Describes collection-level asset definitions that appear in items.
    """

    model_config = ConfigDict(extra="allow")

    title: str | None = None
    description: str | None = None
    type: str | None = None
    roles: list[str] | None = None
    keywords: list[str] | None = None
    data_type: str | None = None
    nodata: Any | None = None
    unit: str | None = None
    statistics: Statistics | None = None

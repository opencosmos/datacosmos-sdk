"""Model representing a datacosmos item asset."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from datacosmos.stac.item.models.band import Band
from datacosmos.stac.item.models.statistics import Statistics


class Asset(BaseModel):
    """Model representing a datacosmos item asset.

    Includes STAC 1.1.0 common metadata fields.
    Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/assets.md
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    href: str
    title: str | None = None
    description: str | None = None
    type: str | None = None
    roles: list[str] | None = None

    # STAC 1.1.0 common metadata fields
    keywords: list[str] | None = None
    data_type: str | None = None
    nodata: Any | None = None
    unit: str | None = None
    statistics: Statistics | None = None
    bands: list[Band] | None = None

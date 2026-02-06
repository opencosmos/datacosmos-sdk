"""Model representing a STAC 1.1.0 band object."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from datacosmos.stac.item.models.statistics import Statistics


class Band(BaseModel):
    """Model representing a STAC 1.1.0 band object.

    This is the unified band metadata structure introduced in STAC 1.1.0.
    Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#band-object
    """

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    roles: list[str] | None = None
    data_type: str | None = None
    nodata: Any | None = None
    unit: str | None = None
    statistics: Statistics | None = None

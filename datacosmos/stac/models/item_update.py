from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator
from pystac import Asset, Link
from shapely.geometry import mapping


class ItemUpdate(BaseModel):
    """Model representing a partial update for a STAC item."""

    model_config = {"arbitrary_types_allowed": True}

    stac_extensions: Optional[list[str]] = None
    geometry: Optional[dict[str, Any]] = None
    bbox: Optional[list[float]] = Field(
        None, min_items=4, max_items=4
    )  # Must be [minX, minY, maxX, maxY]
    properties: Optional[dict[str, Any]] = None
    assets: Optional[dict[str, Asset]] = None
    links: Optional[list[Link]] = None

    def set_geometry(self, geom) -> None:
        """Convert a shapely geometry to GeoJSON format."""
        self.geometry = mapping(geom)

    @model_validator(mode="before")
    def validate_datetime_fields(cls, values):
        """Ensure at least one of 'datetime' or 'start_datetime'/'end_datetime' exists."""
        properties = values.get("properties", {})
        has_datetime = "datetime" in properties and properties["datetime"] is not None
        has_start_end = (
            "start_datetime" in properties and properties["start_datetime"] is not None
        ) and ("end_datetime" in properties and properties["end_datetime"] is not None)

        if not has_datetime and not has_start_end:
            raise ValueError(
                "Either 'datetime' or both 'start_datetime' and 'end_datetime' must be provided."
            )

        return values

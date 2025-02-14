"""Model representing a partial update for a STAC item."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator
from pystac import Asset, Link


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

    def set_geometry(self, geom_type: str, coordinates: list[Any]) -> None:
        """Set the geometry manually without using shapely.

        Args:
            geom_type (str): The type of geometry (e.g., 'Point', 'Polygon').
            coordinates (list[Any]): The coordinates defining the geometry.
        """
        self.geometry = {"type": geom_type, "coordinates": coordinates}

    @staticmethod
    def has_valid_datetime(properties: dict[str, Any]) -> bool:
        """Check if 'datetime' is present and not None."""
        return properties.get("datetime") is not None

    @staticmethod
    def has_valid_datetime_range(properties: dict[str, Any]) -> bool:
        """Check if both 'start_datetime' and 'end_datetime' are present and not None."""
        return all(
            properties.get(key) is not None
            for key in ["start_datetime", "end_datetime"]
        )

    @model_validator(mode="before")
    def validate_datetime_fields(cls, values):
        """Ensure at least one of 'datetime' or 'start_datetime'/'end_datetime' exists."""
        properties = values.get("properties", {})

        if not cls.has_valid_datetime(properties) and not cls.has_valid_datetime_range(
            properties
        ):
            raise ValueError(
                "Either 'datetime' or both 'start_datetime' and 'end_datetime' must be provided."
            )

        return values

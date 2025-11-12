"""Model representing a datacosmos item."""

import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from shapely.errors import ShapelyError
from shapely.geometry import Polygon, shape

from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.asset import Asset

_REQUIRED_DATACOSMOS_PROPERTIES = [
    "datetime",
    "processing:level",
    "sat:platform_international_designator",
]


class DatacosmosItem(BaseModel):
    """Model representing a flexible Datacosmos STAC item with mandatory business fields."""

    model_config = ConfigDict(extra="allow")

    is_strict: bool = Field(default=True, exclude=True)

    id: str
    type: str
    geometry: dict[str, Any]
    bbox: list[float]
    properties: dict[str, Any]

    links: list[dict[str, Any]]
    assets: dict[str, Asset]

    stac_version: str | None = None
    stac_extensions: list[str] | None = None
    collection: str | None = None

    @field_validator("properties", mode="before")
    @classmethod
    def validate_datacosmos_properties(
        cls, properties_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validates that Datacosmos-specific properties exist."""
        missing_keys = [
            key for key in _REQUIRED_DATACOSMOS_PROPERTIES if key not in properties_data
        ]

        if missing_keys:
            raise StacValidationError(
                f"Datacosmos-specific properties are missing: {', '.join(missing_keys)}."
            )
        return properties_data

    @field_validator("geometry", mode="before")
    @classmethod
    def validate_geometry_is_polygon(
        cls, geometry_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validates that the geometry is a Polygon or MultiPolygon with coordinates."""
        geom_type = geometry_data.get("type")

        valid_types = {"Polygon", "MultiPolygon"}

        if geom_type not in valid_types or not geometry_data.get("coordinates"):
            raise StacValidationError(
                "Geometry must be a Polygon or MultiPolygon with coordinates."
            )

        if getattr(cls, "is_strict", True) and geom_type == "Polygon":
            try:
                polygon = shape(geometry_data)

                if not polygon.is_valid:
                    raise ValueError(
                        f"Polygon geometry is invalid: {polygon.geom_type}"
                    )

                if not polygon.exterior.is_ccw:
                    raise ValueError(
                        "Polygon winding order violates GeoJSON Right-Hand Rule (Exterior ring is clockwise)."
                    )

            except (KeyError, ShapelyError, ValueError) as e:
                raise StacValidationError(f"Invalid geometry data: {e}") from e

        return geometry_data

    @model_validator(mode="after")
    def validate_bbox_vs_geometry(self) -> "DatacosmosItem":
        """Validates that the bbox tightly encloses the geometry and performs strict geometric checks."""
        if not getattr(self, "is_strict", True):
            return self

        geom_shape = None

        if self.geometry.get("type") == "Polygon":
            try:
                geom_shape = shape(self.geometry)

                if not geom_shape.is_valid:
                    raise StacValidationError(
                        f"Polygon geometry is invalid: {geom_shape.geom_type}"
                    )

                if not geom_shape.exterior.is_ccw:
                    raise StacValidationError(
                        "Polygon winding order violates GeoJSON Right-Hand Rule."
                    )
            except Exception as e:
                raise StacValidationError(f"Invalid geometry data: {e}") from e

        if self.geometry and self.bbox:
            try:
                # If geom_shape was not created in the check above, create it now for the bbox check.
                if geom_shape is None:
                    geom_shape = shape(self.geometry)

                true_bbox = list(geom_shape.bounds)

                if not all(
                    math.isclose(a, b, rel_tol=1e-9)
                    for a, b in zip(self.bbox, true_bbox)
                ):
                    raise StacValidationError(
                        "Provided bbox does not match geometry bounds."
                    )
            except Exception as e:
                raise StacValidationError(f"Invalid bbox or geometry: {e}") from e

        return self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatacosmosItem":
        """Creates a DatacosmosItem instance from a dictionary using Pydantic's model_validate."""
        return cls.model_validate(data)

    @classmethod
    def from_dict_permissive(cls, data: dict[str, Any]) -> "DatacosmosItem":
        """Creates a DatacosmosItem instance from a dictionary in permissive mode, skipping strict geometric and bbox consistency checks."""

        class PermissiveDatacosmosItem(cls):
            is_strict: bool = False

        return PermissiveDatacosmosItem.model_validate(data)

    def get_property(self, key: str) -> Any | None:
        """Get a property value from the Datacosmos item."""
        return self.properties.get(key)

    def get_asset(self, key: str) -> Asset | None:
        """Get an asset from the Datacosmos item."""
        return self.assets.get(key)

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the Datacosmos item."""
        return datetime.strptime(self.properties["datetime"], "%Y-%m-%dT%H:%M:%SZ")

    @property
    def level(self) -> ProcessingLevel:
        """Get the processing level of the Datacosmos item."""
        return ProcessingLevel(self.properties["processing:level"].lower())

    @property
    def sat_int_designator(self) -> str:
        """Get the satellite international designator of the Datacosmos item."""
        return self.properties["sat:platform_international_designator"]

    @property
    def polygon(self) -> Polygon:
        """Returns the polygon of the item."""
        coordinates = self.geometry["coordinates"][0]
        return Polygon(coordinates)

    def to_dict(self) -> dict:
        """Converts the DatacosmosItem instance to a dictionary."""
        return self.model_dump()

    def has_self_link(self) -> bool:
        """Checks if the item has a 'self' link."""
        return any(link.get("rel") == "self" for link in self.links)

    def has_parent_link(self) -> bool:
        """Checks if the item has a 'parent' link."""
        return any(link.get("rel") == "parent" for link in self.links)

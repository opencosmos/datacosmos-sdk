"""Model representing a datacosmos item."""

import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
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
        """Validates that the geometry is a Polygon with coordinates and correct winding order."""
        if geometry_data.get("type") != "Polygon" or not geometry_data.get(
            "coordinates"
        ):
            raise StacValidationError("Geometry must be a Polygon with coordinates.")

        try:
            # Use shape() for robust GeoJSON parsing and validation
            polygon = shape(geometry_data)

            if not polygon.is_valid:
                raise ValueError(f"Polygon geometry is invalid: {polygon.geom_type}")

            # right-hand rule validation:
            # The right-hand rule means exterior ring must be counter-clockwise (CCW).
            # Shapely's Polygon stores the exterior as CCW if the input is valid.
            if not polygon.exterior.is_ccw:
                raise ValueError(
                    "Polygon winding order violates GeoJSON Right-Hand Rule (Exterior ring is clockwise)."
                )

        except (KeyError, ShapelyError, ValueError) as e:
            raise StacValidationError(f"Invalid geometry data: {e}") from e

        return geometry_data

    @model_validator(mode="after")
    def validate_bbox_vs_geometry(self) -> "DatacosmosItem":
        """Validates that the bbox tightly encloses the geometry."""
        if self.geometry and self.bbox:
            try:
                geom_shape = shape(self.geometry)
                true_bbox = list(geom_shape.bounds)

                # Check for floating point equality within a tolerance
                if not all(
                    math.isclose(a, b, rel_tol=1e-9)
                    for a, b in zip(self.bbox, true_bbox)
                ):
                    raise StacValidationError(
                        "Provided bbox does not match geometry bounds."
                    )
            except Exception as e:
                # Catch any errors from Shapely or the comparison
                raise StacValidationError(f"Invalid bbox or geometry: {e}") from e
        return self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatacosmosItem":
        """Creates a DatacosmosItem instance from a dictionary using Pydantic's model_validate.

        Args:
            data (dict): The dictionary (JSON response) to validate and load.

        Returns:
            DatacosmosItem: A validated instance of the model.
        """
        return cls.model_validate(data)

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

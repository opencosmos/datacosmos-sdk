"""Model representing a datacosmos item."""

import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
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

    def validate(self) -> None:
        """Runs all mandatory Datacosmos and STAC structural checks on the current item instance.

        Raises:
            StacValidationError: If the item violates any structural or business rules.
        """
        self._validate_datacosmos_properties()

        self._validate_geometry_is_polygon()

        self._validate_bbox_vs_geometry()

        self._validate_collection_id()

    def _validate_datacosmos_properties(self) -> None:
        """Validates that Datacosmos-specific properties exist."""
        missing_keys = [
            key for key in _REQUIRED_DATACOSMOS_PROPERTIES if key not in self.properties
        ]

        if missing_keys:
            raise StacValidationError(
                f"Datacosmos-specific properties are missing: {', '.join(missing_keys)}."
            )

    def _validate_geometry_is_polygon(self) -> None:
        """Validates that the geometry is a Polygon (or MultiPolygon) with coordinates and correct winding order."""
        geometry_data = self.geometry
        geom_type = geometry_data.get("type")

        valid_types = {"Polygon", "MultiPolygon"}
        if geom_type not in valid_types or not geometry_data.get("coordinates"):
            raise StacValidationError(
                "Geometry must be a Polygon or MultiPolygon with coordinates."
            )

        try:
            geom = shape(geometry_data)
            if geom_type == "Polygon":
                # Single polygon validation
                if not geom.is_valid:
                    raise StacValidationError(
                        f"Polygon geometry is invalid: {geom.geom_type}"
                    )
                if not geom.exterior.is_ccw:
                    raise StacValidationError(
                        "Polygon winding order violates GeoJSON Right-Hand Rule (Exterior ring is clockwise)."
                    )
            elif geom_type == "MultiPolygon":
                # Validate each polygon in the MultiPolygon
                for idx, polygon in enumerate(geom.geoms):
                    if not polygon.is_valid:
                        raise StacValidationError(
                            f"MultiPolygon geometry is invalid at index {idx}: {polygon.geom_type}"
                        )
                    if not polygon.exterior.is_ccw:
                        raise StacValidationError(
                            f"MultiPolygon winding order violates GeoJSON Right-Hand Rule at index {idx} (Exterior ring is clockwise)."
                        )
        except (KeyError, ShapelyError, ValueError) as e:
            raise StacValidationError(f"Invalid geometry data: {e}") from e

    def _validate_bbox_vs_geometry(self) -> None:
        """Validates that the bbox tightly encloses the geometry."""
        if self.geometry and self.bbox:
            try:
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

    def _validate_collection_id(self) -> None:
        if not self.collection:
            raise StacValidationError("Item does not have a collection.")

        if not self.__is_collection_link_consistent():
            raise StacValidationError(
                "Parent link in DatacosmosItem does not match its collection."
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatacosmosItem":
        """Creates a DatacosmosItem instance from a dictionary using Pydantic's model_validate."""
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

    def __is_collection_link_consistent(self) -> bool:
        """Helper to check if the parent link matches the datacosmos item's collection field."""
        for link in self.links:
            if link.get("rel") == "parent":
                link_collection_id = link.get("href", "").rstrip("/").split("/")[-1]
                if not link_collection_id:
                    continue
                if link_collection_id == self.collection:
                    return True

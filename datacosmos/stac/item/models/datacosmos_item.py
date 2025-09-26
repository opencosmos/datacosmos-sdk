"""Model representing a datacosmos item."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from shapely.geometry import Polygon

from datacosmos.exceptions.datacosmos_exception import DatacosmosException
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.asset import Asset


class DatacosmosItem(BaseModel):
    """Model representing a flexible Datacosmos STAC item with mandatory business fields."""

    model_config = ConfigDict(extra="allow")

    id: str
    type: str
    geometry: Dict[str, Any]
    bbox: List[float]
    properties: Dict[str, Any]

    links: List[Dict[str, Any]]
    assets: Dict[str, Asset]

    stac_version: Optional[str] = None
    stac_extensions: Optional[List[str]] = None
    collection: Optional[str] = None

    @field_validator("properties", mode="before")
    @classmethod
    def validate_datacosmos_properties(
        cls, properties_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validates that Datacosmos-specific properties exist."""
        required_keys = [
            "datetime",
            "processing:level",
            "sat:platform_international_designator",
        ]

        missing_keys = [key for key in required_keys if key not in properties_data]

        if missing_keys:
            raise DatacosmosException(
                f"Datacosmos-specific properties are missing: {', '.join(missing_keys)}."
            )
        return properties_data

    @field_validator("geometry", mode="before")
    @classmethod
    def validate_geometry_is_polygon(
        cls, geometry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validates that the geometry is a Polygon with coordinates."""
        if geometry_data.get("type") != "Polygon" or not geometry_data.get(
            "coordinates"
        ):
            raise DatacosmosException("Geometry must be a Polygon with coordinates.")
        return geometry_data

    def get_property(self, key: str) -> Optional[Any]:
        """Get a property value from the Datacosmos item."""
        return self.properties.get(key)

    def get_asset(self, key: str) -> Optional[Asset]:
        """Get an asset from the Datacosmos item."""
        return self.assets.get(key)

    @property
    def datacosmos_datetime(self) -> datetime:
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
    def polygon(
        self,
    ) -> Polygon:
        """Returns the polygon of the item."""
        coordinates = self.geometry["coordinates"][0]
        return Polygon(coordinates)

    def to_dict(self) -> dict:
        """Converts the DatacosmosItem instance to a dictionary."""
        return self.model_dump()

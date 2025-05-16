"""Model representing a datacosmos item."""

from datetime import datetime

from pydantic import BaseModel

from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.asset import Asset


class DatacosmosItem(BaseModel):
    """Model representing a datacosmos item."""

    id: str
    type: str
    stac_version: str
    stac_extensions: list | None
    geometry: dict
    properties: dict
    links: list
    assets: dict[str, Asset]
    collection: str
    bbox: tuple[float, float, float, float]

    def get_property(self, key: str) -> str | None:
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
        property = self.get_property("sat:platform_international_designator")
        if property is None:
            raise ValueError(
                "sat:platform_international_designator is missing in STAC item"
            )
        return property

    def to_dict(self) -> dict:
        """Converts the DatacosmosItem instance to a dictionary."""
        return self.model_dump()

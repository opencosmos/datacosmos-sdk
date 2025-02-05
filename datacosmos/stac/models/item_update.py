from typing import Optional, Any
from pydantic import BaseModel, Field
from pystac import Asset, Link
from shapely.geometry import mapping


class ItemUpdate(BaseModel):
    """Model representing a partial update for a STAC item."""
    model_config = {
        "arbitrary_types_allowed": True
    }

    stac_extensions: Optional[list[str]] = None
    geometry: Optional[dict[str, Any]] = None
    bbox: Optional[list[float]] = Field(None, min_items=4, max_items=4)  # Must be [minX, minY, maxX, maxY]
    properties: Optional[dict[str, Any]] = None
    assets: Optional[dict[str, Asset]] = None
    links: Optional[list[Link]] = None

    def set_geometry(self, geom) -> None:
        """Convert a shapely geometry to GeoJSON format."""
        self.geometry = mapping(geom)
"""Contains classes for holding and working with STAC data."""
from dataclasses import dataclass
from typing import Dict, List

import geojson


@dataclass
class STACAsset:
    """Structure for storing STAC asset data.

    See the following link for more details about the STAC asset structure:
    https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#asset-object
    """

    href: str
    title: str | None
    description: str | None
    type: str | None
    roles: List[str] | None

    @classmethod
    def from_dict(cls, d: Dict) -> "STACAsset":
        """Create a STACAsset from a dictionary matching the STAC asset format."""
        return cls(
            href=d["href"],
            title=d.get("title"),
            description=d.get("description"),
            type=d.get("type"),
            roles=d.get("roles"),
        )


@dataclass
class STACItem:
    """Structure for storing STAC item data.

    See the following link for more details about the STAC item structure:
    https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md
    """

    id: str
    collection: str
    properties: Dict
    geometry: geojson.GeoJSON
    bbox: List[float]
    assets: Dict[str, STACAsset]

    @classmethod
    def from_dict(cls, d: Dict) -> "STACItem":
        """Create a STACItem from a dictionary matching the STAC item format."""
        return cls(
            id=d["id"],
            collection=d["collection"],
            properties=d["properties"],
            geometry=geojson.GeoJSON.to_instance(d["geometry"]),
            bbox=d["bbox"],
            assets={k: STACAsset.from_dict(v) for k, v in d["assets"].items()},
        )

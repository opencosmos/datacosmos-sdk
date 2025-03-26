from datetime import datetime
from pydantic import BaseModel
from datacosmos.stac.enums.level import Level
from datacosmos.stac.item.models.asset import Asset

class Item(BaseModel):
    id: str
    type: str
    stac_version: str
    # Required as some bad data is present in the STAC catalogue currently
    stac_extensions: list | None
    geometry: dict
    properties: dict
    links: list
    assets: dict[str, Asset]
    collection: str
    bbox: tuple[float, float, float, float]

    def get_property(self, key: str) -> str | None:
        return self.properties.get(key)

    def get_asset(self, key: str) -> Asset | None:
        return self.assets.get(key)

    @property
    def datetime(self) -> datetime:
        return datetime.strptime(self.properties["datetime"], "%Y-%m-%dT%H:%M:%SZ")

    @property
    def level(self) -> Level:
        return Level(self.properties["processing:level"].lower())

    @property
    def sat_int_designator(self) -> str:
        property = self.get_property("sat:platform_international_designator")
        if property is None:
            raise ValueError("sat:platform_international_designator is missing in STAC item")
        return property
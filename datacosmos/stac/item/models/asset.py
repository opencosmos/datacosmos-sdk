from pydantic import BaseModel, Field

from datacosmos.stac.item.models.eo_band import EoBand
from datacosmos.stac.item.models.raster_band import RasterBand

class Asset(BaseModel):
    href: str
    title: str
    description: str
    type: str
    roles: list[str] | None
    eo_bands: list[EoBand] | None = Field(default=None, alias="eo:bands")
    raster_bands: list[RasterBand] | None = Field(default=None, alias="raster:bands")

    class Config:
        populate_by_name = True
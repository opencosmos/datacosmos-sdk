"""Model representing a raster band."""

from pydantic import BaseModel, Field


class RasterBand(BaseModel):
    """Model representing a raster band."""

    gain: float = Field(alias="scale")
    bias: float = Field(alias="offset")
    nodata: int
    unit: str

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

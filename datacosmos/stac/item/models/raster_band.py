from pydantic import BaseModel, Field

class RasterBand(BaseModel):
    gain: float = Field(alias="scale")
    bias: float = Field(alias="offset")
    nodata: int
    unit: str

    class Config:
        populate_by_name = True
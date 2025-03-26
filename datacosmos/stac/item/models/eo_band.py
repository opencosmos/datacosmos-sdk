
from pydantic import BaseModel
from typing import Optional

class EoBand(BaseModel):
    name: str
    common_name: str
    center_wavelength: float
    full_width_half_max: float
    solar_illumination: Optional[float] = None
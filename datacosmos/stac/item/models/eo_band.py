"""Model representing an EO band."""

from typing import Optional

from pydantic import BaseModel


class EoBand(BaseModel):
    """Model representing an EO band."""

    name: str
    common_name: str
    center_wavelength: float
    full_width_half_max: float
    solar_illumination: Optional[float] = None

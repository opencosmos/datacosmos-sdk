"""Product type enum class."""

from enum import Enum


class ProductType(str, Enum):
    """Different product types."""

    SATELLITE = "Satellite"
    VECTOR = "Vector"
    INSIGHT = "Insight"

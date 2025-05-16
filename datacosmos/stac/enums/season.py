"""Season enum class."""

from enum import Enum


class Season(str, Enum):
    """Different Open Cosmos seasons."""

    SUMMER = "Summer"
    WINTER = "Winter"
    AUTUMN = "Autumn"
    SPRING = "Spring"
    RAINY = "Rainy"
    DRY = "Dry"

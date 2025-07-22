"""Level enum class."""

from enum import Enum


class ProcessingLevel(Enum):
    """Enum class for the processing levels of the data."""

    RAW = "RAW"
    L0 = "l0"
    L1A = "l1A"
    L2A = "l2A"
    L1B = "l1B"
    L1C = "l1C"
    L1D = "l1D"
    L3 = "l3"

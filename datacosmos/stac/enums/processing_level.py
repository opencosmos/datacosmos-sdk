"""Level enum class."""

from enum import Enum


class CaseInsensitiveEnum(Enum):
    """An enum that can be initialized with case-insensitive strings."""

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return super()._missing_(value)


class ProcessingLevel(CaseInsensitiveEnum):
    """Enum class for the processing levels of the data."""

    RAW = "RAW"
    L0 = "l0"
    L1A = "l1A"
    L2A = "l2A"
    L1B = "l1B"
    L1C = "l1C"
    L1D = "l1D"
    L3 = "l3"

"""Custom exception for STAC validation errors."""
from datacosmos.exceptions.datacosmos_error import DatacosmosError


class StacValidationError(DatacosmosError):
    """Exception raised for errors in STAC item validation."""

    pass

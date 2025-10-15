"""Custom exception for STAC validation errors."""
from datacosmos.exceptions.datacosmos_exception import DatacosmosException


class StacValidationException(DatacosmosException):
    """Exception raised for errors in STAC item validation."""

    pass

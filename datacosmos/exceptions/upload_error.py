"""Exception raised during asset upload operations."""
from typing import Any, Optional

from datacosmos.exceptions.datacosmos_error import DatacosmosError


class UploadError(DatacosmosError):
    """Exception raised during asset upload operations, including asset context."""

    def __init__(self, message: str, asset_key: Optional[str] = None, **kwargs: Any):
        """Initialize UploadError.

        Args:
            message (str): The error message.
            asset_key (Optional[str]): The key of the asset that caused the failure.
        """
        self.asset_key = asset_key

        # Modify message to include context if available
        if asset_key:
            message = f"[{asset_key}] {message}"

        super().__init__(message, **kwargs)

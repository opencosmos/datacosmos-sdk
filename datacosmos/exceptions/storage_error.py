"""Exception raised during storage operations."""

from typing import Any, Literal, Optional

from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError

OperationType = Literal["upload", "download", "delete"]


class StorageError(DatacosmosError):
    """Exception raised during storage operations (upload, download, delete)."""

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        operation: Optional[OperationType] = None,
        response: Optional[Response] = None,
        **kwargs: Any,
    ):
        """Initialize StorageError.

        Args:
            message: The error message.
            path: The storage path involved in the operation.
            operation: The type of operation that failed ('upload', 'download', 'delete').
            response: The HTTP response object, if available.
        """
        self.path = path
        self.operation = operation

        prefix_parts = []
        if operation:
            prefix_parts.append(operation)
        if path:
            prefix_parts.append(path)

        if prefix_parts:
            message = f"[{' '.join(prefix_parts)}] {message}"

        super().__init__(message, response=response, **kwargs)

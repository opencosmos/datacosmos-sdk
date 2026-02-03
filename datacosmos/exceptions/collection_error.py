"""Exception raised when a STAC collection operation fails."""

from typing import Any, Optional

from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError


class CollectionNotFoundError(DatacosmosError):
    """Exception raised when a STAC collection is not found."""

    def __init__(
        self,
        message: str,
        collection_id: Optional[str] = None,
        response: Optional[Response] = None,
        **kwargs: Any,
    ):
        """Initialize CollectionNotFoundError.

        Args:
            message: The error message.
            collection_id: The ID of the collection that was not found.
            response: The HTTP response object, if available.
        """
        self.collection_id = collection_id

        if collection_id:
            message = f"{message} (collection_id={collection_id})"

        super().__init__(message, response=response, **kwargs)

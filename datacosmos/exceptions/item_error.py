"""Exception raised when a STAC item operation fails."""

from typing import Any, Optional

from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError


class ItemNotFoundError(DatacosmosError):
    """Exception raised when a STAC item is not found."""

    def __init__(
        self,
        message: str,
        item_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        response: Optional[Response] = None,
        **kwargs: Any,
    ):
        """Initialize ItemNotFoundError.

        Args:
            message: The error message.
            item_id: The ID of the item that was not found.
            collection_id: The ID of the collection where the item was expected.
            response: The HTTP response object, if available.
        """
        self.item_id = item_id
        self.collection_id = collection_id

        context_parts = []
        if item_id:
            context_parts.append(f"item_id={item_id}")
        if collection_id:
            context_parts.append(f"collection_id={collection_id}")

        if context_parts:
            message = f"{message} ({', '.join(context_parts)})"

        super().__init__(message, response=response, **kwargs)

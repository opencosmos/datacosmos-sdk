"""Exception raised during delete operations."""

from typing import Any, Optional

from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError


class DeleteError(DatacosmosError):
    """Exception raised when deleting an item and/or its assets fails."""

    def __init__(
        self,
        message: str,
        item_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        failed_assets: Optional[list[dict[str, Any]]] = None,
        response: Optional[Response] = None,
        **kwargs: Any,
    ):
        """Initialize DeleteError.

        Args:
            message: The error message.
            item_id: The ID of the item being deleted.
            collection_id: The ID of the collection containing the item.
            failed_assets: List of dicts with 'asset_key' and 'error' for each failed asset.
            response: The HTTP response object, if available.
        """
        self.item_id = item_id
        self.collection_id = collection_id
        self.failed_assets = failed_assets or []

        context_parts = []
        if item_id:
            context_parts.append(f"item_id={item_id}")
        if collection_id:
            context_parts.append(f"collection_id={collection_id}")
        if self.failed_assets:
            failed_keys = [f.get("asset_key", "unknown") for f in self.failed_assets]
            context_parts.append(f"failed_assets={failed_keys}")

        if context_parts:
            message = f"{message} ({', '.join(context_parts)})"

        super().__init__(message, response=response, **kwargs)

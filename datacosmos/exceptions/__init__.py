"""Exceptions for the datacosmos package."""

from .authentication_error import AuthenticationError
from .collection_error import CollectionNotFoundError
from .datacosmos_error import DatacosmosError
from .delete_error import DeleteError
from .http_error import HTTPError
from .item_error import ItemNotFoundError
from .stac_validation_error import StacValidationError
from .storage_error import StorageError
from .upload_error import UploadError

__all__ = [
    "AuthenticationError",
    "CollectionNotFoundError",
    "DatacosmosError",
    "DeleteError",
    "HTTPError",
    "ItemNotFoundError",
    "StacValidationError",
    "StorageError",
    "UploadError",
]

"""Handles file uploads to DataCosmos storage."""

import mimetypes
import os

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.storage.models.storage_path import StoragePath
from datacosmos.utils.http_response import check_api_response


class StorageClient:
    """Handles file uploads to DataCosmos storage."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the StorageClient with Datacosmos authentication.

        Args:
            client (DatacosmosClient): Authenticated client for API calls.
        """
        self.client = client
        self.storage_base_url = self.client.config.stac.as_domain_url()

    def upload_file(self, file_path: str, storage_path: StoragePath) -> str:
        """Uploads a file to storage and returns the file URL.

        Args:
            file_path (str): Path to the local file.
            storage_path (StoragePath): Structured storage path.

        Returns:
            str: URL of the uploaded file.
        """
        url = self.storage_base_url.with_suffix(f"/upload/{storage_path.as_url_path()}")

        with open(file_path, "rb") as file:
            response = self.client.put(url, data=file)

        check_api_response(response)
        return f"{self.storage_base_url}/{storage_path.as_url_path()}"

    def upload_files(
        self, file_paths: list[str], collection_id: str, item_id: str
    ) -> dict[str, str]:
        """Uploads multiple files and returns a mapping of filenames to storage URLs.

        Args:
            file_paths (list[str]): list of local file paths to upload.
            collection_id (str): The target collection ID.
            item_id (str): The target item ID.

        Returns:
            dict[str, str]: Mapping of filenames to their storage URLs.
        """
        uploaded_files = {}
        for file_path in file_paths:
            storage_path = StoragePath(
                collection_id=collection_id,
                item_id=item_id,
                filename=os.path.basename(file_path),
            )
            uploaded_files[storage_path.filename] = self.upload_file(
                file_path, storage_path
            )

        return uploaded_files

    def get_mime_type(self, file_path: str) -> str:
        """Determine the MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

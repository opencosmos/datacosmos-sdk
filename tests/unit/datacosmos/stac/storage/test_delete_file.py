"""Unit tests for StorageBase.delete_file method."""

from unittest.mock import MagicMock

import pytest

from datacosmos.exceptions.storage_error import StorageError
from datacosmos.stac.storage.storage_base import StorageBase


@pytest.fixture
def mock_client():
    """Provides a mock DatacosmosClient with the required config structure."""
    client = MagicMock()
    client.config = MagicMock()
    client.config.datacosmos_cloud_storage.as_domain_url.return_value = MagicMock(
        with_suffix=lambda path: f"https://mock.storage.com{path}"
    )
    return client


@pytest.fixture
def storage_base(mock_client):
    """Instantiates the StorageBase class."""
    return StorageBase(mock_client)


class TestStorageBaseDeleteFile:
    """Tests for StorageBase.delete_file method."""

    def test_delete_file_with_full_url(self, storage_base, mock_client):
        """Test delete_file with a full HTTP URL."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete.return_value = mock_response

        storage_base.delete_file("https://storage.example.com/bucket/file.tif")

        mock_client.delete.assert_called_once_with(
            "https://storage.example.com/bucket/file.tif"
        )
        mock_response.raise_for_status.assert_called_once()

    def test_delete_file_with_relative_path(self, storage_base, mock_client):
        """Test delete_file with a relative storage path."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete.return_value = mock_response

        storage_base.delete_file("/bucket/my-file.tif")

        # Should construct URL from base_url
        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args[0][0]
        assert "mock.storage.com" in str(call_args)

    def test_delete_file_raises_storage_error_on_failure(
        self, storage_base, mock_client
    ):
        """Test that delete_file raises StorageError on HTTP failure."""
        mock_client.delete.side_effect = Exception("Connection refused")

        with pytest.raises(StorageError) as exc_info:
            storage_base.delete_file("/bucket/file.tif")

        assert exc_info.value.operation == "delete"
        assert exc_info.value.path == "/bucket/file.tif"
        assert "Failed to delete file" in str(exc_info.value)

    def test_delete_file_with_https_url(self, storage_base, mock_client):
        """Test delete_file correctly identifies HTTPS URLs."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete.return_value = mock_response

        storage_base.delete_file("https://secure.storage.com/file.tif")

        mock_client.delete.assert_called_once_with(
            "https://secure.storage.com/file.tif"
        )

    def test_delete_file_with_http_url(self, storage_base, mock_client):
        """Test delete_file correctly identifies HTTP URLs."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete.return_value = mock_response

        storage_base.delete_file("http://insecure.storage.com/file.tif")

        mock_client.delete.assert_called_once_with(
            "http://insecure.storage.com/file.tif"
        )

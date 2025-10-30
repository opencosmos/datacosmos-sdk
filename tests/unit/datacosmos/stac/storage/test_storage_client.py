from unittest.mock import MagicMock, Mock

import pytest

import datacosmos.stac.storage.storage_client as storage_client_module
from datacosmos.stac.storage.storage_client import StorageClient

PROJECT_ID = "proj123"


class DummyUploader:
    """Mock class to simulate Uploader and track arguments passed to upload_item."""

    def __init__(self, client):
        self.client = client
        self.upload_called_with = None

    def upload_item(self, *args, **kwargs):
        self.upload_called_with = (args, kwargs)
        return "uploaded_item", ["key1"], []


class DummyDownloader:
    """Mock class to simulate Downloader and track arguments passed to download_assets."""

    def __init__(self, client):
        self.client = client
        self.download_called_with = None

    def download_assets(self, *args, **kwargs):
        self.download_called_with = (args, kwargs)
        return MagicMock(), ["path1"], []


class TestStorageClient:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, monkeypatch):
        """Patches external dependencies for all tests in this class."""
        monkeypatch.setattr(storage_client_module, "Uploader", DummyUploader)
        monkeypatch.setattr(storage_client_module, "Downloader", DummyDownloader)
        monkeypatch.setattr(storage_client_module, "ItemClient", Mock)

    @pytest.fixture
    def storage_client(self):
        """Initializes StorageClient with a mock client."""
        dummy_client = Mock()
        return StorageClient(dummy_client)

    def test_storage_client_upload_item(self, storage_client):
        """Test the upload_item proxy method passes all args correctly."""

        result = storage_client.upload_item(
            "item_id", PROJECT_ID, assets_path="path", max_workers=2
        )

        assert result == ("uploaded_item", ["key1"], [])

        args, kwargs = storage_client.uploader.upload_called_with
        assert kwargs == {
            "item": "item_id",
            "project_id": PROJECT_ID,
            "assets_path": "path",
            "included_assets": True,
            "max_workers": 2,
            "time_out": 3600,
        }

    def test_storage_client_download_assets(self, storage_client, tmp_path):
        """Test the download_assets proxy method passes all args correctly."""

        TEST_ITEM = "test-item-1"
        TEST_COLLECTION = "test-coll-1"
        TEST_PATH = str(tmp_path / "downloads")

        result = storage_client.download_assets(
            TEST_ITEM,
            TEST_COLLECTION,
            target_path=TEST_PATH,
            included_assets=["a1"],
            overwrite=False,
        )

        assert isinstance(result, tuple)
        assert len(result) == 3

        args, kwargs = storage_client.downloader.download_called_with
        assert kwargs == {
            "item": TEST_ITEM,
            "collection_id": TEST_COLLECTION,
            "target_path": TEST_PATH,
            "included_assets": ["a1"],
            "overwrite": False,
            "max_workers": 4,
            "time_out": 3600,
        }

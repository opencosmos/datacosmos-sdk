"""Unit tests for StorageClient.delete_item_with_assets method."""

from unittest.mock import MagicMock, patch

import pytest

from datacosmos.exceptions.item_error import ItemNotFoundError
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.delete_result import DeleteResult
from datacosmos.stac.storage.storage_client import StorageClient


@pytest.fixture
def mock_client():
    """Provides a mock DatacosmosClient."""
    client = MagicMock()
    client.config = MagicMock()
    client.config.datacosmos_cloud_storage.as_domain_url.return_value = MagicMock(
        with_suffix=lambda path: f"https://mock.storage.com{path}"
    )
    return client


@pytest.fixture
def sample_item():
    """Creates a sample DatacosmosItem for testing."""
    return DatacosmosItem(
        id="test-item-1",
        type="Feature",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
            ],
        },
        bbox=[0.0, 0.0, 1.0, 1.0],
        properties={
            "datetime": "2023-01-01T12:00:00Z",
            "processing:level": "l1a",
            "sat:platform_international_designator": "TEST-SAT-1",
        },
        collection="test-collection",
        links=[],
        assets={
            "thumbnail": Asset(
                href="https://storage.example.com/thumb.jpg",
                title="Thumbnail",
                description="A thumbnail image",
                type="image/jpeg",
                roles=["thumbnail"],
            ),
            "data": Asset(
                href="https://storage.example.com/data.tif",
                title="Data",
                description="The main data file",
                type="image/tiff",
                roles=["data"],
            ),
        },
    )


class TestDeleteResult:
    """Tests for the DeleteResult dataclass."""

    def test_all_assets_deleted_true(self, sample_item):
        """Test all_assets_deleted returns True when no failures."""
        result = DeleteResult(
            item=sample_item,
            item_deleted=True,
            successful_assets=["thumbnail", "data"],
            failed_assets=[],
        )
        assert result.all_assets_deleted is True

    def test_all_assets_deleted_false(self, sample_item):
        """Test all_assets_deleted returns False when there are failures."""
        result = DeleteResult(
            item=sample_item,
            item_deleted=True,
            successful_assets=["thumbnail"],
            failed_assets=[{"asset_key": "data", "error": "Not found"}],
        )
        assert result.all_assets_deleted is False

    def test_fully_deleted_true(self, sample_item):
        """Test fully_deleted returns True when item and all assets deleted."""
        result = DeleteResult(
            item=sample_item,
            item_deleted=True,
            successful_assets=["thumbnail", "data"],
            failed_assets=[],
        )
        assert result.fully_deleted is True

    def test_fully_deleted_false_item_not_deleted(self, sample_item):
        """Test fully_deleted returns False when item not deleted."""
        result = DeleteResult(
            item=sample_item,
            item_deleted=False,
            successful_assets=["thumbnail", "data"],
            failed_assets=[],
        )
        assert result.fully_deleted is False


class TestStorageClientDeleteItemWithAssets:
    """Tests for StorageClient.delete_item_with_assets method."""

    @pytest.fixture
    def storage_client(self, mock_client):
        """Creates a StorageClient with mocked dependencies."""
        with patch(
            "datacosmos.stac.storage.storage_client.Uploader"
        ) as mock_uploader_cls, patch(
            "datacosmos.stac.storage.storage_client.Downloader"
        ) as mock_downloader_cls, patch(
            "datacosmos.stac.storage.storage_client.ItemClient"
        ) as mock_item_client_cls:
            mock_uploader = MagicMock()
            mock_downloader = MagicMock()
            mock_item_client = MagicMock()

            mock_uploader_cls.return_value = mock_uploader
            mock_downloader_cls.return_value = mock_downloader
            mock_item_client_cls.return_value = mock_item_client

            client = StorageClient(mock_client)
            client._item_client = mock_item_client
            client.uploader = mock_uploader
            return client

    def test_delete_item_with_assets_success(self, storage_client, sample_item):
        """Test successful deletion of item and all assets."""
        storage_client._item_client.fetch_item.return_value = sample_item
        storage_client._item_client.delete_item.return_value = None
        storage_client.uploader.delete_file = MagicMock()

        result = storage_client.delete_item_with_assets("test-item-1", "test-collection")

        assert isinstance(result, DeleteResult)
        assert result.item_deleted is True
        assert result.fully_deleted is True
        assert len(result.successful_assets) == 2
        assert "thumbnail" in result.successful_assets
        assert "data" in result.successful_assets

    def test_delete_item_with_assets_item_not_found(self, storage_client):
        """Test that ItemNotFoundError is raised when item doesn't exist."""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = HTTPError(response=mock_response)
        storage_client._item_client.fetch_item.side_effect = http_error

        with pytest.raises(ItemNotFoundError) as exc_info:
            storage_client.delete_item_with_assets("nonexistent", "test-collection")

        assert exc_info.value.item_id == "nonexistent"
        assert exc_info.value.collection_id == "test-collection"

    def test_delete_item_with_assets_skip_storage(self, storage_client, sample_item):
        """Test deletion with delete_from_storage=False."""
        storage_client._item_client.fetch_item.return_value = sample_item
        storage_client._item_client.delete_item.return_value = None

        result = storage_client.delete_item_with_assets(
            "test-item-1", "test-collection", delete_from_storage=False
        )

        assert result.item_deleted is True
        # No assets should be in successful list since we didn't delete them
        assert len(result.successful_assets) == 0
        assert len(result.failed_assets) == 0

    def test_delete_item_with_assets_partial_failure(self, storage_client, sample_item):
        """Test deletion when some assets fail to delete."""
        storage_client._item_client.fetch_item.return_value = sample_item
        storage_client._item_client.delete_item.return_value = None

        # Make delete_file fail for one asset
        def side_effect(href):
            if "data.tif" in href:
                raise Exception("Permission denied")
            return None

        storage_client.uploader.delete_file = MagicMock(side_effect=side_effect)

        result = storage_client.delete_item_with_assets("test-item-1", "test-collection")

        assert result.item_deleted is True
        assert result.fully_deleted is False
        assert "thumbnail" in result.successful_assets
        assert len(result.failed_assets) == 1
        assert result.failed_assets[0]["asset_key"] == "data"

    def test_delete_item_with_assets_no_assets(self, storage_client):
        """Test deletion of item with no assets."""
        item_no_assets = DatacosmosItem(
            id="test-item-1",
            type="Feature",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            bbox=[0.0, 0.0, 1.0, 1.0],
            properties={
                "datetime": "2023-01-01T12:00:00Z",
                "processing:level": "l1a",
                "sat:platform_international_designator": "TEST-SAT-1",
            },
            collection="test-collection",
            links=[],
            assets={},
        )
        storage_client._item_client.fetch_item.return_value = item_no_assets
        storage_client._item_client.delete_item.return_value = None

        result = storage_client.delete_item_with_assets("test-item-1", "test-collection")

        assert result.item_deleted is True
        assert result.fully_deleted is True
        assert len(result.successful_assets) == 0
        assert len(result.failed_assets) == 0

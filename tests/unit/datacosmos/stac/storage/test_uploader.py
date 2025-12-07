import json
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

import datacosmos.stac.storage.uploader as uploader_module
from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.upload_result import UploadResult
from datacosmos.stac.storage.uploader import Uploader

PROJECT_ID = "proj123"


class FakeClient:
    def __init__(self):
        self.config = Mock()
        self.config.datacosmos_cloud_storage.as_domain_url.return_value = Path(
            "https://storage.example.com"
        )
        self.config.datacosmos_public_cloud_storage.as_domain_url.return_value = Path(
            "https://public.example.com"
        )
        self.put = Mock()


class FakeItemClient:
    def __init__(self):
        self.added = None

    def add_item(self, item):
        self.added = item


@pytest.fixture(autouse=True)
def patch_item_client(monkeypatch):
    fake_item_client = FakeItemClient()
    monkeypatch.setattr(uploader_module, "ItemClient", lambda client: fake_item_client)
    return fake_item_client


@pytest.fixture(autouse=True)
def patch_upload_path(monkeypatch):
    def _dummy_from_item_path(cls, item, project_id, collection_id, asset_name):
        return f"project/{project_id or collection_id}/{item.id}/{asset_name}"

    monkeypatch.setattr(
        uploader_module.UploadPath,
        "from_item_path",
        classmethod(_dummy_from_item_path),
    )


@pytest.fixture
def uploader():
    client = FakeClient()
    return Uploader(client)


@pytest.fixture
def simple_item(tmp_path):
    file_path_1 = tmp_path / "data1.tif"
    file_path_1.write_text("content1")
    file_path_2 = tmp_path / "data2.tif"
    file_path_2.write_text("content2")

    asset_1 = Asset(
        href=file_path_1.name,
        title="asset1",
        description="desc1",
        type="image/tiff",
        roles=["data"],
    )
    asset_2 = Asset(
        href=file_path_2.name,
        title="asset2",
        description="desc2",
        type="image/tiff",
        roles=["data"],
    )

    item = DatacosmosItem(
        id="item1",
        type="Feature",
        stac_version="1.0.0",
        stac_extensions=[],
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
            ],
        },
        properties={
            "datetime": "2023-01-01T12:00:00Z",
            "processing:level": "l1a",
            "sat:platform_international_designator": "sat123",
        },
        links=[],
        assets={"file1": asset_1, "file2": asset_2},
        collection="collection1",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    return item, str(tmp_path)


class TestUploader:
    """Tests for the multithreaded batch functionality and utility methods of the Uploader."""

    def test_save_item_success(self, simple_item, tmp_path):
        """Test that the save_item method correctly serializes and saves the item."""
        item, _ = simple_item
        save_dir = tmp_path / "saved_items"

        saved_path = Uploader.save_item(item, str(save_dir))

        expected_path = save_dir / f"{item.id}.json"

        assert Path(saved_path).exists()
        assert Path(saved_path) == expected_path

        with open(saved_path, "r") as f:
            content = json.load(f)
            assert content["id"] == item.id
            assert content["collection"] == item.collection
            assert content["properties"]["datetime"] == "2023-01-01T12:00:00Z"

    def test_load_item_success(self, simple_item, tmp_path):
        """Test that the load_item method correctly deserializes the item."""
        item, _ = simple_item
        save_path = tmp_path / "temp_item.json"

        with open(save_path, "w") as f:
            f.write(item.model_dump_json(exclude_none=True, by_alias=True))

        loaded_item = Uploader.load_item(str(save_path))

        assert isinstance(loaded_item, DatacosmosItem)
        assert loaded_item.id == item.id
        assert (
            loaded_item.properties["processing:level"]
            == item.properties["processing:level"]
        )
        assert loaded_item.collection == item.collection

    def test_upload_item_success(
        self, uploader, simple_item, patch_item_client, monkeypatch
    ):
        """Test successful parallel upload and item registration."""
        item, assets_path = simple_item

        # Mock the parallel runner to simulate success (returns List[str] of asset keys)
        mock_run_in_threads = MagicMock(return_value=(["file1", "file2"], []))
        monkeypatch.setattr(
            uploader_module.Uploader, "run_in_threads", mock_run_in_threads
        )

        uploader.upload_from_file = Mock()
        uploader._update_asset_href = Mock()

        result = uploader.upload_item(
            item, PROJECT_ID, assets_path=assets_path, max_workers=2, time_out=30
        )

        assert isinstance(result, UploadResult)
        assert result.item is item
        assert result.successful_assets == ["file1", "file2"]
        assert result.failed_assets == []

        assert mock_run_in_threads.call_count == 1
        assert patch_item_client.added is item

    def test_upload_item_partial_failure(
        self, uploader, simple_item, patch_item_client, monkeypatch
    ):
        """Test parallel upload where some assets fail, and the on_error hook is executed."""
        item, assets_path = simple_item

        mock_exception = Exception("Upload failed due to permissions.")
        mock_on_error = MagicMock()

        # Mock the parallel runner to simulate 1 success ('file1') and 1 failure ('file2')
        raw_failures = [
            {
                "error": str(mock_exception),
                "exception": mock_exception,
                "job_args": (item, "file2", assets_path, PROJECT_ID, None),
            }
        ]
        mock_run_in_threads = MagicMock(return_value=(["file1"], raw_failures))
        monkeypatch.setattr(
            uploader_module.Uploader, "run_in_threads", mock_run_in_threads
        )

        uploader.upload_from_file = Mock()
        uploader._update_asset_href = Mock()

        result = uploader.upload_item(
            item,
            PROJECT_ID,
            assets_path=assets_path,
            max_workers=2,
            time_out=30,
            on_error=mock_on_error,
        )

        assert isinstance(result, UploadResult)
        assert result.item is item
        assert result.successful_assets == ["file1"]
        assert len(result.failed_assets) == 1

        failed_asset = item.assets["file2"]
        mock_on_error.assert_called_once_with(failed_asset, mock_exception)

        assert patch_item_client.added is item

    def test_upload_item_timeout_raises_error(
        self, uploader, simple_item, patch_item_client, monkeypatch
    ):
        """Test that a timeout error still aborts the process immediately (handled in run_in_threads)."""
        item, assets_path = simple_item

        # Mock the parallel runner to raise the DatacosmosError (simulating timeout)
        mock_run_in_threads = MagicMock(
            side_effect=DatacosmosError("Batch processing failed: operation timed out.")
        )
        monkeypatch.setattr(
            uploader_module.Uploader, "run_in_threads", mock_run_in_threads
        )

        with pytest.raises(DatacosmosError, match="operation timed out"):
            uploader.upload_item(item, PROJECT_ID, assets_path=assets_path)

        assert patch_item_client.added is None

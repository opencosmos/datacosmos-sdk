from datetime import datetime
from unittest.mock import MagicMock

import pytest

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.dataclasses.upload_path import UploadPath


class DummyItem:
    """Minimal stand-in for DatacosmosItem (only .id and .properties are used)."""

    def __init__(self, id_: str, dt: datetime):
        self.id = id_
        self.properties = {"datetime": dt}
        self.assets = {"asset1": MagicMock(href="some/href")}
        self.collection = "test-collection"


class TestUploadPath:

    TEST_DATETIME = datetime(2025, 9, 10, 12, 30, 0)
    TEST_ITEM_ID = "item-123"
    TEST_ASSET_NAME = "file.tif"

    def test_str_output_project_path(self):
        """Test the string output for the project path structure."""
        up = UploadPath(
            project_id="proj123",
            collection_id=None,
            item_id=self.TEST_ITEM_ID,
            asset_name=self.TEST_ASSET_NAME,
        )
        assert str(up) == "project/proj123/item-123/file.tif"

    def test_str_output_catalog_path(self):
        """Test the string output for the full catalog path structure (with dates)."""
        up = UploadPath(
            project_id=None,
            collection_id="coll_abc",
            item_id=self.TEST_ITEM_ID,
            asset_name=self.TEST_ASSET_NAME,
            year="2025",
            month="09",
            day="10",
        )
        assert str(up) == "catalog/coll_abc/2025/09/10/item-123/file.tif"

    def test_str_output_fallback_path(self):
        """Test the string output when insufficient data is provided (no project/collection)."""
        up = UploadPath(
            project_id=None,
            collection_id=None,
            item_id=self.TEST_ITEM_ID,
            asset_name=self.TEST_ASSET_NAME,
        )
        assert str(up) == "item-123/file.tif"

    def test_from_item_path_project_upload(self):
        """Test path creation when project_id is provided."""
        item = DummyItem(id_=self.TEST_ITEM_ID, dt=self.TEST_DATETIME)

        up = UploadPath.from_item_path(
            item=item,
            project_id="proj456",
            asset_name="test_asset.txt",
            collection_id=item.collection,
        )

        assert up.project_id == "proj456"
        assert up.collection_id == item.collection
        assert up.year == "2025"
        assert up.month == "09"
        assert up.day == "10"

    def test_from_item_path_catalog_upload(self):
        """Test path creation when project_id is None, forcing catalog path."""
        item = DummyItem(id_=self.TEST_ITEM_ID, dt=self.TEST_DATETIME)

        up = UploadPath.from_item_path(
            item=item,
            project_id=None,
            asset_name="test_asset.txt",
            collection_id="new_coll",
        )

        assert up.project_id is None
        assert up.collection_id == "new_coll"
        assert up.year == "2025"
        assert up.month == "09"
        assert up.day == "10"

    def test_from_item_path_missing_required_ids_raises(self):
        """Test that a ValueError is raised when both project_id and collection_id are missing."""
        item = DummyItem(id_=self.TEST_ITEM_ID, dt=self.TEST_DATETIME)

        with pytest.raises(
            ValueError, match="Either project_id or collection_id must be provided"
        ):
            UploadPath.from_item_path(
                item=item,
                project_id=None,
                asset_name="test_asset.txt",
                collection_id=None,
            )

    def test_from_item_path_missing_datetime_uses_none(self):
        """Test that if item.properties['datetime'] is missing (raises), date fields are None."""
        item = MagicMock(spec=DatacosmosItem)
        item.id = "no-dt-item"
        item.properties = {"datetime": "invalid-date-format"}

        up = UploadPath.from_item_path(
            item=item, project_id="proj", asset_name="asset.tif", collection_id="c"
        )

        assert up.year is None
        assert up.month is None
        assert up.day is None

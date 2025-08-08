from unittest.mock import MagicMock

import pytest

from datacosmos.stac.storage.dataclasses.upload_path import UploadPath


class DummyItem:
    """Minimal stand-in for DatacosmosItem (only .id is used)."""

    def __init__(self, id_: str):
        self.id = id_
        self.assets = {"asset1": MagicMock(href="some/href")}


class TestUploadPath:
    def test_str_output(self):
        up = UploadPath(
            project_id="proj123",
            item_id="item123",
            asset_name="file.tif",
        )
        assert str(up) == "project/proj123/item123/file.tif"

    def test_from_item_path(self):
        item = DummyItem(id_="item123")
        up = UploadPath.from_item_path(item, "proj123", "file.tif")

        assert up.project_id == "proj123"
        assert up.item_id == "item123"
        assert up.asset_name == "file.tif"

    def test_from_path_valid(self):
        path_str = "project/proj123/item123/file.tif"
        up = UploadPath.from_path(path_str)

        assert up.project_id == "proj123"
        assert up.item_id == "item123"
        assert up.asset_name == "file.tif"

    def test_from_path_invalid_raises(self):
        with pytest.raises(ValueError):
            UploadPath.from_path("invalid/path/structure")

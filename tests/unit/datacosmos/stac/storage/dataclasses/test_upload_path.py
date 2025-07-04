from unittest.mock import MagicMock

import pytest

from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.storage.dataclasses.upload_path import UploadPath


class DummyItem:
    def __init__(self, id_, datetime_str, level_str, assets):
        self.id = id_
        self.properties = {
            "datetime": datetime_str,
            "processing:level": level_str,
        }
        self.assets = assets


class TestUploadPath:
    def test_str_output(self):
        up = UploadPath(
            mission="MissionX",
            level=ProcessingLevel.L1A,
            day=9,
            month=5,
            year=2023,
            id="item123",
            path="file.tif",
        )
        expected = "full/missionx/l1a/2023/05/09/item123/file.tif"
        assert str(up) == expected

    def test_from_item_path_with_mission(self):
        item = DummyItem(
            id_="item123",
            datetime_str="2023-05-09T12:00:00Z",
            level_str="L1A",
            assets={"asset1": MagicMock(href="some/href")},
        )
        up = UploadPath.from_item_path(item, "MissionX", "file.tif")
        assert up.mission == "MissionX"
        assert up.level == ProcessingLevel.L1A
        assert up.day == 9
        assert up.month == 5
        assert up.year == 2023
        assert up.id == "item123"
        assert up.path == "file.tif"

    def test_from_path_valid(self):
        path_str = "missionx/L1A/2023/05/09/item123/file.tif"
        up = UploadPath.from_path(path_str)
        assert up.mission == "missionx"
        assert up.level == ProcessingLevel.L1A
        assert up.year == 2023
        assert up.month == 5
        assert up.day == 9
        assert up.id == "item123"
        assert up.path == "file.tif"

    def test_from_path_invalid_raises(self):
        with pytest.raises(ValueError):
            UploadPath.from_path("too/short/path")

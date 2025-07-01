from pathlib import Path
from unittest.mock import MagicMock

import pytest

from datacosmos.stac.item.models.asset import Asset
from datacosmos.uploader.datacosmos_uploader import DatacosmosUploader


class DummyClient:
    def __init__(self):
        self.config = MagicMock()
        self.config.datacosmos_cloud_storage.as_domain_url.return_value = Path(
            "http://fakecloud/"
        )
        self.config.datacosmos_public_cloud_storage.as_domain_url.return_value = Path(
            "http://publiccloud/"
        )


class DummyItem:
    def __init__(self, assets):
        self.assets = assets


@pytest.fixture
def uploader_and_dir(tmp_path, monkeypatch):
    client = DummyClient()
    uploader = DatacosmosUploader(client)
    monkeypatch.setattr(
        "datacosmos.uploader.datacosmos_uploader.UploadPath.from_item_path",
        lambda *args, **kwargs: Path("destination/path.txt"),
    )
    monkeypatch.setattr(
        DatacosmosUploader, "_update_asset_href", lambda self, asset: None
    )
    return uploader, tmp_path


class TestDatacosmosUploader:
    def test_upload_item_with_local_asset(self, uploader_and_dir):
        uploader, assets_dir = uploader_and_dir
        # Prepare a local asset file
        file_path = assets_dir / "asset1.txt"
        file_path.write_text("dummy")
        asset = Asset(
            type="test_type",
            href="https://example.com/sample-image.tiff",
            description="test asset",
            title="Sample Image",
            roles=["data"],
        )
        item = DummyItem({"a1": asset})

        uploader.item_client.add_item = MagicMock()

        returned = uploader.upload_item(item, assets_path=str(assets_dir))

        assert returned is item
        uploader.item_client.add_item.assert_called_once_with(item)

    def test_upload_item_with_remote_asset(self, uploader_and_dir):
        uploader, assets_dir = uploader_and_dir
        # Asset href with subpath; local file only exists by name
        asset = Asset(
            type="test_type",
            href="https://example.com/sample-image.tiff",
            description="test asset",
            title="Sample Image",
            roles=["data"],
        )
        file_path = assets_dir / "remote.txt"
        file_path.write_text("dummy")
        item = DummyItem({"r1": asset})

        uploader.item_client.add_item = MagicMock()

        returned = uploader.upload_item(item, assets_path=str(assets_dir))

        assert returned is item
        uploader.item_client.add_item.assert_called_once()

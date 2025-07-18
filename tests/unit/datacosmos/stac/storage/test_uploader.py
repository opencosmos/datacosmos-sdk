from pathlib import Path
from unittest.mock import Mock

import pytest

import datacosmos.stac.storage.uploader as uploader_module
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.uploader import Uploader


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
    monkeypatch.setattr(
        uploader_module.UploadPath,
        "from_item_path",
        classmethod(lambda cls, item, mission_name, filename: filename),
    )


@pytest.fixture
def uploader():
    client = FakeClient()
    return Uploader(client)


@pytest.fixture
def simple_item(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("content")

    asset = Asset(
        href=file_path.name,
        title="dummy",
        description="dummy",
        type="text/plain",
        roles=None,
        eo_bands=None,
        raster_bands=None,
    )

    item = DatacosmosItem(
        id="item1",
        type="Feature",
        stac_version="1.0.0",
        stac_extensions=[],
        geometry={},
        properties={},
        links=[],
        assets={"file": asset},
        collection="collection1",
        bbox=(0.0, 0.0, 0.0, 0.0),
    )
    return item, str(tmp_path)


def test_upload_item(uploader, simple_item, patch_item_client):
    item, assets_path = simple_item
    uploader.upload_from_file = Mock()
    uploader._update_asset_href = Mock()

    result = uploader.upload_item(
        item, assets_path=assets_path, max_workers=2, time_out=30
    )

    # Verify that upload_from_file was called once for our one asset
    assert uploader.upload_from_file.call_count == 1
    # Confirm that add_item was called on the item client and returned item
    assert patch_item_client.added is result

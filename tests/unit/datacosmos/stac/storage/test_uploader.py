from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

import datacosmos.stac.storage.uploader as uploader_module
from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
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
    def _dummy_from_item_path(cls, item, project_id, asset_name):  # new sig
        return f"project/{project_id}/{item.id}/{asset_name}"

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
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [0.0, 0.0],
                    [1.0, 0.0],
                    [1.0, 1.0],
                    [0.0, 1.0],
                    [0.0, 0.0],
                ]
            ],
        },
        properties={
            "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processing:level": "level1a",
            "sat:platform_international_designator": "sat123",
        },
        links=[],
        assets={"file": asset},
        collection="collection1",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    return item, str(tmp_path)


def test_upload_item(uploader, simple_item, patch_item_client):
    item, assets_path = simple_item
    uploader.upload_from_file = Mock()
    uploader._update_asset_href = Mock()

    result = uploader.upload_item(
        item, PROJECT_ID, assets_path=assets_path, max_workers=2, time_out=30
    )

    assert uploader.upload_from_file.call_count == 1
    assert patch_item_client.added is result

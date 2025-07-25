from unittest.mock import Mock

import datacosmos.stac.storage.storage_client as storage_client_module
from datacosmos.stac.storage.storage_client import StorageClient


class DummyUploader:
    def __init__(self, client):
        self.client = client
        self.upload_called_with = None

    def upload_item(self, *args, **kwargs):
        self.upload_called_with = (args, kwargs)
        return "uploaded"


def test_storage_client_upload_item(monkeypatch):
    dummy_client = Mock()
    monkeypatch.setattr(storage_client_module, "Uploader", DummyUploader)
    storage = StorageClient(dummy_client)

    result = storage.upload_item("item", assets_path="path", max_workers=2)

    assert result == "uploaded"
    # Check that uploader.upload_item was called with correct args
    uploader_instance = storage.uploader
    assert uploader_instance.upload_called_with[1] == {
        "item": "item",
        "assets_path": "path",
        "included_assets": True,
        "max_workers": 2,
        "time_out": 3600,
    }

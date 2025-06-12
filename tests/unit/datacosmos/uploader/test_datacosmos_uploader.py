from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.uploader.dataclasses.upload_path import UploadPath
from datacosmos.uploader.datacosmos_uploader import DatacosmosUploader


class TestDatacosmosUploader:
    @pytest.fixture
    def mock_client(self):
        mock = MagicMock()
        mock.config.mission_id = 55
        mock.config.environment = "test"
        mock.config.datacosmos_cloud_storage.as_domain_url.return_value = MagicMock(
            with_suffix=lambda x: f"https://mockstorage.com/{x}",
            with_base=lambda x: f"https://mockstorage.com/{x}",
        )
        return mock

    def test_init_sets_attributes(self, mock_client):
        uploader = DatacosmosUploader(mock_client)

        assert uploader.datacosmos_client == mock_client
        assert uploader.item_client is not None
        assert uploader.base_url.startswith("https://mockstorage.com/")

    @patch("datacosmos.datacosmos_client.DatacosmosClient.put")
    @patch(
        "datacosmos.uploader.datacosmos_uploader.DatacosmosUploader.upload_from_folder"
    )
    @patch(
        "datacosmos.uploader.datacosmos_uploader.DatacosmosUploader._update_item_assets"
    )
    def test_upload_and_register_item(
        self, mock_update, mock_upload_folder, mock_put, mock_client, tmp_path
    ):
        import json

        dummy_item_data = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "stac_extensions": [],
            "id": "item123",
            "collection": "mycollection",
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "bbox": [0.0, 0.0, 0.0, 0.0],
            "properties": {
                "datetime": "2023-05-09T12:00:00Z",
                "processing:level": "L1A",
            },
            "assets": {
                "asset1": {
                    "href": "some/path.tif",
                    "type": "image/tiff",
                    "title": "Asset 1",
                    "description": "Test asset",
                    "roles": ["data"],
                }
            },
            "links": [],
        }

        file_path = tmp_path / "myitem.json"
        file_path.write_text(json.dumps(dummy_item_data))

        # Setup mock_put to return a real-looking response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        uploader = DatacosmosUploader(mock_client)

        # Patch _load_item to return a valid DatacosmosItem
        mock_item = DatacosmosItem.parse_obj(dummy_item_data)

        with patch.object(uploader, "_load_item", return_value=mock_item), patch.object(
            uploader, "_delete_existing_item"
        ) as mock_delete, patch.object(
            uploader.item_client, "create_item"
        ) as mock_create_item:

            uploader.upload_and_register_item(str(file_path))

            mock_delete.assert_called_once_with("mycollection", "item123")
            mock_upload_folder.assert_called_once()
            mock_update.assert_called_once()
            mock_create_item.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake content")
    def test_upload_file_success(self, mock_file, mock_client):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.put.return_value = mock_response

        uploader = DatacosmosUploader(mock_client)
        uploader.upload_file("src.txt", "dst/path.txt")

        mock_client.put.assert_called_once_with(
            "https://mockstorage.com/dst/path.txt", data=mock_file()
        )
        mock_response.raise_for_status.assert_called_once()

    def test_upload_from_folder_uploads_files(self, tmp_path, mock_client):
        folder = tmp_path / "data"
        folder.mkdir()
        (folder / "file1.txt").write_text("File 1")
        (folder / "file2.txt").write_text("File 2")

        dst = UploadPath(
            mission="mission",
            level=ProcessingLevel.L1A,
            day=1,
            month=1,
            year=2020,
            id="item123",
            path="",
        )

        uploader = DatacosmosUploader(mock_client)

        with patch.object(uploader, "upload_file") as mock_upload:
            uploader.upload_from_folder(str(folder), dst)
            calls = [
                call(
                    str(folder / "file1.txt"),
                    dst.__class__(**{**dst.__dict__, "path": "file1.txt"}),
                ),
                call(
                    str(folder / "file2.txt"),
                    dst.__class__(**{**dst.__dict__, "path": "file2.txt"}),
                ),
            ]
            mock_upload.assert_has_calls(calls, any_order=True)

    def test_upload_from_folder_raises_on_file_path(self, tmp_path, mock_client):
        file_path = tmp_path / "file.txt"
        file_path.write_text("I'm a file")

        uploader = DatacosmosUploader(mock_client)
        dst = UploadPath(
            mission="mission",
            level=ProcessingLevel.L1A,
            day=1,
            month=1,
            year=2020,
            id="item123",
            path="",
        )

        with pytest.raises(ValueError, match="Source path should not be a file path"):
            uploader.upload_from_folder(str(file_path), dst)

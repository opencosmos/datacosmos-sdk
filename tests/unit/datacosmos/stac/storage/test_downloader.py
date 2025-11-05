from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pystac import Item

from datacosmos.stac.storage.downloader import Downloader

ITEM_ID = "test-item-1"
COLLECTION_ID = "test-collection"
SUCCESS_KEY = "band_data"


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config = MagicMock()
    client.config.datacosmos_cloud_storage.as_domain_url.return_value = (
        "https://mock.storage.com"
    )
    return client


@pytest.fixture
def downloader(mock_clients, monkeypatch, tmp_path):
    mock_client, mock_item_client = mock_clients

    SAFE_ASSETS_DIR = str(tmp_path / "download_test_dir")

    with patch("datacosmos.stac.storage.downloader.ItemClient") as MockItemClient:
        MockItemClient.return_value = mock_item_client
        downloader_instance = Downloader(mock_client)

    monkeypatch.setattr(Path, "cwd", lambda: Path(SAFE_ASSETS_DIR))

    return downloader_instance


@pytest.fixture
def mock_clients():
    mock_client = MagicMock()
    mock_item_client = MagicMock()
    return mock_client, mock_item_client


@pytest.fixture
def mock_item():
    asset_data = {
        SUCCESS_KEY: {
            "href": "https://platform.com/asset1.tif",
            "title": "Data",
            "type": "image/tiff",
        },
        "thumbnail": {
            "href": "https://platform.com/thumb.png",
            "title": "Preview",
            "type": "image/png",
        },
    }

    item = MagicMock(spec=Item)
    item.id = ITEM_ID
    item.assets = asset_data

    item.to_dict.return_value = {"id": ITEM_ID, "assets": asset_data}
    return item


class TestDownloader:
    def test_download_assets_success_and_orchestration(
        self, downloader, mock_item, mock_clients, monkeypatch
    ):
        mock_item_client = mock_clients[1]

        mock_item_client.fetch_item.return_value = mock_item

        MOCKED_ASSETS_DIR = Path.cwd() / mock_item.id
        SUCCESS_PATH = str(MOCKED_ASSETS_DIR / "asset1.tif")

        mock_success_result = [{SUCCESS_KEY: SUCCESS_PATH}]
        mock_run_in_threads = MagicMock(return_value=(mock_success_result, []))
        monkeypatch.setattr(downloader, "run_in_threads", mock_run_in_threads)

        result_item, successes, failures = downloader.download_assets(
            item=ITEM_ID,
            collection_id=COLLECTION_ID,
            included_assets=True,
        )

        mock_item_client.fetch_item.assert_called_once_with(
            item_id=ITEM_ID, collection_id=COLLECTION_ID
        )
        mock_run_in_threads.assert_called_once()

        assert result_item is mock_item
        assert len(successes) == 1
        assert failures == []


def test_download_assets_skip_existing(
    downloader, mock_item, mock_clients, monkeypatch, tmp_path
):
    """Tests that assets are skipped if overwrite=False and the file exists."""

    mock_item_client = mock_clients[1]
    mock_item_client.fetch_item.return_value = mock_item

    SAFE_ASSETS_DIR = tmp_path / "downloads"
    SAFE_ASSETS_DIR.mkdir()
    SKIP_PATH = str(SAFE_ASSETS_DIR / "thumb.png")

    Path(SKIP_PATH).write_text("exists")

    mock_successes = [{"thumbnail": SKIP_PATH}]
    mock_run_in_threads = MagicMock(return_value=(mock_successes, []))
    monkeypatch.setattr(downloader, "run_in_threads", mock_run_in_threads)

    mock_download_file = MagicMock()
    monkeypatch.setattr(downloader, "download_file", mock_download_file)

    result_item, successes, failures = downloader.download_assets(
        item=ITEM_ID,
        collection_id=COLLECTION_ID,
        target_path=str(SAFE_ASSETS_DIR),
        included_assets=["thumbnail"],
        overwrite=False,
    )

    mock_download_file.assert_not_called()

    assert len(successes) == 1
    assert failures == []


def test_download_assets_no_assets_included(
    downloader, mock_item, mock_clients, monkeypatch
):
    """Tests that the concurrency runner is NOT called when included_assets=False."""

    mock_item_client = mock_clients[1]
    mock_item_client.fetch_item.return_value = mock_item

    mock_run_in_threads = MagicMock()
    monkeypatch.setattr(downloader, "run_in_threads", mock_run_in_threads)

    result_item, successes, failures = downloader.download_assets(
        item=ITEM_ID, collection_id=COLLECTION_ID, included_assets=False
    )

    assert result_item is mock_item
    assert successes == []
    assert failures == []

    mock_run_in_threads.assert_not_called()

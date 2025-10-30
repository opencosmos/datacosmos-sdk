from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pystac import Item

from datacosmos.stac.storage.downloader import Downloader

ITEM_ID = "test-item-1"
COLLECTION_ID = "test-collection"
ASSETS_DIR = "/tmp/download_test"
SUCCESS_KEY = "band_data"


@pytest.fixture
def mock_client():
    """Provides a mock DatacosmosClient with the required config structure."""
    client = MagicMock()
    client.config = MagicMock()
    client.config.datacosmos_cloud_storage.as_domain_url.return_value = (
        "https://mock.storage.com"
    )
    return client


@pytest.fixture
def downloader(mock_clients, monkeypatch):
    """Instantiates the Downloader class with mocked dependencies."""
    mock_client, mock_item_client = mock_clients

    with patch("datacosmos.stac.storage.downloader.ItemClient") as MockItemClient:
        MockItemClient.return_value = mock_item_client
        downloader_instance = Downloader(mock_client)

    monkeypatch.setattr(Path, "cwd", lambda: Path(ASSETS_DIR))

    return downloader_instance


@pytest.fixture
def mock_clients():
    """Provides mock clients needed for Downloader initialization."""
    mock_client = MagicMock()
    mock_item_client = MagicMock()
    return mock_client, mock_item_client


@pytest.fixture
def mock_item():
    """Returns a mock pystac.Item with assets and a serializable to_dict method."""

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
        """Tests end-to-end success: fetch, concurrent run, and result collection."""

        mock_item_client = mock_clients[1]

        mock_item_client.fetch_item.return_value = mock_item

        SUCCESS_PATH = str(Path(ASSETS_DIR) / "asset1.tif")
        mock_success_result = [{SUCCESS_KEY: SUCCESS_PATH}]
        mock_run_in_threads = MagicMock(return_value=(mock_success_result, []))
        monkeypatch.setattr(downloader, "run_in_threads", mock_run_in_threads)

        result_item, successes, failures = downloader.download_assets(
            item=ITEM_ID,
            collection_id=COLLECTION_ID,
            target_path=ASSETS_DIR,
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
    downloader, mock_item, mock_clients, monkeypatch
):
    """Tests that assets are skipped if overwrite=False and the file exists."""

    mock_item_client = mock_clients[1]
    mock_item_client.fetch_item.return_value = mock_item

    SKIP_PATH = str(Path(ASSETS_DIR) / "thumb.png")
    mock_successes = [{"thumbnail": SKIP_PATH}]
    mock_run_in_threads = MagicMock(return_value=(mock_successes, []))
    monkeypatch.setattr(downloader, "run_in_threads", mock_run_in_threads)

    def mock_path_exists(path_instance):
        return path_instance.name == "thumb.png"

    with patch("pathlib.Path.exists", side_effect=mock_path_exists, autospec=True):
        mock_download_file = MagicMock()
        monkeypatch.setattr(downloader, "download_file", mock_download_file)

        result_item, successes, failures = downloader.download_assets(
            item=ITEM_ID,
            collection_id=COLLECTION_ID,
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

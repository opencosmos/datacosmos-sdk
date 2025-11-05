"""Handles downloading STAC items and their assets from Datacosmos storage."""

import json
import logging
from pathlib import Path
from typing import Any

from pystac import Item

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.storage.storage_base import StorageBase

_log = logging.getLogger(__name__)


class Downloader(StorageBase):
    """Handles downloading files from Datacosmos storage and orchestrating item downloads."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the downloader."""
        super().__init__(client)
        self.item_client = ItemClient(client)

    def download_assets(
        self,
        item: str,
        collection_id: str,
        target_path: str | None = None,
        included_assets: list[str] | bool = True,
        overwrite: bool = True,
        max_workers: int = 4,
        time_out: float = 60 * 60 * 1,
    ) -> tuple[DatacosmosItem, list[dict[str, str]], list[dict[str, Any]]]:
        """Downloads a STAC item's assets from the catalog in parallel.

        Args:
            item (str): The item ID of the item to download.
            collection_id (str): The ID of the collection containing the item.
            target_path (str | None): The local path to save the assets (defaults to CWD / item_id).
            included_assets (list[str] | bool): Asset keys to include, or True for all.
            overwrite (bool): Whether to overwrite existing files.
            max_workers (int): Maximum number of parallel threads for asset download.
            time_out (float): Timeout in seconds for the entire asset batch download.

        Returns:
            tuple[DatacosmosItem, list[dict[str, str]], list[dict[str, Any]]]:
            The downloaded DatacosmosItem, a list of asset keys mapped to local paths (successes), and a list of failures.
        """
        stac_item = self.item_client.fetch_item(
            item_id=item, collection_id=collection_id
        )
        item_id = stac_item.id

        base_path = Path(target_path) if target_path else Path.cwd() / item_id
        base_path.mkdir(parents=True, exist_ok=True)

        item_json_path = base_path / f"{item_id}.json"
        if overwrite or not item_json_path.exists():
            with open(item_json_path, "w") as f:
                json.dump(stac_item.to_dict(), f)

        if included_assets is False:
            download_assets: list[str] = []
        elif included_assets is True:
            download_assets = list(stac_item.assets.keys())
        elif isinstance(included_assets, list):
            download_assets = included_assets
        else:
            download_assets = []

        jobs = []

        for asset_key in download_assets:
            if asset_key in stac_item.assets:
                jobs.append((stac_item, asset_key, str(base_path), overwrite))
            else:
                _log.warning(
                    f"Requested asset '{asset_key}' not found in STAC item '{item_id}'. Skipping download."
                )

        if not jobs:
            return stac_item, [], []

        successes, failures = self.run_in_threads(
            self._download_asset_worker, jobs, max_workers, time_out
        )

        return stac_item, successes, failures

    def download_file(self, src: str, dst: str) -> None:
        """Download a single file from the specified URL to a local destination path."""
        response = self.client.get(src, stream=True)
        response.raise_for_status()

        with open(dst, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def _download_asset_worker(
        self, item: Item, asset_key: str, base_path: str, overwrite: bool
    ) -> dict[str, str]:
        """Worker function for parallel asset download: fetches asset URL and saves file."""
        asset = item.assets[asset_key]
        asset_url = asset.href  # The URL to download
        local_path = Path(base_path) / Path(asset_url).name

        # Skip if file exists and overwrite is False
        if not overwrite and local_path.exists():
            _log.info(
                f"Asset file already exists at '{local_path}'. Skipping download because overwrite=False."
            )
            return {asset_key: str(local_path)}

        self.download_file(src=asset_url, dst=str(local_path))

        return {asset_key: str(local_path)}

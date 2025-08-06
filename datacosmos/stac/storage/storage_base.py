"""Base class providing common storage helpers (threading, MIME guess, futures)."""

import mimetypes
import os
from concurrent.futures import ThreadPoolExecutor, wait

from datacosmos.datacosmos_client import DatacosmosClient


class StorageBase:
    """Base class providing common storage helpers (threading, MIME guess, futures)."""

    def __init__(self, client: DatacosmosClient):
        """Base class providing common storage helpers (threading, MIME guess, futures)."""
        self.client = client

        if hasattr(client, "config") and client.config:
            self.base_url = client.config.datacosmos_cloud_storage.as_domain_url()
        else:
            self.base_url = None

        self.datacosmos_file_storage = os.getenv("DATACOSMOS_FILE_STORAGE")

    def _guess_mime(self, src: str) -> str:
        mime, _ = mimetypes.guess_type(src)
        return mime or "application/octet-stream"

    def _run_in_threads(self, fn, fn_args, max_workers: int, timeout: float):
        """Run the callable `fn(*args)` over the iterable of jobs in parallel threads.

        `jobs` should be a list of tuples, each tuple unpacked as fn(*args).
        """
        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for args in fn_args:
                futures.append(executor.submit(fn, *args))
        done, not_done = wait(futures, timeout=timeout)
        errors = []
        for future in done:
            try:
                future.result()
            except Exception as e:
                errors.append(e)
        for future in not_done:
            future.cancel()
        if errors:
            raise errors[0]

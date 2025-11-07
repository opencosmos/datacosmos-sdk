"""Base class providing common storage helpers (threading, MIME guess, futures)."""

import mimetypes
from concurrent.futures import Future, ThreadPoolExecutor, wait
from typing import Any, Callable, Iterable

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.datacosmos_error import DatacosmosError


class StorageBase:
    """Base class providing common storage helpers (threading, MIME guess, futures)."""

    def __init__(self, client: DatacosmosClient):
        """Base class providing common storage helpers (threading, MIME guess, futures)."""
        self.client = client
        self.base_url = client.config.datacosmos_cloud_storage.as_domain_url()

    def _guess_mime(self, src: str) -> str:
        mime, _ = mimetypes.guess_type(src)
        return mime or "application/octet-stream"

    def run_in_threads(
        self,
        fn: Callable[..., Any],
        jobs: Iterable[tuple[Any, ...]],
        max_workers: int,
        timeout: float,
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Run the callable `fn(*args)` over the iterable of jobs in parallel threads.

        Collects successes and failures without aborting the batch on individual errors.

        Args:
            fn: The function to execute.
            jobs: An iterable of tuples, where each tuple is unpacked as fn(*args).
            max_workers: Maximum number of threads to use.
            timeout: Timeout for the entire batch.

        Returns:
            A tuple containing (successes: list[Any], failures: list[dict[str, Any]]).
            Failures include the exception and job arguments.

        Raises:
            DatacosmosError: If the entire batch times out.
        """
        futures: list[Future] = []

        # Dictionary to map Future object to its original job arguments
        future_to_job = {}

        executor = ThreadPoolExecutor(max_workers=max_workers)

        try:
            for args in jobs:
                future = executor.submit(fn, *args)
                futures.append(future)
                future_to_job[future] = args  # Store the link to the original job

            # Wait until all futures are done or the timeout is reached
            done, not_done = wait(futures, timeout=timeout)

            successes = []
            failures = []

            for future in done:
                original_args = future_to_job.get(future)
                try:
                    result = future.result()
                except Exception as e:
                    # Capture the original job arguments upon failure
                    failures.append(
                        {"error": str(e), "exception": e, "job_args": original_args}
                    )
                else:
                    successes.append(result)

            if not_done:
                # The executor's shutdown wait must be skipped to allow cancellation
                raise DatacosmosError("Batch processing failed: operation timed out.")

            return successes, failures
        finally:
            # Shutdown without waiting to enable timeout handling
            # The wait call already established which jobs finished
            executor.shutdown(wait=False)

from concurrent.futures import Future
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from datacosmos.stac.storage.storage_base import StorageBase


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
def storage_base(mock_client):
    """Instantiates the StorageBase class."""
    return StorageBase(mock_client)


def create_mock_future(
    success: bool, result: Any = None, exception: Exception = None
) -> Future:
    """Creates a mock Future object to simulate job outcomes."""
    future = Future()
    if success:
        future.set_result(result)
    else:
        future.set_exception(exception or Exception("Simulated job failure"))
    return future


class TestStorageBase:
    """Tests the resilience and concurrency logic of StorageBase.run_in_threads."""

    @patch("datacosmos.stac.storage.storage_base.wait")
    @patch("datacosmos.stac.storage.storage_base.ThreadPoolExecutor", autospec=True)
    def test_run_in_threads_all_success(self, mock_executor, mock_wait, storage_base):
        """Tests batch execution where all jobs complete successfully."""
        jobs = [("job1",), ("job2",), ("job3",)]

        futures = [create_mock_future(True, r) for r in [10, 20, 30]]

        mock_executor.return_value.submit.side_effect = futures
        mock_wait.return_value = (futures, [])

        successes, failures = storage_base.run_in_threads(
            MagicMock(), jobs, max_workers=3, timeout=60
        )

        assert successes == [10, 20, 30]
        assert failures == []
        mock_executor.return_value.shutdown.assert_called_once_with(wait=False)

    @patch("datacosmos.stac.storage.storage_base.wait")
    @patch("datacosmos.stac.storage.storage_base.ThreadPoolExecutor", autospec=True)
    def test_run_in_threads_partial_failure(
        self, mock_executor, mock_wait, storage_base
    ):
        """Tests batch execution where some jobs fail but successful results are collected."""
        successful_future_1 = create_mock_future(True, "Result A")
        failed_future = create_mock_future(False, exception=ValueError("Invalid Input"))
        successful_future_2 = create_mock_future(True, "Result B")

        futures = [successful_future_1, failed_future, successful_future_2]

        mock_executor.return_value.submit.side_effect = futures
        mock_wait.return_value = (futures, [])

        successes, failures = storage_base.run_in_threads(
            MagicMock(), MagicMock(), max_workers=3, timeout=60
        )

        assert len(successes) == 2
        assert len(failures) == 1
        assert isinstance(failures[0]["exception"], ValueError)

        mock_executor.return_value.shutdown.assert_called_once_with(wait=False)

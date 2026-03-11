"""Tests for the is_running_in_opencosmos_cluster function."""

from datacosmos.config.constants import OPENCOSMOS_INTERNAL_CLUSTER_ENV
from datacosmos.config.environment import is_running_in_opencosmos_cluster


class TestOpenCosmosClusterDetection:
    """Tests for the is_running_in_opencosmos_cluster function."""

    def test_returns_false_when_env_not_set(self, monkeypatch):
        """Should return False when OPENCOSMOS_INTERNAL_CLUSTER is not set."""
        monkeypatch.delenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, raising=False)
        assert is_running_in_opencosmos_cluster() is False

    def test_returns_true_when_env_is_true(self, monkeypatch):
        """Should return True when OPENCOSMOS_INTERNAL_CLUSTER is 'true'."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")
        assert is_running_in_opencosmos_cluster() is True

    def test_returns_true_when_env_is_1(self, monkeypatch):
        """Should return True when OPENCOSMOS_INTERNAL_CLUSTER is '1'."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "1")
        assert is_running_in_opencosmos_cluster() is True

    def test_returns_true_when_env_is_yes(self, monkeypatch):
        """Should return True when OPENCOSMOS_INTERNAL_CLUSTER is 'yes'."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "yes")
        assert is_running_in_opencosmos_cluster() is True

    def test_returns_true_case_insensitive(self, monkeypatch):
        """Should be case insensitive."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "TRUE")
        assert is_running_in_opencosmos_cluster() is True

    def test_returns_false_for_empty_string(self, monkeypatch):
        """Should return False when OPENCOSMOS_INTERNAL_CLUSTER is empty string."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "")
        assert is_running_in_opencosmos_cluster() is False

    def test_returns_false_for_other_values(self, monkeypatch):
        """Should return False for values other than true/1/yes."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "false")
        assert is_running_in_opencosmos_cluster() is False

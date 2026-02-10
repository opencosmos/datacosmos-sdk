"""Tests for the is_running_in_kubernetes function."""

from datacosmos.config.constants import KUBERNETES_SERVICE_HOST_ENV
from datacosmos.config.environment import is_running_in_kubernetes


class TestKubernetesDetection:
    """Tests for the is_running_in_kubernetes function."""

    def test_returns_false_when_env_not_set(self, monkeypatch):
        """Should return False when KUBERNETES_SERVICE_HOST is not set."""
        monkeypatch.delenv(KUBERNETES_SERVICE_HOST_ENV, raising=False)
        assert is_running_in_kubernetes() is False

    def test_returns_true_when_env_is_set(self, monkeypatch):
        """Should return True when KUBERNETES_SERVICE_HOST is set."""
        monkeypatch.setenv(KUBERNETES_SERVICE_HOST_ENV, "10.0.0.1")
        assert is_running_in_kubernetes() is True

    def test_returns_true_for_empty_string(self, monkeypatch):
        """Should return True even if KUBERNETES_SERVICE_HOST is empty string.

        Kubernetes always sets this to a non-empty IP, but we check presence only.
        """
        monkeypatch.setenv(KUBERNETES_SERVICE_HOST_ENV, "")
        assert is_running_in_kubernetes() is True

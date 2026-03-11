"""Tests for the dynamic URL default functions."""

from datacosmos.config.constants import (
    DEFAULT_STAC_EXTERNAL,
    DEFAULT_STAC_INTERNAL,
    DEFAULT_STORAGE_EXTERNAL,
    DEFAULT_STORAGE_INTERNAL,
    OPENCOSMOS_INTERNAL_CLUSTER_ENV,
)
from datacosmos.config.environment import get_default_stac, get_default_storage


class TestGetDefaultUrls:
    """Tests for the dynamic URL default functions."""

    def test_get_default_stac_returns_external_outside_oc_cluster(self, monkeypatch):
        """Should return external STAC URL when not in Open Cosmos cluster."""
        monkeypatch.delenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, raising=False)
        result = get_default_stac()
        assert result == DEFAULT_STAC_EXTERNAL

    def test_get_default_stac_returns_internal_inside_oc_cluster(self, monkeypatch):
        """Should return internal STAC URL when in Open Cosmos cluster."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")
        result = get_default_stac()
        assert result == DEFAULT_STAC_INTERNAL

    def test_get_default_storage_returns_external_outside_oc_cluster(self, monkeypatch):
        """Should return external storage URL when not in Open Cosmos cluster."""
        monkeypatch.delenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, raising=False)
        result = get_default_storage()
        assert result == DEFAULT_STORAGE_EXTERNAL

    def test_get_default_storage_returns_internal_inside_oc_cluster(self, monkeypatch):
        """Should return internal storage URL when in Open Cosmos cluster."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")
        result = get_default_storage()
        assert result == DEFAULT_STORAGE_INTERNAL

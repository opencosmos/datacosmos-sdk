"""Tests for Config class with Open Cosmos cluster auto-detection."""

import os

import pytest

from datacosmos.config.config import Config
from datacosmos.config.constants import OPENCOSMOS_INTERNAL_CLUSTER_ENV


class TestConfigWithOpenCosmosClusterDetection:
    """Tests for Config class with Open Cosmos cluster auto-detection."""

    @pytest.fixture(autouse=True)
    def clean_environment(self, monkeypatch):
        """Clean environment before each test."""
        monkeypatch.delenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, raising=False)
        for k in list(os.environ):
            if k.startswith(("AUTHENTICATION__", "STAC__", "DATACOSMOS_", "OPENCOSMOS_")):
                monkeypatch.delenv(k, raising=False)

    def test_config_uses_external_urls_outside_oc_cluster(self, tmp_path, monkeypatch):
        """Config should use external URLs when not running in Open Cosmos cluster."""
        monkeypatch.delenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, raising=False)

        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
              client_id: test-client
              client_secret: test-secret
            """
        )
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(yaml_file),
            raising=True,
        )

        cfg = Config()

        assert cfg.stac.protocol == "https"
        assert cfg.stac.host == "app.open-cosmos.com"
        assert cfg.stac.port == 443
        assert cfg.stac.path == "/api/data/v0/stac"

        assert cfg.datacosmos_cloud_storage.protocol == "https"
        assert cfg.datacosmos_cloud_storage.host == "app.open-cosmos.com"

        assert cfg.datacosmos_public_cloud_storage.protocol == "https"
        assert cfg.datacosmos_public_cloud_storage.host == "app.open-cosmos.com"

    def test_config_uses_internal_urls_inside_oc_cluster(self, tmp_path, monkeypatch):
        """Config should use internal URLs when running in Open Cosmos cluster."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")

        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
              client_id: test-client
              client_secret: test-secret
            """
        )
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(yaml_file),
            raising=True,
        )

        cfg = Config()

        assert cfg.stac.protocol == "http"
        assert cfg.stac.host == "catalog.default.svc.cluster.local"
        assert cfg.stac.port == 80
        assert cfg.stac.path == "/"

        assert cfg.datacosmos_cloud_storage.protocol == "http"
        assert cfg.datacosmos_cloud_storage.host == "storage.default.svc.cluster.local"

        # Public cloud storage should always use external URLs (for public asset hrefs)
        assert cfg.datacosmos_public_cloud_storage.protocol == "https"
        assert cfg.datacosmos_public_cloud_storage.host == "app.open-cosmos.com"

    def test_explicit_config_overrides_oc_cluster_detection(self, tmp_path, monkeypatch):
        """Explicit YAML config should override auto-detected URLs."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")

        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
              client_id: test-client
              client_secret: test-secret
            stac:
              protocol: https
              host: custom.stac.host
              port: 8443
              path: /custom/stac
            """
        )
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(yaml_file),
            raising=True,
        )

        cfg = Config()

        # Explicit config should override the OC cluster defaults
        assert cfg.stac.protocol == "https"
        assert cfg.stac.host == "custom.stac.host"
        assert cfg.stac.port == 8443
        assert cfg.stac.path == "/custom/stac"

    def test_env_vars_override_oc_cluster_detection(self, tmp_path, monkeypatch):
        """Environment variables should override auto-detected URLs."""
        monkeypatch.setenv(OPENCOSMOS_INTERNAL_CLUSTER_ENV, "true")
        monkeypatch.setenv("STAC__PROTOCOL", "https")
        monkeypatch.setenv("STAC__HOST", "env-override.host")
        monkeypatch.setenv("STAC__PORT", "9443")
        monkeypatch.setenv("STAC__PATH", "/env/path")

        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
              client_id: test-client
              client_secret: test-secret
            """
        )
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(yaml_file),
            raising=True,
        )

        cfg = Config()

        # Env vars should override the OC cluster defaults
        assert cfg.stac.protocol == "https"
        assert cfg.stac.host == "env-override.host"
        assert cfg.stac.port == 9443
        assert cfg.stac.path == "/env/path"

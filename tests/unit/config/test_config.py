import os

import pytest

from datacosmos.config.config import Config
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.url import URL
from datacosmos.exceptions import AuthenticationError

ALL_CONFIG_ENV_PREFIXES = [
    "AUTHENTICATION__",
    "STAC__",
    "DATACOSMOS_DATACOSMOS_CLOUD_STORAGE__",
    "DATACOSMOS_DATACOSMOS_PUBLIC_CLOUD_STORAGE__",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Fixture to ensure a clean environment for every test by deleting known config ENVs."""
    for k in list(os.environ):
        for prefix in ALL_CONFIG_ENV_PREFIXES:
            if k.startswith(prefix):
                monkeypatch.delenv(k, raising=False)


class TestConfig:
    def test_yaml_loads_defaults_for_m2m(self, tmp_path, monkeypatch):
        # Prepare a temp YAML file with only the required m2m fields
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
              client_id: test-client
              client_secret: test-secret
            """
        )
        # Point Config's YAML source to our temp file
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(yaml_file),
            raising=True,
        )

        cfg = Config()

        # Authentication required fields present & type inferred as m2m
        assert isinstance(cfg.authentication, M2MAuthenticationConfig)
        assert cfg.authentication.client_id == "test-client"
        assert cfg.authentication.client_secret == "test-secret"

        # Defaults applied for missing fields
        assert cfg.authentication.token_url
        assert cfg.authentication.audience
        assert cfg.authentication.type == "m2m"

        assert isinstance(cfg.stac, URL)
        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/stac",
        )

    def test_yaml_missing_file_raises_validation_error(self, tmp_path, monkeypatch):
        """Test that missing required fields (no file/no env) raises AuthenticationError."""
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(tmp_path / "does_not_exist.yaml"),
            raising=True,
        )

        with pytest.raises(AuthenticationError):
            Config()

    def test_env_m2m(self, monkeypatch, tmp_path):
        """Test reading nested Pydantic Settings ENVs for both Authentication and STAC."""
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(tmp_path / "does_not_exist.yaml"),
            raising=True,
        )

        monkeypatch.setenv("AUTHENTICATION__TYPE", "m2m")
        monkeypatch.setenv("AUTHENTICATION__CLIENT_ID", "nested-env-client")
        monkeypatch.setenv("AUTHENTICATION__CLIENT_SECRET", "nested-env-secret")
        monkeypatch.setenv("AUTHENTICATION__TOKEN_URL", "https://nested.token.url")
        monkeypatch.setenv("AUTHENTICATION__AUDIENCE", "https://nested.audience")

        monkeypatch.setenv("STAC__PROTOCOL", "http")
        monkeypatch.setenv("STAC__HOST", "env-stac-host")
        monkeypatch.setenv("STAC__PORT", "8080")
        monkeypatch.setenv("STAC__PATH", "/env/stac")

        cfg = Config()

        assert isinstance(cfg.authentication, M2MAuthenticationConfig)
        assert cfg.authentication.client_id == "nested-env-client"
        assert cfg.authentication.client_secret == "nested-env-secret"
        assert cfg.authentication.token_url == "https://nested.token.url"
        assert cfg.authentication.audience == "https://nested.audience"

        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "http",
            "env-stac-host",
            8080,
            "/env/stac",
        )

    def test_invalid_authentication_raises_validation_error(
        self, monkeypatch, tmp_path
    ):
        """Test that missing client_secret raises AuthenticationError."""
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(tmp_path / "does_not_exist.yaml"),
            raising=True,
        )

        with pytest.raises(AuthenticationError):
            Config(authentication={"client_id": "some-client"})

    def test_auth_defaults_applied_when_only_required_m2m(self):
        """Test that non-credential M2M fields are defaulted when only ID/Secret are provided."""
        cfg = Config(
            authentication={"type": "m2m", "client_id": "id", "client_secret": "secret"}
        )

        assert isinstance(cfg.authentication, M2MAuthenticationConfig)
        assert cfg.authentication.type == "m2m"
        assert cfg.authentication.token_url
        assert cfg.authentication.audience
        assert cfg.authentication.client_id == "id"
        assert cfg.authentication.client_secret == "secret"

    def test_stac_defaults_applied_when_missing(self):
        """Test STAC falls back to its own defaults when config is minimal."""
        cfg = Config(authentication={"client_id": "id", "client_secret": "secret"})
        assert isinstance(cfg.stac, URL)
        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/stac",
        )

    def test_cloud_storage_defaults_applied_when_missing(self):
        """Test datacosmos_cloud_storage falls back to its own defaults."""
        cfg = Config(authentication={"client_id": "id", "client_secret": "secret"})
        s = cfg.datacosmos_cloud_storage
        assert isinstance(s, URL)
        assert (s.protocol, s.host, s.port, s.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/storage",
        )

    def test_public_cloud_storage_defaults_applied_when_missing(self):
        """Test datacosmos_public_cloud_storage falls back to its own defaults."""
        cfg = Config(authentication={"client_id": "id", "client_secret": "secret"})
        s = cfg.datacosmos_public_cloud_storage
        assert isinstance(s, URL)
        assert (s.protocol, s.host, s.port, s.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/storage",
        )

    def test_local_auth_defaults_applied(self):
        """Test local authentication fields are correctly defaulted by the factory."""
        cfg = Config(authentication={"type": "local", "client_id": "abc"})
        assert isinstance(cfg.authentication, LocalUserAccountAuthenticationConfig)
        a = cfg.authentication
        assert a.type == "local"
        assert a.client_id == "abc"
        assert isinstance(a.redirect_port, int) and a.redirect_port > 0
        assert a.authorization_endpoint
        assert a.token_endpoint
        assert a.scopes
        assert a.audience
        assert a.cache_file

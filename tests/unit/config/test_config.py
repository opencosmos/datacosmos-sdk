import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.url import URL
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)


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
        # (token_url, audience, type are set in the auth factory defaults)
        assert cfg.authentication.token_url
        assert cfg.authentication.audience
        assert cfg.authentication.type == "m2m"

        # STAC config should be default since missing from YAML
        assert isinstance(cfg.stac, URL)
        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/stac",
        )

    def test_yaml_missing_file_raises_validation_error(self, tmp_path, monkeypatch):
        # Point YAML to a NON-existent file and ensure no env vars are set
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(tmp_path / "does_not_exist.yaml"),
            raising=True,
        )
        # Clear any auth env that could make it pass
        for k in list(os.environ):
            if k.startswith("OC_AUTH_"):
                monkeypatch.delenv(k, raising=False)

        # With no YAML and no env, authentication validator should fail
        with pytest.raises(ValidationError):
            Config()

    def test_env_m2m(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
        "datacosmos.config.config.DEFAULT_CONFIG_YAML",
        str(tmp_path / "does_not_exist.yaml"),
        raising=True,
        )

        monkeypatch.setenv("AUTHENTICATION__TYPE", "m2m")
        monkeypatch.setenv("AUTHENTICATION__CLIENT_ID", "env-client")
        monkeypatch.setenv("AUTHENTICATION__CLIENT_SECRET", "env-secret")
        monkeypatch.setenv("AUTHENTICATION__TOKEN_URL", "https://env.token.url")
        monkeypatch.setenv("AUTHENTICATION__AUDIENCE", "https://env.audience")

        monkeypatch.setenv("STAC__PROTOCOL", "http")
        monkeypatch.setenv("STAC__HOST", "env-stac-host")
        monkeypatch.setenv("STAC__PORT", "8080")
        monkeypatch.setenv("STAC__PATH", "/env/stac")

        monkeypatch.delenv("OC_AUTH_TYPE", raising=False)

        cfg = Config()

        from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
        assert isinstance(cfg.authentication, M2MAuthenticationConfig)
        assert cfg.authentication.client_id == "env-client"
        assert cfg.authentication.client_secret == "env-secret"
        assert cfg.authentication.token_url == "https://env.token.url"
        assert cfg.authentication.audience == "https://env.audience"
        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "http", "env-stac-host", 8080, "/env/stac"
        )

    def test_invalid_authentication_raises_validation_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "datacosmos.config.config.DEFAULT_CONFIG_YAML",
            str(tmp_path / "does_not_exist.yaml"),
            raising=True,
        )

        for k in list(os.environ):
            if k.startswith(("OC_", "AUTHENTICATION__", "STAC__")):
                monkeypatch.delenv(k, raising=False)

        with pytest.raises(ValidationError):
            Config(authentication={"client_id": "some-client"})

    def test_auth_defaults_applied_when_only_required_m2m(self):
        # Provide just the required m2m creds; the rest should be defaulted
        cfg = Config(authentication={"type": "m2m", "client_id": "id", "client_secret": "secret"})

        assert isinstance(cfg.authentication, M2MAuthenticationConfig)
        assert cfg.authentication.type == "m2m"
        assert cfg.authentication.token_url
        assert cfg.authentication.audience
        assert cfg.authentication.client_id == "id"
        assert cfg.authentication.client_secret == "secret"

    def test_stac_defaults_applied_when_missing(self):
        # Pass valid auth to prevent validation error; omit stac -> defaults applied
        cfg = Config(authentication={"client_id": "id", "client_secret": "secret"})
        assert isinstance(cfg.stac, URL)
        assert (cfg.stac.protocol, cfg.stac.host, cfg.stac.port, cfg.stac.path) == (
            "https",
            "app.open-cosmos.com",
            443,
            "/api/data/v0/stac",
        )

    def test_cloud_storage_defaults_applied_when_missing(self):
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
        # Minimal local auth (client_id only) should pick up defaults from the auth factory
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

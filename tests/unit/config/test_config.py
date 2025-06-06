import pytest

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.url import URL


class TestConfig:
    def test_from_yaml_loads_defaults(self, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
            authentication:
                client_id: test-client
                client_secret: test-secret
            """
        )

        config = Config.from_yaml(str(yaml_file))

        # Authentication required fields present
        assert isinstance(config.authentication, M2MAuthenticationConfig)
        assert config.authentication.client_id == "test-client"
        assert config.authentication.client_secret == "test-secret"

        # Defaults applied for missing fields
        assert config.authentication.token_url == Config.DEFAULT_AUTH_TOKEN_URL
        assert config.authentication.audience == Config.DEFAULT_AUTH_AUDIENCE
        assert config.authentication.type == Config.DEFAULT_AUTH_TYPE

        # STAC config should be default since missing from YAML
        assert isinstance(config.stac, URL)
        assert config.stac.protocol == "https"
        assert config.stac.host == "app.open-cosmos.com"
        assert config.stac.port == 443
        assert config.stac.path == "/api/data/v0/stac"

        assert config.mission_id == 0

    def test_from_yaml_ignores_missing_file(self):
        # If file doesn't exist, returns default config with required fields missing, so should raise error
        with pytest.raises(ValueError):
            Config.from_yaml("nonexistent.yaml")

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OC_AUTH_CLIENT_ID", "env-client")
        monkeypatch.setenv("OC_AUTH_CLIENT_SECRET", "env-secret")
        monkeypatch.setenv("OC_AUTH_TOKEN_URL", "https://env.token.url")
        monkeypatch.setenv("OC_AUTH_AUDIENCE", "https://env.audience")
        monkeypatch.setenv("OC_STAC_PROTOCOL", "http")
        monkeypatch.setenv("OC_STAC_HOST", "env-stac-host")
        monkeypatch.setenv("OC_STAC_PORT", "8080")
        monkeypatch.setenv("OC_STAC_PATH", "/env/stac")
        monkeypatch.setenv("MISSION_ID", "99")

        config = Config.from_env()

        assert config.authentication.client_id == "env-client"
        assert config.authentication.client_secret == "env-secret"
        assert config.authentication.token_url == "https://env.token.url"
        assert config.authentication.audience == "https://env.audience"

        assert config.stac.protocol == "http"
        assert config.stac.host == "env-stac-host"
        assert config.stac.port == 8080
        assert config.stac.path == "/env/stac"

        assert config.mission_id == 99

    def test_validate_authentication_applies_defaults_and_raises_value_error(self):
        # Missing client_id and client_secret should raise
        with pytest.raises(ValueError):
            Config.validate_authentication(M2MAuthenticationConfig())

        # Partial input applies defaults
        auth_input = M2MAuthenticationConfig(client_id="id", client_secret="secret")
        auth = Config.validate_authentication(auth_input)

        assert auth.type == Config.DEFAULT_AUTH_TYPE
        assert auth.token_url == Config.DEFAULT_AUTH_TOKEN_URL
        assert auth.audience == Config.DEFAULT_AUTH_AUDIENCE
        assert auth.client_id == "id"
        assert auth.client_secret == "secret"

    def test_invalid_authentication_raises_validation_error(self):
        # Missing client_secret should raise ValueError from the validator
        with pytest.raises(ValueError):
            Config(authentication={"client_id": "some-client"})

    def test_stac_defaults_applied_when_none(self):
        stac = Config.validate_stac(None)
        assert stac.protocol == "https"
        assert stac.host == "app.open-cosmos.com"
        assert stac.port == 443
        assert stac.path == "/api/data/v0/stac"

    def test_datacosmos_cloud_storage_defaults_applied_when_none(self):
        storage = Config.validate_datacosmos_cloud_storage(None)
        assert storage.protocol == "https"
        assert storage.host == "app.open-cosmos.com"
        assert storage.port == 443
        assert storage.path == "/api/data/v0/storage"

    def test_apply_auth_defaults(self):
        auth = M2MAuthenticationConfig(client_id="cid", client_secret="csecret")
        updated_auth = Config.apply_auth_defaults(auth)
        assert updated_auth.type == Config.DEFAULT_AUTH_TYPE
        assert updated_auth.token_url == Config.DEFAULT_AUTH_TOKEN_URL
        assert updated_auth.audience == Config.DEFAULT_AUTH_AUDIENCE

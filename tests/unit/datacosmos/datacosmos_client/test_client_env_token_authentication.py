"""Tests for environment-token authentication (AUTHENTICATION__TYPE=token)."""

from unittest.mock import patch

import pytest

from datacosmos.config.config import Config
from datacosmos.config.models.token_authentication_config import (
    TokenAuthenticationConfig,
)
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions import AuthenticationError


def _token_config() -> Config:
    return Config(authentication=TokenAuthenticationConfig(type="token"))


class TestClientEnvTokenAuthentication:
    """Test suite for the `token` authentication type reading the env var."""

    def test_reads_token_from_env_and_sets_bearer_header(self, monkeypatch):
        """A token-type config builds a bearer session from the env var."""
        monkeypatch.setenv("DATACOSMOS_USER_TOKEN", "env-token")
        client = DatacosmosClient(config=_token_config())

        assert client.token == "env-token"
        assert client._owns_session is False
        assert client.token_expiry is None
        assert client._http_client.headers["Authorization"] == "Bearer env-token"

    def test_skips_authentication_flow(self, monkeypatch):
        """Token type must not invoke the m2m/local authentication flow."""
        monkeypatch.setenv("DATACOSMOS_USER_TOKEN", "env-token")
        with patch.object(
            DatacosmosClient,
            "_authenticate_and_initialize_client",
            side_effect=AssertionError("should not authenticate for token type"),
        ):
            DatacosmosClient(config=_token_config())

    def test_missing_env_var_raises(self, monkeypatch):
        """An unset token env var yields a clear AuthenticationError."""
        monkeypatch.delenv("DATACOSMOS_USER_TOKEN", raising=False)
        with pytest.raises(AuthenticationError, match="DATACOSMOS_USER_TOKEN"):
            DatacosmosClient(config=_token_config())

    def test_custom_env_var_name(self, monkeypatch):
        """A custom token_env_var is honoured."""
        monkeypatch.delenv("DATACOSMOS_USER_TOKEN", raising=False)
        monkeypatch.setenv("MY_TOKEN", "custom-token")
        config = Config(
            authentication=TokenAuthenticationConfig(
                type="token", token_env_var="MY_TOKEN"
            )
        )
        client = DatacosmosClient(config=config)
        assert client.token == "custom-token"

    def test_preserves_endpoint_config(self, monkeypatch):
        """Token init keeps the coerced config's endpoint settings.

        All four URL fields must be set together — the SDK builds each service
        URL from a nested model whose fields are all required.
        """
        monkeypatch.setenv("DATACOSMOS_USER_TOKEN", "env-token")
        monkeypatch.setenv("STAC__PROTOCOL", "https")
        monkeypatch.setenv("STAC__HOST", "test.app.open-cosmos.com")
        monkeypatch.setenv("STAC__PORT", "443")
        monkeypatch.setenv("STAC__PATH", "/api/data/v0/stac")
        client = DatacosmosClient(config=_token_config())
        assert client.config.stac.host == "test.app.open-cosmos.com"

    def test_does_not_refresh(self, monkeypatch):
        """A pre-obtained token must never be treated as refreshable."""
        monkeypatch.setenv("DATACOSMOS_USER_TOKEN", "env-token")
        client = DatacosmosClient(config=_token_config())
        assert client._needs_refresh() is False

    def test_type_from_env_var(self, monkeypatch):
        """AUTHENTICATION__TYPE=token selects token auth end-to-end."""
        monkeypatch.setenv("AUTHENTICATION__TYPE", "token")
        monkeypatch.setenv("DATACOSMOS_USER_TOKEN", "env-token")
        client = DatacosmosClient()
        assert client.token == "env-token"
        assert client._http_client.headers["Authorization"] == "Bearer env-token"

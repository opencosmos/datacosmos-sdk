# tests/unit/config/test_auth_factory.py

import pytest

from datacosmos.config.auth.factory import (
    apply_auth_defaults,
    check_required_auth_fields,
    normalize_authentication,
    parse_auth_config,
)
from datacosmos.config.constants import (
    DEFAULT_AUTH_AUDIENCE,
    DEFAULT_AUTH_TOKEN_URL,
    DEFAULT_AUTH_TYPE,
    DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT,
    DEFAULT_LOCAL_CACHE_FILE,
    DEFAULT_LOCAL_REDIRECT_PORT,
    DEFAULT_LOCAL_SCOPES,
    DEFAULT_LOCAL_TOKEN_ENDPOINT,
)
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig


class TestFactory:
    # ---------------- parse_auth_config ----------------

    def test_parse_auth_config_none(self):
        assert parse_auth_config(None) is None

    def test_parse_auth_config_m2m_dict(self):
        raw = {
            "client_id": "cid",
            "client_secret": "secret",
            # omit token_url / audience to ensure defaults are applied in parse
        }
        auth = parse_auth_config(raw)
        assert isinstance(auth, M2MAuthenticationConfig)
        assert auth.client_id == "cid"
        assert auth.client_secret == "secret"
        assert auth.type == DEFAULT_AUTH_TYPE  # "m2m"
        assert auth.token_url == DEFAULT_AUTH_TOKEN_URL
        assert auth.audience == DEFAULT_AUTH_AUDIENCE

    def test_parse_auth_config_local_dict(self):
        raw = {
            "type": "local",
            "client_id": "cid",
            # omit everything else to ensure defaults are applied in parse
        }
        auth = parse_auth_config(raw)
        assert isinstance(auth, LocalUserAccountAuthenticationConfig)
        assert auth.type == "local"
        assert auth.client_id == "cid"
        assert auth.authorization_endpoint == DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT
        assert auth.token_endpoint == DEFAULT_LOCAL_TOKEN_ENDPOINT
        assert auth.redirect_port == DEFAULT_LOCAL_REDIRECT_PORT
        assert auth.scopes == DEFAULT_LOCAL_SCOPES
        assert auth.audience == DEFAULT_AUTH_AUDIENCE
        assert auth.cache_file == DEFAULT_LOCAL_CACHE_FILE

    def test_parse_auth_config_passthrough_instance(self):
        m2m = M2MAuthenticationConfig(
            type="m2m",
            client_id="x",
            client_secret="y",
            token_url=DEFAULT_AUTH_TOKEN_URL,
            audience=DEFAULT_AUTH_AUDIENCE,
        )
        local = LocalUserAccountAuthenticationConfig(
            type="local",
            client_id="x",
            authorization_endpoint=DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT,
            token_endpoint=DEFAULT_LOCAL_TOKEN_ENDPOINT,
            redirect_port=DEFAULT_LOCAL_REDIRECT_PORT,
            scopes=DEFAULT_LOCAL_SCOPES,
            audience=DEFAULT_AUTH_AUDIENCE,
            cache_file=DEFAULT_LOCAL_CACHE_FILE,
        )
        assert parse_auth_config(m2m) is m2m
        assert parse_auth_config(local) is local

    # ---------------- apply_auth_defaults ----------------

    def test_apply_auth_defaults_when_none_uses_default_type(self):
        # DEFAULT_AUTH_TYPE is "m2m" in your constants, so we expect an M2M shell
        auth = apply_auth_defaults(None)
        assert isinstance(auth, M2MAuthenticationConfig)
        assert auth.type == "m2m"
        assert auth.token_url == DEFAULT_AUTH_TOKEN_URL
        assert auth.audience == DEFAULT_AUTH_AUDIENCE
        # these are intentionally None (filled later by user/env)
        assert getattr(auth, "client_id") is None
        assert getattr(auth, "client_secret") is None

    def test_apply_auth_defaults_m2m_fills_missing_fields(self):
        # missing token_url/audience should be defaulted
        partial = M2MAuthenticationConfig(
            type="m2m", client_id="cid", client_secret="sec"
        )
        filled = apply_auth_defaults(partial)
        assert filled.type == "m2m"
        assert filled.client_id == "cid"
        assert filled.client_secret == "sec"
        assert filled.token_url == DEFAULT_AUTH_TOKEN_URL
        assert filled.audience == DEFAULT_AUTH_AUDIENCE

    def test_apply_auth_defaults_local_fills_missing_fields(self):
        partial = LocalUserAccountAuthenticationConfig(type="local", client_id="cid")
        filled = apply_auth_defaults(partial)
        assert filled.type == "local"
        assert filled.client_id == "cid"
        assert filled.authorization_endpoint == DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT
        assert filled.token_endpoint == DEFAULT_LOCAL_TOKEN_ENDPOINT
        assert filled.redirect_port == DEFAULT_LOCAL_REDIRECT_PORT
        assert filled.scopes == DEFAULT_LOCAL_SCOPES
        assert filled.audience == DEFAULT_AUTH_AUDIENCE
        assert filled.cache_file == DEFAULT_LOCAL_CACHE_FILE

    # ---------------- check_required_auth_fields ----------------

    def test_check_required_auth_fields_m2m_missing_raises(self):
        with pytest.raises(
            ValueError, match="Missing required authentication fields for m2m"
        ):
            check_required_auth_fields(M2MAuthenticationConfig(type="m2m"))

        with pytest.raises(
            ValueError, match="Missing required authentication fields for m2m"
        ):
            check_required_auth_fields(
                M2MAuthenticationConfig(type="m2m", client_id="cid")
            )

    def test_check_required_auth_fields_local_missing_raises(self):
        with pytest.raises(
            ValueError,
            match="Missing required authentication field for local: client_id",
        ):
            check_required_auth_fields(
                LocalUserAccountAuthenticationConfig(type="local")
            )

    def test_check_required_auth_fields_valid(self):
        # m2m ok
        check_required_auth_fields(
            M2MAuthenticationConfig(
                type="m2m",
                client_id="cid",
                client_secret="sec",
                token_url=DEFAULT_AUTH_TOKEN_URL,
                audience=DEFAULT_AUTH_AUDIENCE,
            )
        )
        # local ok
        check_required_auth_fields(
            LocalUserAccountAuthenticationConfig(
                type="local",
                client_id="cid",
                authorization_endpoint=DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT,
                token_endpoint=DEFAULT_LOCAL_TOKEN_ENDPOINT,
                redirect_port=DEFAULT_LOCAL_REDIRECT_PORT,
                scopes=DEFAULT_LOCAL_SCOPES,
                audience=DEFAULT_AUTH_AUDIENCE,
                cache_file=DEFAULT_LOCAL_CACHE_FILE,
            )
        )

    # ---------------- normalize_authentication (end-to-end) ----------------

    def test_normalize_authentication_m2m_minimal_dict(self):
        raw = {"client_id": "cid", "client_secret": "sec"}
        auth = normalize_authentication(raw)
        assert isinstance(auth, M2MAuthenticationConfig)
        assert auth.client_id == "cid"
        assert auth.client_secret == "sec"
        assert auth.token_url == DEFAULT_AUTH_TOKEN_URL
        assert auth.audience == DEFAULT_AUTH_AUDIENCE

    def test_normalize_authentication_local_minimal_dict(self):
        raw = {"type": "local", "client_id": "cid"}
        auth = normalize_authentication(raw)
        assert isinstance(auth, LocalUserAccountAuthenticationConfig)
        assert auth.client_id == "cid"
        assert auth.authorization_endpoint == DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT
        assert auth.token_endpoint == DEFAULT_LOCAL_TOKEN_ENDPOINT
        assert auth.redirect_port == DEFAULT_LOCAL_REDIRECT_PORT
        assert auth.scopes == DEFAULT_LOCAL_SCOPES
        assert auth.audience == DEFAULT_AUTH_AUDIENCE
        assert auth.cache_file == DEFAULT_LOCAL_CACHE_FILE

    def test_normalize_authentication_m2m_missing_secret_raises(self):
        with pytest.raises(
            ValueError, match="Missing required authentication fields for m2m"
        ):
            normalize_authentication({"client_id": "cid"})  # no client_secret

    def test_normalize_authentication_local_missing_client_id_raises(self):
        with pytest.raises(
            ValueError,
            match="Missing required authentication field for local: client_id",
        ):
            normalize_authentication({"type": "local"})  # no client_id

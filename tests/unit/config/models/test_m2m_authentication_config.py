from datacosmos.config.auth.factory import apply_auth_defaults
from datacosmos.config.constants import DEFAULT_AUTH_AUDIENCE, DEFAULT_AUTH_TOKEN_URL
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig


class TestM2MAuthenticationConfig:
    def test_with_minimal_input(self):
        """Defaults are filled by the factory when only client_id/secret are provided."""
        partial = M2MAuthenticationConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        config = apply_auth_defaults(partial)  # <-- fills token_url & audience

        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.type == "m2m"
        assert config.token_url == DEFAULT_AUTH_TOKEN_URL
        assert config.audience == DEFAULT_AUTH_AUDIENCE

    def test_with_full_input(self):
        """Test full config input overrides defaults correctly."""
        config = M2MAuthenticationConfig(
            type="m2m",
            client_id="custom-client-id",
            client_secret="custom-client-secret",
            token_url="https://custom.token.url",
            audience="https://custom.audience",
        )

        assert config.type == "m2m"
        assert config.client_id == "custom-client-id"
        assert config.client_secret == "custom-client-secret"
        assert config.token_url == "https://custom.token.url"
        assert config.audience == "https://custom.audience"

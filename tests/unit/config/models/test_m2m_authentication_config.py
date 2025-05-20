
from config.models.m2m_authentication_config import M2MAuthenticationConfig


class TestM2MAuthenticationConfig:
    def test_with_minimal_input(self):
        """Test default values are set when only client_id and client_secret are provided."""
        config = M2MAuthenticationConfig(
            client_id="test-client-id", client_secret="test-client-secret"
        )

        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.type == "m2m"
        assert config.token_url == "https://login.open-cosmos.com/oauth/token"
        assert config.audience == "https://beeapp.open-cosmos.com"

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

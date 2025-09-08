from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient


@patch(
    "datacosmos.datacosmos_client.DatacosmosClient._DatacosmosClient__build_m2m_session",
    autospec=True,
)
@patch(
    "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
)
def test_client_token_refreshing(mock_init_auth, mock_build_m2m):
    """Test that the client refreshes the token when it expires."""
    mock_http_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "success"}
    mock_http_client.request.return_value = mock_response

    mock_init_auth.return_value = mock_http_client

    def fake_build(self):
        self.token = "NEW_TOKEN"
        self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        return mock_http_client

    mock_build_m2m.side_effect = fake_build

    config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://example.invalid/oauth/token",
            audience="https://mock.audience",
        )
    )

    client = DatacosmosClient(config=config)

    client.token = "OLD_TOKEN"
    client.token_expiry = datetime.now(timezone.utc) - timedelta(seconds=1)

    response = client.get("https://mock.api/some-endpoint")

    assert response.status_code == 200
    assert response.json() == {"message": "success"}

    assert mock_init_auth.call_count == 1
    assert mock_build_m2m.call_count == 1

    mock_http_client.request.assert_called_once_with(
        "GET", "https://mock.api/some-endpoint"
    )

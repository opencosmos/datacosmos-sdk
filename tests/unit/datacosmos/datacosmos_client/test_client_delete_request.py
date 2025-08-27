from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient


@patch(
    "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
)
def test_delete_request(mock_auth_client):
    mock_http_client = MagicMock()
    mock_resp = MagicMock(status_code=204)
    mock_http_client.request.return_value = mock_resp
    mock_auth_client.return_value = mock_http_client

    cfg = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="id",
            client_secret="secret",
            token_url="https://example.invalid/oauth/token",
            audience="https://mock.audience",
        )
    )

    client = DatacosmosClient(config=cfg)

    client.token = "TEST_TOKEN"
    client.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    resp = client.delete("https://mock.api/some-endpoint")
    assert resp.status_code == 204
    mock_http_client.request.assert_called_once_with(
        "DELETE", "https://mock.api/some-endpoint"
    )
    assert mock_auth_client.call_count == 1

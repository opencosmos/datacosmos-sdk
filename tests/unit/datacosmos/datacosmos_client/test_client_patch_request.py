from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient


@patch(
    "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
)
def test_patch_request(mock_auth_client):
    """Test that the client performs a PATCH request correctly."""
    # Mock the HTTP client
    mock_http_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "updated"}
    mock_http_client.request.return_value = mock_response
    mock_auth_client.return_value = mock_http_client

    config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://mock.token.url/oauth/token",
            audience="https://mock.audience",
        )
    )

    client = DatacosmosClient(config=config)
    response = client.patch(
        "https://mock.api/some-endpoint", json={"key": "updated-value"}
    )

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "updated"}
    mock_http_client.request.assert_called_once_with(
        "PATCH", "https://mock.api/some-endpoint", json={"key": "updated-value"}
    )
    mock_auth_client.call_count == 2

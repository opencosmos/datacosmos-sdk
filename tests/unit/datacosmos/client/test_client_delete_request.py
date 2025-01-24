from unittest.mock import MagicMock, patch

from config.config import Config
from datacosmos.client import DatacosmosClient


@patch(
    "datacosmos.client.DatacosmosClient._authenticate_and_initialize_client"
)
def test_delete_request(mock_auth_client):
    """
    Test that the client performs a DELETE request correctly.
    """
    # Mock the HTTP client
    mock_http_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_http_client.request.return_value = mock_response
    mock_auth_client.return_value = mock_http_client

    config = Config(
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://mock.token.url/oauth/token",
        audience="https://mock.audience",
    )
    client = DatacosmosClient(config=config)
    response = client.delete("https://mock.api/some-endpoint")

    # Assertions
    assert response.status_code == 204
    mock_http_client.request.assert_called_once_with(
        "DELETE", "https://mock.api/some-endpoint"
    )
    mock_auth_client.call_count == 2

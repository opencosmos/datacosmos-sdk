from unittest.mock import MagicMock, patch

from config.config import Config
from datacosmos.client import DatacosmosClient


@patch(
    "datacosmos.client.DatacosmosClient._authenticate_and_initialize_client"
)
def test_client_get_request(mock_auth_client):
    """
    Test that the client performs a GET request correctly.
    """
    # Mock the HTTP client
    mock_http_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "success"}
    mock_http_client.request.return_value = mock_response
    mock_auth_client.return_value = mock_http_client

    config = Config(
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://mock.token.url/oauth/token",
        audience="https://mock.audience",
    )
    client = DatacosmosClient(config=config)
    response = client.get("https://mock.api/some-endpoint")

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    mock_http_client.request.assert_called_once_with(
        "GET", "https://mock.api/some-endpoint"
    )
    mock_auth_client.call_count == 2

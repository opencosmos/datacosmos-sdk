from unittest.mock import patch, MagicMock
from datacosmos.client import DatacosmosClient
from config.config import Config


@patch("datacosmos.client.DatacosmosClient._authenticate_and_initialize_client")
def test_post_request(mock_auth_client):
    """
    Test that the client performs a POST request correctly.
    """
    # Mock the HTTP client
    mock_http_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"message": "created"}
    mock_http_client.request.return_value = mock_response
    mock_auth_client.return_value = mock_http_client

    config = Config(
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://mock.token.url/oauth/token",
        audience="https://mock.audience",
    )
    client = DatacosmosClient(config=config)
    response = client.post(
        "https://mock.api/some-endpoint", json={"key": "value"}
    )

    # Assertions
    assert response.status_code == 201
    assert response.json() == {"message": "created"}
    mock_http_client.request.assert_called_once_with(
        "POST",
        "https://mock.api/some-endpoint",
        json={"key": "value"}
    )
    mock_auth_client.call_count == 2

"""Tests for token-based authentication in DatacosmosClient."""

from unittest.mock import Mock, patch

import pytest
import requests

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions import AuthenticationError


class TestClientTokenAuthentication:
    """Test suite for DatacosmosClient token-based authentication."""

    def test_token_creates_session_with_bearer_header(self):
        """Test that providing a token creates a session with Bearer auth header."""
        client = DatacosmosClient(token="my-access-token")

        assert client.token == "my-access-token"
        assert client._owns_session is False
        assert client.token_expiry is None
        assert "Authorization" in client._http_client.headers
        assert client._http_client.headers["Authorization"] == "Bearer my-access-token"

    def test_token_skips_authentication_flow(self):
        """Test that providing a token skips the SDK authentication flow."""
        with patch.object(
            DatacosmosClient,
            "_authenticate_and_initialize_client",
            side_effect=AssertionError(
                "Should not authenticate when token is provided"
            ),
        ):
            client = DatacosmosClient(token="my-access-token")

        assert client.token == "my-access-token"

    def test_token_cannot_be_combined_with_config(self):
        """Test that providing both token and config raises AuthenticationError."""
        config = Config(
            authentication=M2MAuthenticationConfig(
                type="m2m",
                client_id="test-client-id",
                client_secret="test-client-secret",
            )
        )

        with pytest.raises(AuthenticationError) as exc_info:
            DatacosmosClient(token="my-access-token", config=config)

        assert "Cannot provide both 'token' and 'config'" in str(exc_info.value)

    def test_token_cannot_be_combined_with_http_session(self):
        """Test that providing both token and http_session raises AuthenticationError."""
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer existing-token"})

        with pytest.raises(AuthenticationError) as exc_info:
            DatacosmosClient(token="my-access-token", http_session=session)

        assert "Cannot provide both 'token' and 'http_session'" in str(exc_info.value)

    def test_token_client_can_make_requests(self):
        """Test that a token-authenticated client can make HTTP requests."""
        client = DatacosmosClient(token="my-access-token")

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        client._http_client.request = Mock(return_value=mock_response)

        result = client.request("GET", "https://api.example.com/data")

        assert result is mock_response
        client._http_client.request.assert_called_once()
        call_kwargs = client._http_client.request.call_args
        assert call_kwargs[0] == ("GET", "https://api.example.com/data")

    def test_token_client_has_default_config_for_urls(self):
        """Test that token client uses default Config for URL endpoints."""
        client = DatacosmosClient(token="my-access-token")

        # Should have a default Config with standard URL endpoints
        assert client.config is not None
        assert client.config.stac.host == "app.open-cosmos.com"

    def test_token_client_with_hooks(self):
        """Test that token client works with request/response hooks."""
        request_hook_called = []
        response_hook_called = []

        def request_hook(method, url, *args, **kwargs):
            request_hook_called.append((method, url))

        def response_hook(response):
            response_hook_called.append(response.status_code)

        client = DatacosmosClient(
            token="my-access-token",
            request_hooks=[request_hook],
            response_hooks=[response_hook],
        )

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        client._http_client.request = Mock(return_value=mock_response)

        client.request("GET", "https://api.example.com/data")

        assert len(request_hook_called) == 1
        assert request_hook_called[0] == ("GET", "https://api.example.com/data")
        assert len(response_hook_called) == 1
        assert response_hook_called[0] == 200

    def test_token_client_does_not_refresh_token(self):
        """Test that token client does not attempt token refresh."""
        client = DatacosmosClient(token="my-access-token")

        # _owns_session is False, so _needs_refresh should return False
        assert client._owns_session is False
        assert client._needs_refresh() is False

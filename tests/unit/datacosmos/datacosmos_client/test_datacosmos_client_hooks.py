import unittest
from unittest.mock import MagicMock, patch

import requests

from datacosmos.config.config import Config
from datacosmos.datacosmos_client import DatacosmosClient


class TestDatacosmosClientHooks(unittest.TestCase):
    """Unit tests for the DatacosmosClient request/response hooks."""

    def setUp(self):
        """Set up a mock config for the client."""
        self.mock_config = Config(
            authentication={
                "type": "m2m",
                "client_id": "test_id",
                "client_secret": "test_secret",
                "token_url": "https://test.url",
                "audience": "https://api.example.com",
            }
        )

    @patch("datacosmos.datacosmos_client.requests.Session")
    @patch("datacosmos.auth.m2m_authenticator.OAuth2Session")
    def test_request_and_response_hooks_are_called(
        self, mock_oauth_session, mock_requests_session
    ):
        """
        Test that both request and response hooks are called exactly once
        during a successful HTTP request, including keyword arguments.
        """
        mock_oauth_session.return_value.fetch_token.return_value = {
            "access_token": "dummy_access_token",
            "expires_at": 9999999999,
        }

        mock_request_hook = MagicMock()
        mock_response_hook = MagicMock()

        client = DatacosmosClient(
            config=self.mock_config,
            request_hooks=[mock_request_hook],
            response_hooks=[mock_response_hook],
        )

        mock_response = MagicMock(spec=requests.Response)
        mock_response.raise_for_status.return_value = None
        mock_requests_session.return_value.request.return_value = mock_response

        test_params = {"foo": "bar"}
        client.get("https://api.example.com/data", params=test_params)

        mock_request_hook.assert_called_once()
        mock_response_hook.assert_called_once()

        mock_request_hook.assert_called_with(
            "GET", "https://api.example.com/data", params=test_params
        )
        mock_response_hook.assert_called_with(mock_response)

    @patch("datacosmos.datacosmos_client.requests.Session")
    @patch("datacosmos.auth.m2m_authenticator.OAuth2Session")
    def test_response_hook_is_not_called_on_http_error(
        self, mock_oauth_session, mock_requests_session
    ):
        """
        Test that the response hook is not called if an HTTP error occurs.
        """
        mock_oauth_session.return_value.fetch_token.return_value = {
            "access_token": "dummy_access_token",
            "expires_at": 9999999999,
        }

        mock_request_hook = MagicMock()
        mock_response_hook = MagicMock()

        client = DatacosmosClient(
            config=self.mock_config,
            request_hooks=[mock_request_hook],
            response_hooks=[mock_response_hook],
        )

        mock_requests_session.return_value.request.side_effect = (
            requests.exceptions.HTTPError()
        )

        with self.assertRaises(Exception):
            client.get("https://api.example.com/data")

        mock_request_hook.assert_called_once()
        mock_response_hook.assert_not_called()

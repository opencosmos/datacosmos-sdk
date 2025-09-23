import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from datacosmos.auth.local_authenticator import LocalAuthenticator
from datacosmos.exceptions.datacosmos_exception import DatacosmosException


class TestLocalAuthenticator(unittest.TestCase):
    """Unit tests for the LocalAuthenticator class."""

    def setUp(self):
        """Set up mock objects and the authenticator instance before each test."""
        # Mock the Config object and its attributes
        self.mock_config = MagicMock()
        self.mock_config.authentication.client_id = "test_client_id"
        self.mock_config.authentication.authorization_endpoint = "http://auth.endpoint"
        self.mock_config.authentication.token_endpoint = "http://token.endpoint"
        self.mock_config.authentication.redirect_port = "8000"
        self.mock_config.authentication.audience = "test_audience"
        self.mock_config.authentication.scopes = ["scope1", "scope2"]
        self.mock_config.authentication.cache_file = "/mock/cache.json"

    @patch("datacosmos.auth.local_authenticator.LocalTokenFetcher")
    @patch("datacosmos.auth.local_authenticator.requests.Session")
    def test_authenticate_and_build_session_success(
        self, mock_session_class, mock_fetcher_class
    ):
        """Test that authentication succeeds and returns a valid AuthResult."""
        mock_fetcher_instance = mock_fetcher_class.return_value
        mock_token_object = MagicMock()
        mock_token_object.access_token = "mock_access_token"
        mock_token_object.expires_at = datetime.now(timezone.utc).timestamp() + 3600
        mock_fetcher_instance.get_token.return_value = mock_token_object

        authenticator = LocalAuthenticator(self.mock_config)
        auth_result = authenticator.authenticate_and_build_session()

        self.assertIs(auth_result.http_client, mock_session_class.return_value)
        self.assertEqual(auth_result.token, "mock_access_token")
        self.assertAlmostEqual(
            auth_result.token_expiry.timestamp(), mock_token_object.expires_at, delta=1
        )
        mock_session_class.return_value.headers.update.assert_called_with(
            {"Authorization": "Bearer mock_access_token"}
        )

    @patch("datacosmos.auth.local_authenticator.LocalTokenFetcher")
    def test_authenticate_and_build_session_failure(self, mock_fetcher_class):
        """Test that authentication fails when LocalTokenFetcher raises an exception."""
        mock_fetcher_instance = mock_fetcher_class.return_value
        mock_fetcher_instance.get_token.side_effect = Exception(
            "Mocked authentication error"
        )

        authenticator = LocalAuthenticator(self.mock_config)
        with self.assertRaises(DatacosmosException) as cm:
            authenticator.authenticate_and_build_session()

        self.assertIn("Local authentication failed", str(cm.exception))

    @patch("datacosmos.auth.local_authenticator.LocalTokenFetcher")
    @patch("datacosmos.auth.local_authenticator.requests.Session")
    def test_refresh_token_success(self, mock_session_class, mock_fetcher_class):
        """Test that token refresh succeeds and returns a valid AuthResult."""
        authenticator = LocalAuthenticator(self.mock_config)
        authenticator.http_client = mock_session_class.return_value

        mock_fetcher_instance = mock_fetcher_class.return_value
        mock_refresh_token = MagicMock()
        mock_refresh_token.access_token = "new_mock_token"
        mock_refresh_token.expires_at = datetime.now(timezone.utc).timestamp() + 7200
        mock_fetcher_instance.get_token.return_value = mock_refresh_token

        auth_result = authenticator.refresh_token()

        self.assertEqual(auth_result.token, "new_mock_token")
        self.assertAlmostEqual(
            auth_result.token_expiry.timestamp(), mock_refresh_token.expires_at, delta=1
        )

    @patch("datacosmos.auth.local_authenticator.LocalTokenFetcher")
    def test_refresh_token_failure(self, mock_fetcher_class):
        """Test that token refresh fails when LocalTokenFetcher raises an exception."""
        authenticator = LocalAuthenticator(self.mock_config)
        mock_fetcher_instance = mock_fetcher_class.return_value
        mock_fetcher_instance.get_token.side_effect = Exception("Mocked refresh error")

        with self.assertRaises(DatacosmosException) as cm:
            authenticator.refresh_token()

        self.assertIn("Local token refresh failed", str(cm.exception))

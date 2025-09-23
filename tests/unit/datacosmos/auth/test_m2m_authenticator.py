import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError

from datacosmos.auth.m2m_authenticator import M2MAuthenticator
from datacosmos.exceptions.datacosmos_exception import DatacosmosException


class TestM2MAuthenticator(unittest.TestCase):
    """Unit tests for the M2MAuthenticator class."""

    def setUp(self):
        """Set up a mock Config object before each test."""
        self.mock_config = MagicMock()
        self.mock_config.authentication.client_id = "test_client_id"
        self.mock_config.authentication.client_secret = "test_client_secret"
        self.mock_config.authentication.token_url = "http://token.url"
        self.mock_config.authentication.audience = "test_audience"

    @patch("datacosmos.auth.m2m_authenticator.requests.Session")
    @patch("datacosmos.auth.m2m_authenticator.OAuth2Session")
    def test_authenticate_and_build_session_success(
        self, mock_oauth_session, mock_session
    ):
        """Test that authentication succeeds and returns a valid AuthResult."""

        mock_oauth_session.return_value.fetch_token.return_value = {
            "access_token": "mock_access_token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }

        authenticator = M2MAuthenticator(self.mock_config)
        auth_result = authenticator.authenticate_and_build_session()

        self.assertEqual(auth_result.token, "mock_access_token")
        self.assertIs(auth_result.http_client, mock_session.return_value)
        self.assertIsInstance(auth_result.token_expiry, datetime)
        mock_session.return_value.headers.update.assert_called_with(
            {"Authorization": "Bearer mock_access_token"}
        )
        mock_oauth_session.return_value.fetch_token.assert_called_once_with(
            token_url="http://token.url",
            client_id="test_client_id",
            client_secret="test_client_secret",
            audience="test_audience",
        )

    @patch("datacosmos.auth.m2m_authenticator.OAuth2Session")
    def test_authenticate_and_build_session_failure(self, mock_oauth_session):
        """Test that authentication raises DatacosmosException on HTTP error."""

        mock_oauth_session.return_value.fetch_token.side_effect = HTTPError(
            "Mocked HTTP error"
        )

        authenticator = M2MAuthenticator(self.mock_config)
        with self.assertRaises(DatacosmosException) as cm:
            authenticator.authenticate_and_build_session()

        self.assertIn("M2M authentication failed", str(cm.exception))
        self.assertIsInstance(cm.exception.__cause__, HTTPError)

    def test_refresh_token_delegates_to_auth_method(self):
        """Test that refresh_token simply calls the main auth method."""

        authenticator = M2MAuthenticator(self.mock_config)
        authenticator.authenticate_and_build_session = MagicMock(
            return_value=MagicMock()
        )

        authenticator.refresh_token()

        authenticator.authenticate_and_build_session.assert_called_once()

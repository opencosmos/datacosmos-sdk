"""Tests for ProjectItemClient.delete_project_item method."""

import unittest
from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


class TestDeleteProjectItem(unittest.TestCase):
    """Unit tests for the ProjectItemClient.delete_project_item method."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
        self.mock_delete = patch.object(DatacosmosClient, "delete").start()
        self.mock_check_api_response = patch(
            "datacosmos.stac.project.project_item_client.check_api_response"
        ).start()

        self.mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        self.config = Config(
            authentication=M2MAuthenticationConfig(
                type="m2m",
                client_id="test-client-id",
                client_secret="test-client-secret",
                token_url="https://mock.token.url/oauth/token",
                audience="https://mock.audience",
            )
        )
        self.client = DatacosmosClient(config=self.config)
        self.project_client = ProjectItemClient(self.client)

    def tearDown(self):
        """Stop all patches."""
        patch.stopall()

    def test_delete_project_item(self):
        """Test deleting an item from a project/scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.mock_delete.return_value = mock_response
        self.mock_check_api_response.return_value = None

        self.project_client.delete_project_item("scenario-123", "item-456")

        self.mock_delete.assert_called_once_with(
            self.project_client.project_base_url.with_suffix(
                "/scenario/scenario-123/items/item-456"
            )
        )
        self.mock_check_api_response.assert_called_once_with(mock_response)


if __name__ == "__main__":
    unittest.main()

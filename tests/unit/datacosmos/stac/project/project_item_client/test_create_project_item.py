"""Tests for ProjectItemClient.create_project_item method."""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from pystac import Item

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


class TestCreateProjectItem(unittest.TestCase):
    """Unit tests for the ProjectItemClient.create_project_item method."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
        self.mock_post = patch.object(DatacosmosClient, "post").start()
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

    def test_create_project_item(self):
        """Test creating a new item in a project/scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        self.mock_post.return_value = mock_response
        self.mock_check_api_response.return_value = None

        item = Item(
            id="new-item-789",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            bbox=[0.0, 0.0, 1.0, 1.0],
            datetime=datetime(2023, 1, 1, 10, 30, 9, tzinfo=timezone.utc),
            properties={},
        )

        self.project_client.create_project_item("scenario-123", item)

        self.mock_post.assert_called_once_with(
            self.project_client.project_base_url.with_suffix("/scenario/scenario-123/items"),
            json=item.to_dict(),
        )
        self.mock_check_api_response.assert_called_once_with(mock_response)

    def test_create_project_item_no_id(self):
        """Test creating an item without ID raises ValueError."""
        item = Item(
            id="",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            bbox=[0.0, 0.0, 1.0, 1.0],
            datetime=datetime(2023, 1, 1, 10, 30, 9, tzinfo=timezone.utc),
            properties={},
        )

        with self.assertRaises(ValueError, msg="no item_id found on item"):
            self.project_client.create_project_item("scenario-123", item)


if __name__ == "__main__":
    unittest.main()

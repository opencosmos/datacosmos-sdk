"""Tests for ProjectItemClient.get_project_item method."""

import unittest
from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


class TestGetProjectItem(unittest.TestCase):
    """Unit tests for the ProjectItemClient.get_project_item method."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
        self.mock_get = patch.object(DatacosmosClient, "get").start()
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

    def test_get_project_item(self):
        """Test fetching a specific item from a project/scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "item-123",
                "type": "Feature",
                "stac_version": "1.1.0",
                "stac_extensions": [],
                "collection": "test-collection",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                    ],
                },
                "bbox": [0.0, 0.0, 1.0, 1.0],
                "properties": {"datetime": "2023-01-01T10:30:09Z"},
                "links": [
                    {
                        "rel": "self",
                        "href": "https://example.com/stac/items/item-123.json",
                        "type": "application/json",
                    },
                ],
                "assets": {
                    "visual": {
                        "href": "https://example.com/data/visual.tif",
                        "type": "image/tiff; application=geotiff",
                        "title": "Visual Image",
                        "roles": ["visual", "data"],
                    }
                },
            }
        }
        self.mock_get.return_value = mock_response
        self.mock_check_api_response.return_value = None

        item = self.project_client.get_project_item("scenario-123", "item-123")

        assert item.id == "item-123"
        assert item.properties["datetime"] == "2023-01-01T10:30:09Z"
        self.mock_get.assert_called_once_with(
            self.project_client.project_base_url.with_suffix(
                "/scenario/scenario-123/items/item-123"
            )
        )
        self.mock_check_api_response.assert_called_once_with(mock_response)


if __name__ == "__main__":
    unittest.main()

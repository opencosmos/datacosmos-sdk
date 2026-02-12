"""Tests for ProjectItemClient.list_project_items method."""

import unittest
from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


class TestListProjectItems(unittest.TestCase):
    """Unit tests for the ProjectItemClient.list_project_items method."""

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

    def test_list_project_items(self):
        """Test listing items in a project/scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "id": "item-1",
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
                        "links": [],
                        "assets": {},
                    },
                    {
                        "id": "item-2",
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
                        "properties": {"datetime": "2023-01-02T10:30:09Z"},
                        "links": [],
                        "assets": {},
                    },
                ],
            }
        }
        self.mock_get.return_value = mock_response
        self.mock_check_api_response.return_value = None

        items = list(self.project_client.list_project_items("scenario-123"))

        assert len(items) == 2
        assert items[0].id == "item-1"
        assert items[1].id == "item-2"
        self.mock_get.assert_called_once_with(
            self.project_client.project_base_url.with_suffix("/scenario/scenario-123/items")
        )
        self.mock_check_api_response.assert_called_once_with(mock_response)


if __name__ == "__main__":
    unittest.main()

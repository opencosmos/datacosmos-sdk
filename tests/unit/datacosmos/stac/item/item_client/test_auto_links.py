"""Unit tests for ItemClient auto-link functionality."""

import unittest
from unittest.mock import MagicMock, patch

from pystac import Item

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestItemClientAutoLinks(unittest.TestCase):
    """Unit tests for the ItemClient auto-link population feature."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
        self.mock_put = patch.object(DatacosmosClient, "put").start()
        self.mock_post = patch.object(DatacosmosClient, "post").start()
        self.mock_check_api_response = patch(
            "datacosmos.stac.item.item_client.check_api_response"
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
        self.item_client = ItemClient(self.client)

        self.item_data_no_links = {
            "id": "test-item-1",
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "properties": {
                "datetime": "2023-01-01T12:00:00Z",
                "processing:level": "l1a",
                "sat:platform_international_designator": "TEST-SAT-1",
            },
            "collection": "test-collection",
            "links": [],
            "assets": {},
        }

    def tearDown(self):
        """Clean up patches after each test."""
        patch.stopall()

    def test_add_item_auto_populates_links_datacosmos_item(self):
        """Test that add_item adds self/parent links for DatacosmosItem without links."""
        mock_response = MagicMock()
        self.mock_put.return_value = mock_response

        item = DatacosmosItem(**self.item_data_no_links)
        self.assertFalse(item.has_self_link())
        self.assertFalse(item.has_parent_link())

        self.item_client.add_item(item)

        # After add_item, the item should have links
        self.assertTrue(item.has_self_link())
        self.assertTrue(item.has_parent_link())

    def test_add_item_preserves_existing_links(self):
        """Test that add_item does not overwrite existing links."""
        mock_response = MagicMock()
        self.mock_put.return_value = mock_response

        data = self.item_data_no_links.copy()
        data["links"] = [{"rel": "self", "href": "http://custom.url/item"}]
        item = DatacosmosItem(**data)

        self.item_client.add_item(item)

        # Original self link should be preserved
        self_link = next(link for link in item.links if link.get("rel") == "self")
        self.assertEqual(self_link["href"], "http://custom.url/item")
        # Parent link should be added
        self.assertTrue(item.has_parent_link())

    def test_create_item_auto_populates_links_datacosmos_item(self):
        """Test that create_item adds self/parent links for DatacosmosItem."""
        mock_response = MagicMock()
        self.mock_post.return_value = mock_response

        item = DatacosmosItem(**self.item_data_no_links)

        self.item_client.create_item(item)

        self.assertTrue(item.has_self_link())
        self.assertTrue(item.has_parent_link())

    def test_add_item_auto_populates_links_pystac_item(self):
        """Test that add_item adds self/parent links for pystac Item."""
        mock_response = MagicMock()
        self.mock_put.return_value = mock_response

        # Create pystac item without self/parent links
        pystac_data = self.item_data_no_links.copy()
        pystac_data["stac_version"] = "1.0.0"
        item = Item.from_dict(pystac_data)

        # Verify no self/parent links initially
        has_self = any(link.rel == "self" for link in item.links)
        has_parent = any(link.rel == "parent" for link in item.links)
        self.assertFalse(has_self)
        self.assertFalse(has_parent)

        self.item_client.add_item(item)

        # After add_item, should have links
        has_self = any(link.rel == "self" for link in item.links)
        has_parent = any(link.rel == "parent" for link in item.links)
        self.assertTrue(has_self)
        self.assertTrue(has_parent)

    def test_auto_link_url_format(self):
        """Test that auto-generated links have correct URL format."""
        mock_response = MagicMock()
        self.mock_put.return_value = mock_response

        item = DatacosmosItem(**self.item_data_no_links)
        self.item_client.add_item(item)

        self_link = next(link for link in item.links if link.get("rel") == "self")
        parent_link = next(link for link in item.links if link.get("rel") == "parent")

        # Check URL structure
        self.assertIn("/collections/test-collection/items/test-item-1", self_link["href"])
        self.assertIn("/collections/test-collection", parent_link["href"])
        self.assertNotIn("/items/", parent_link["href"])


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch

from pystac import Item, Link

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestItemClient(unittest.TestCase):
    """Unit tests for the ItemClient class."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
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
        self.stac_client = ItemClient(self.client)

        self.valid_asset_data = {
            "href": "http://example.com/thumb.jpg",
            "title": "Thumbnail Image",
            "description": "A preview thumbnail.",
            "type": "image/jpeg",
            "roles": ["role"],
        }

    def tearDown(self):
        """Clean up patches after each test."""
        patch.stopall()

    def test_create_item_successful_creation(self):
        """Test creating a new STAC item successfully."""
        item_dict = {
            "id": "item-1",
            "collection": "test-collection",
            "type": "Feature",
            "stac_version": "1.0.0",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-12-01T12:00:00Z"},
            "assets": {},
            "links": [],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = item_dict
        self.mock_post.return_value = mock_response

        item = Item.from_dict(item_dict)
        item.add_link(Link.parent(f"https://some.url/collections/{item.collection_id}"))

        self.stac_client.create_item(item)

        self.mock_post.assert_called_once()
        self.mock_check_api_response.assert_called_once()
        self.mock_post.assert_called_with(
            self.stac_client.base_url.with_suffix("/collections/test-collection/items"),
            json=item.to_dict(),
        )

    def test_create_pystac_item_mismatched_collection_raises_error(self):
        """Test that creating a pystac.Item with a mismatched parent link raises StacValidationError."""
        item_dict = {
            "id": "item-1",
            "collection": "test-collection",
            "type": "Feature",
            "stac_version": "1.0.0",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-12-01T12:00:00Z"},
            "assets": {},
            "links": [],
        }

        item = Item.from_dict(item_dict)
        item.add_link(Link.parent("https://some.url/collections/wrong-collection"))

        with self.assertRaisesRegex(
            StacValidationError,
            "Parent link in pystac.Item does not match its collection_id.",
        ):
            self.stac_client.create_item(item)

        self.mock_post.assert_not_called()
        self.mock_check_api_response.assert_not_called()

    def test_create_datacosmos_item_mismatched_collection_raises_error(self):
        """Test that creating a DatacosmosItem with a mismatched parent link raises StacValidationError."""
        item_dict = {
            "id": "item-1",
            "type": "Feature",
            "stac_version": "1.0.0",
            "stac_extensions": [],
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            "properties": {
                "datetime": "2023-12-01T12:00:00Z",
                "processing:level": "l1a",
                "sat:platform_international_designator": "TEST-SAT-1",
            },
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "links": [
                {
                    "href": "https://some.url/collections/wrong-collection",
                    "rel": "parent",
                }
            ],
            "assets": {"thumbnail": self.valid_asset_data},
            "collection": "test-collection",
        }

        item = DatacosmosItem(**item_dict)

        with self.assertRaisesRegex(
            StacValidationError,
            "Parent link in DatacosmosItem does not match its collection.",
        ):
            self.stac_client.create_item(item)

        self.mock_post.assert_not_called()
        self.mock_check_api_response.assert_not_called()

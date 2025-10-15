import unittest
from unittest.mock import MagicMock, patch

from pystac import Item, Link

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.stac_validation_exception import StacValidationException
from datacosmos.stac.item.item_client import ItemClient


class TestItemClientAddItem(unittest.TestCase):
    """Unit tests for the ItemClient.add_item method."""

    def setUp(self):
        """Set up mock objects and client instance for all tests."""
        self.mock_fetch_token = patch(
            "requests_oauthlib.OAuth2Session.fetch_token"
        ).start()
        self.mock_put = patch.object(DatacosmosClient, "put").start()
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
        self.item_dict = {
            "id": "item-1",
            "collection": "test-collection",
            "type": "Feature",
            "stac_version": "1.0.0",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-12-01T12:00:00Z"},
            "assets": {},
            "links": [],
        }

    def tearDown(self):
        """Clean up patches after each test."""
        patch.stopall()

    def test_add_item_successful_creation(self):
        """Test adding a new STAC item successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.item_dict
        self.mock_put.return_value = mock_response

        # Create a pystac.Item with a consistent parent link
        item = Item.from_dict(self.item_dict)
        item.add_link(Link.parent(f"https://some.url/collections/{item.collection_id}"))

        self.stac_client.add_item(item)

        self.mock_put.assert_called_once()
        self.mock_check_api_response.assert_called_once()
        self.mock_put.assert_called_with(
            self.stac_client.base_url.with_suffix(
                "/collections/test-collection/items/item-1"
            ),
            json=item.to_dict(),
        )

    def test_add_item_mismatched_collection_raises_error(self):
        """Test that adding a STAC item with a mismatched parent link raises StacValidationException."""
        # Create a pystac.Item with an inconsistent parent link
        item = Item.from_dict(self.item_dict)
        item.add_link(Link.parent("https://some.url/collections/wrong-collection"))

        with self.assertRaisesRegex(
            StacValidationException,
            "Parent link in pystac.Item does not match its collection_id.",
        ):
            self.stac_client.add_item(item)

        self.mock_put.assert_not_called()
        self.mock_check_api_response.assert_not_called()

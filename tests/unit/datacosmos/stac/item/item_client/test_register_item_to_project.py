import unittest
from unittest.mock import MagicMock, patch

from pystac import Item

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestItemClientRegisterItemToProject(unittest.TestCase):
    """Unit tests for the ItemClient.register_item_to_project method."""

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
        self.item_client = ItemClient(self.client)

    def tearDown(self):
        """Stop all patches."""
        patch.stopall()

    def test_register_pystac_item_to_project(self):
        """Test registering a pystac Item to a project."""
        self.mock_post.return_value = MagicMock(status_code=200)

        item = Item.from_dict({
            "id": "item-1",
            "collection": "test-collection",
            "type": "Feature",
            "stac_version": "1.1.0",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-12-01T12:00:00Z"},
            "assets": {},
            "links": [],
        })

        self.item_client.register_item_to_project(item, "project-123")

        self.mock_post.assert_called_once()
        call_args = self.mock_post.call_args
        # Verify the URL ends with /relation
        url = str(call_args[0][0])
        assert "/scenario/relation" in url or url.endswith("/relation")
        # Verify the body
        body = call_args[1]["json"]
        assert body["scenario"] == "project-123"
        assert body["collection"] == "test-collection"
        assert body["item"] == "item-1"

    def test_register_datacosmos_item_to_project(self):
        """Test registering a DatacosmosItem to a project."""
        self.mock_post.return_value = MagicMock(status_code=200)

        item = DatacosmosItem(
            id="item-2",
            type="Feature",
            stac_version="1.0.0",
            stac_extensions=[],
            geometry={"type": "Point", "coordinates": [0, 0]},
            bbox=[0, 0, 1, 1],
            properties={"datetime": "2023-12-01T12:00:00Z"},
            links=[],
            assets={},
            collection="my-collection",
        )

        self.item_client.register_item_to_project(item, "project-456")

        self.mock_post.assert_called_once()
        call_args = self.mock_post.call_args
        body = call_args[1]["json"]
        assert body["scenario"] == "project-456"
        assert body["collection"] == "my-collection"
        assert body["item"] == "item-2"

    def test_register_item_without_collection_raises(self):
        """Test that registering an item without a collection raises ValueError."""
        item = Item.from_dict({
            "id": "item-no-collection",
            "type": "Feature",
            "stac_version": "1.1.0",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-12-01T12:00:00Z"},
            "assets": {},
            "links": [],
        })

        with self.assertRaises(ValueError) as ctx:
            self.item_client.register_item_to_project(item, "project-123")

        assert "no collection_id found" in str(ctx.exception)

    def test_register_item_without_id_raises(self):
        """Test that registering an item without an id raises ValueError."""
        from datetime import datetime as dt

        # Create valid item then clear the id
        item = Item(
            id="temp-id",
            geometry={"type": "Point", "coordinates": [0, 0]},
            bbox=[0, 0, 1, 1],
            datetime=dt.utcnow(),
            properties={},
        )
        item.collection_id = "my-collection"
        item.id = None  # Clear the id after creation

        with self.assertRaises(ValueError) as ctx:
            self.item_client.register_item_to_project(item, "project-123")

        assert "no item_id found" in str(ctx.exception)


if __name__ == "__main__":
    unittest.main()

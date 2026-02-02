"""Unit tests for DatacosmosItem pystac compatibility and link helper methods."""

import unittest

from pystac import Item as PystacItem

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestDatacosmosItemPystacCompatibility(unittest.TestCase):
    """Tests for pystac Item conversion methods."""

    def setUp(self):
        """Set up valid item data for testing."""
        self.valid_item_data = {
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
            "stac_version": "1.0.0",
            "stac_extensions": [],
            "collection": "test-collection",
            "links": [
                {
                    "rel": "parent",
                    "href": "https://api.example.com/stac/collections/test-collection",
                    "type": "application/json",
                }
            ],
            "assets": {
                "thumbnail": {
                    "href": "http://example.com/thumb.jpg",
                    "title": "Thumbnail",
                    "description": "A thumbnail image",
                    "type": "image/jpeg",
                    "roles": ["thumbnail"],
                }
            },
        }

    def test_to_pystac_item(self):
        """Test conversion from DatacosmosItem to pystac Item."""
        dc_item = DatacosmosItem(**self.valid_item_data)
        pystac_item = dc_item.to_pystac_item()

        self.assertIsInstance(pystac_item, PystacItem)
        self.assertEqual(pystac_item.id, "test-item-1")
        self.assertEqual(pystac_item.collection_id, "test-collection")
        self.assertIn("thumbnail", pystac_item.assets)

    def test_from_pystac_item(self):
        """Test conversion from pystac Item to DatacosmosItem."""
        # First create a pystac item
        pystac_item = PystacItem.from_dict(self.valid_item_data)

        # Convert to DatacosmosItem
        dc_item = DatacosmosItem.from_pystac_item(pystac_item)

        self.assertIsInstance(dc_item, DatacosmosItem)
        self.assertEqual(dc_item.id, "test-item-1")
        self.assertEqual(dc_item.collection, "test-collection")

    def test_roundtrip_conversion(self):
        """Test that DatacosmosItem -> pystac -> DatacosmosItem preserves data."""
        original = DatacosmosItem(**self.valid_item_data)

        # Convert to pystac and back
        pystac_item = original.to_pystac_item()
        roundtrip = DatacosmosItem.from_pystac_item(pystac_item)

        self.assertEqual(original.id, roundtrip.id)
        self.assertEqual(original.collection, roundtrip.collection)
        self.assertEqual(
            original.properties["datetime"], roundtrip.properties["datetime"]
        )


class TestDatacosmosItemLinkHelpers(unittest.TestCase):
    """Tests for link helper methods (add_self_link, add_parent_link, etc.)."""

    def setUp(self):
        """Set up item data without links for testing."""
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
        self.base_url = "https://api.example.com/stac"

    def test_has_self_link_false(self):
        """Test has_self_link returns False when no self link exists."""
        item = DatacosmosItem(**self.item_data_no_links)
        self.assertFalse(item.has_self_link())

    def test_has_parent_link_false(self):
        """Test has_parent_link returns False when no parent link exists."""
        item = DatacosmosItem(**self.item_data_no_links)
        self.assertFalse(item.has_parent_link())

    def test_has_self_link_true(self):
        """Test has_self_link returns True when self link exists."""
        data = self.item_data_no_links.copy()
        data["links"] = [{"rel": "self", "href": "http://example.com/item"}]
        item = DatacosmosItem(**data)
        self.assertTrue(item.has_self_link())

    def test_has_parent_link_true(self):
        """Test has_parent_link returns True when parent link exists."""
        data = self.item_data_no_links.copy()
        data["links"] = [{"rel": "parent", "href": "http://example.com/collection"}]
        item = DatacosmosItem(**data)
        self.assertTrue(item.has_parent_link())

    def test_add_self_link(self):
        """Test add_self_link adds a properly formatted self link."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_self_link(self.base_url)

        self.assertTrue(item.has_self_link())
        self_link = next(link for link in item.links if link.get("rel") == "self")
        self.assertEqual(
            self_link["href"],
            "https://api.example.com/stac/collections/test-collection/items/test-item-1",
        )
        self.assertEqual(self_link["type"], "application/geo+json")

    def test_add_parent_link(self):
        """Test add_parent_link adds a properly formatted parent link."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_parent_link(self.base_url)

        self.assertTrue(item.has_parent_link())
        parent_link = next(link for link in item.links if link.get("rel") == "parent")
        self.assertEqual(
            parent_link["href"],
            "https://api.example.com/stac/collections/test-collection",
        )
        self.assertEqual(parent_link["type"], "application/json")

    def test_add_self_link_with_explicit_collection(self):
        """Test add_self_link with explicit collection_id parameter."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_self_link(self.base_url, collection_id="other-collection")

        self_link = next(link for link in item.links if link.get("rel") == "self")
        self.assertIn("other-collection", self_link["href"])

    def test_add_self_link_does_not_duplicate(self):
        """Test that add_self_link does not add duplicate links."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_self_link(self.base_url)
        item.add_self_link(self.base_url)  # Call again

        self_links = [link for link in item.links if link.get("rel") == "self"]
        self.assertEqual(len(self_links), 1)

    def test_add_parent_link_does_not_duplicate(self):
        """Test that add_parent_link does not add duplicate links."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_parent_link(self.base_url)
        item.add_parent_link(self.base_url)  # Call again

        parent_links = [link for link in item.links if link.get("rel") == "parent"]
        self.assertEqual(len(parent_links), 1)

    def test_ensure_standard_links(self):
        """Test ensure_standard_links adds both self and parent links."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.ensure_standard_links(self.base_url)

        self.assertTrue(item.has_self_link())
        self.assertTrue(item.has_parent_link())

    def test_ensure_standard_links_preserves_existing(self):
        """Test that ensure_standard_links preserves existing links."""
        data = self.item_data_no_links.copy()
        data["links"] = [{"rel": "self", "href": "http://custom.url/item"}]
        item = DatacosmosItem(**data)

        item.ensure_standard_links(self.base_url)

        # Should still have the original self link, not replaced
        self_link = next(link for link in item.links if link.get("rel") == "self")
        self.assertEqual(self_link["href"], "http://custom.url/item")
        # Should have added parent link
        self.assertTrue(item.has_parent_link())

    def test_add_self_link_trailing_slash_handling(self):
        """Test that trailing slashes in base_url are handled correctly."""
        item = DatacosmosItem(**self.item_data_no_links)
        item.add_self_link("https://api.example.com/stac/")

        self_link = next(link for link in item.links if link.get("rel") == "self")
        # Should not have double slashes
        self.assertNotIn("//collections", self_link["href"])

    def test_add_self_link_no_collection_raises(self):
        """Test that add_self_link raises if no collection is available."""
        data = self.item_data_no_links.copy()
        data["collection"] = None
        item = DatacosmosItem(**data)

        with self.assertRaises(ValueError) as context:
            item.add_self_link(self.base_url)
        self.assertIn("collection_id", str(context.exception))


if __name__ == "__main__":
    unittest.main()

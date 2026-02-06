"""Unit tests for STAC 1.1.0 absolute self-link validation requirement.

STAC 1.1.0 requires that self links use absolute URLs.
Spec change: "Validation for absolute self link in item schema."
https://github.com/radiantearth/stac-spec/issues/1281
"""

import unittest

from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestStac110AbsoluteSelfLink(unittest.TestCase):
    """Tests for STAC 1.1.0 absolute self-link validation requirement."""

    def setUp(self):
        """Set up valid item data for self-link validation tests."""
        self.base_item_data = {
            "id": "test-item-1",
            "type": "Feature",
            "stac_version": "1.1.0",
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
                "sat:platform_international_designator": "2024-001A",
            },
            "collection": "test-collection",
            "assets": {},
        }

    def test_absolute_self_link_valid(self):
        """Test that an absolute self-link URL passes validation."""
        item_data = {**self.base_item_data}
        item_data["links"] = [
            {
                "rel": "self",
                "href": "https://api.example.com/collections/test-collection/items/test-item-1",
            },
            {
                "rel": "parent",
                "href": "https://api.example.com/collections/test-collection",
            },
        ]
        item = DatacosmosItem(**item_data)

        # Should not raise
        item.validate()

    def test_relative_self_link_raises_error(self):
        """Test that a relative self-link URL raises StacValidationError."""
        item_data = {**self.base_item_data}
        item_data["links"] = [
            {"rel": "self", "href": "items/test-item-1"},
            {
                "rel": "parent",
                "href": "https://api.example.com/collections/test-collection",
            },
        ]
        item = DatacosmosItem(**item_data)

        with self.assertRaises(StacValidationError) as context:
            item.validate()

        self.assertIn("absolute URL", str(context.exception))
        self.assertIn("STAC 1.1.0", str(context.exception))

    def test_self_link_missing_scheme_raises_error(self):
        """Test that a URL without scheme raises StacValidationError."""
        item_data = {**self.base_item_data}
        item_data["links"] = [
            {"rel": "self", "href": "//example.com/items/test-item-1"},
            {
                "rel": "parent",
                "href": "https://api.example.com/collections/test-collection",
            },
        ]
        item = DatacosmosItem(**item_data)

        with self.assertRaises(StacValidationError) as context:
            item.validate()

        self.assertIn("absolute URL", str(context.exception))

    def test_self_link_path_only_raises_error(self):
        """Test that a path-only self-link raises StacValidationError."""
        item_data = {**self.base_item_data}
        item_data["links"] = [
            {"rel": "self", "href": "/collections/test-collection/items/test-item-1"},
            {
                "rel": "parent",
                "href": "https://api.example.com/collections/test-collection",
            },
        ]
        item = DatacosmosItem(**item_data)

        with self.assertRaises(StacValidationError) as context:
            item.validate()

        self.assertIn("absolute URL", str(context.exception))

    def test_item_without_self_link_passes(self):
        """Test that an item without a self-link passes validation (link is optional)."""
        item_data = {**self.base_item_data}
        item_data["links"] = [
            {
                "rel": "parent",
                "href": "https://api.example.com/collections/test-collection",
            },
        ]
        item = DatacosmosItem(**item_data)

        # Should not raise - self link is strongly recommended but not required
        item.validate()


if __name__ == "__main__":
    unittest.main()

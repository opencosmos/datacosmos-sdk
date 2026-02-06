"""Unit tests for pystac roundtrip compatibility with STAC 1.1.0 fields.

Validates that DatacosmosItem <-> pystac.Item conversion preserves
all 1.1.0 specific fields including bands, link metadata, and stac_version.
"""

import unittest

from pystac import Item as PystacItem

from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestStac110PystacRoundtrip(unittest.TestCase):
    """Tests for pystac roundtrip compatibility with STAC 1.1.0 fields."""

    def setUp(self):
        """Set up full 1.1.0 item with all new features."""
        self.full_item_data = {
            "id": "test-item-1",
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [],
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
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.example.com/collections/test-collection/items/test-item-1",
                    "type": "application/geo+json",
                },
                {
                    "rel": "parent",
                    "href": "https://api.example.com/collections/test-collection",
                    "type": "application/json",
                },
            ],
            "assets": {
                "data": {
                    "href": "https://example.com/data.tif",
                    "type": "image/tiff; application=geotiff",
                    "roles": ["data"],
                    "keywords": ["satellite", "optical"],
                    "bands": [
                        {
                            "name": "red",
                            "data_type": "uint16",
                            "nodata": 0,
                            "statistics": {"minimum": 0, "maximum": 65535},
                        }
                    ],
                }
            },
        }

    def test_item_with_bands_roundtrip(self):
        """Test that DatacosmosItem -> pystac -> DatacosmosItem preserves bands."""
        original = DatacosmosItem.from_dict(self.full_item_data)

        # Convert to pystac and back
        pystac_item = original.to_pystac_item()
        roundtrip = DatacosmosItem.from_pystac_item(pystac_item)

        # Verify bands are preserved
        original_bands = original.assets["data"].bands
        roundtrip_bands = roundtrip.assets["data"].bands

        self.assertEqual(len(original_bands), len(roundtrip_bands))
        self.assertEqual(original_bands[0].name, roundtrip_bands[0].name)
        self.assertEqual(original_bands[0].data_type, roundtrip_bands[0].data_type)

    def test_item_with_asset_keywords_roundtrip(self):
        """Test that asset keywords are preserved through roundtrip."""
        original = DatacosmosItem.from_dict(self.full_item_data)

        pystac_item = original.to_pystac_item()
        roundtrip = DatacosmosItem.from_pystac_item(pystac_item)

        self.assertEqual(
            original.assets["data"].keywords, roundtrip.assets["data"].keywords
        )

    def test_item_stac_version_preserved(self):
        """Test that stac_version 1.1.0 is preserved through roundtrip."""
        original = DatacosmosItem.from_dict(self.full_item_data)

        pystac_item = original.to_pystac_item()
        roundtrip = DatacosmosItem.from_pystac_item(pystac_item)

        self.assertEqual(original.stac_version, "1.1.0")
        self.assertEqual(roundtrip.stac_version, "1.1.0")

    def test_item_core_fields_preserved(self):
        """Test that core item fields are preserved through roundtrip."""
        original = DatacosmosItem.from_dict(self.full_item_data)

        pystac_item = original.to_pystac_item()
        roundtrip = DatacosmosItem.from_pystac_item(pystac_item)

        self.assertEqual(original.id, roundtrip.id)
        self.assertEqual(original.collection, roundtrip.collection)
        self.assertEqual(
            original.properties["datetime"], roundtrip.properties["datetime"]
        )
        self.assertEqual(original.bbox, roundtrip.bbox)

    def test_pystac_item_is_valid_instance(self):
        """Test that conversion produces a valid pystac Item instance."""
        dc_item = DatacosmosItem.from_dict(self.full_item_data)
        pystac_item = dc_item.to_pystac_item()

        self.assertIsInstance(pystac_item, PystacItem)
        self.assertEqual(pystac_item.id, "test-item-1")
        self.assertEqual(pystac_item.collection_id, "test-collection")


if __name__ == "__main__":
    unittest.main()

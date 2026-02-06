"""Unit tests for STAC 1.1.0 common metadata fields on Assets.

STAC 1.1.0 added several fields to asset common metadata:
- keywords (from Collections)
- bands (unified band metadata)
- data_type, nodata, statistics, unit
Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/assets.md
"""

import unittest

from datacosmos.stac.item.models.asset import Asset
from datacosmos.stac.item.models.band import Band
from datacosmos.stac.item.models.statistics import Statistics


class TestStac110AssetCommonMetadata(unittest.TestCase):
    """Tests for STAC 1.1.0 common metadata fields on Assets."""

    def setUp(self):
        """Set up valid asset data with 1.1.0 common metadata."""
        self.valid_band = {
            "name": "red",
            "data_type": "uint16",
            "nodata": 0,
            "unit": "reflectance",
            "statistics": {"minimum": 0, "maximum": 10000, "mean": 2500.0},
        }
        self.valid_asset_data = {
            "href": "https://example.com/data.tif",
            "type": "image/tiff; application=geotiff",
            "title": "GeoTIFF Data",
            "roles": ["data"],
            "keywords": ["satellite", "optical", "multispectral"],
            "bands": [self.valid_band],
            "data_type": "uint16",
            "nodata": 0,
            "unit": "reflectance",
            "statistics": {"minimum": 0, "maximum": 10000},
        }

    def test_asset_with_bands_field(self):
        """Test that Asset model accepts the 1.1.0 bands list field."""
        asset = Asset(**self.valid_asset_data)

        self.assertIsNotNone(asset.bands)
        self.assertEqual(len(asset.bands), 1)
        self.assertIsInstance(asset.bands[0], Band)
        self.assertEqual(asset.bands[0].name, "red")

    def test_asset_with_keywords_field(self):
        """Test that Asset model accepts the 1.1.0 keywords field."""
        asset = Asset(**self.valid_asset_data)

        self.assertEqual(asset.keywords, ["satellite", "optical", "multispectral"])

    def test_asset_with_statistics_field(self):
        """Test that Asset model accepts the 1.1.0 statistics field."""
        asset = Asset(**self.valid_asset_data)

        self.assertIsInstance(asset.statistics, Statistics)
        self.assertEqual(asset.statistics.minimum, 0)
        self.assertEqual(asset.statistics.maximum, 10000)

    def test_asset_with_data_type_and_unit(self):
        """Test that Asset model accepts data_type, nodata, and unit fields."""
        asset = Asset(**self.valid_asset_data)

        self.assertEqual(asset.data_type, "uint16")
        self.assertEqual(asset.nodata, 0)
        self.assertEqual(asset.unit, "reflectance")

    def test_asset_multiple_bands(self):
        """Test that Asset model handles multiple bands correctly."""
        asset_data = {**self.valid_asset_data}
        asset_data["bands"] = [
            {"name": "red", "data_type": "uint16"},
            {"name": "green", "data_type": "uint16"},
            {"name": "blue", "data_type": "uint16"},
        ]
        asset = Asset(**asset_data)

        self.assertEqual(len(asset.bands), 3)
        self.assertEqual(asset.bands[1].name, "green")


if __name__ == "__main__":
    unittest.main()

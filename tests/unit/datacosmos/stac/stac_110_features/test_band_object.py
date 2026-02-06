"""Unit tests for the STAC 1.1.0 unified Band object.

STAC 1.1.0 introduced a new 'bands' field in common metadata to unify
eo:bands and raster:bands into a single construct.
Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#band-object
"""

import unittest

from datacosmos.stac.item.models.band import Band
from datacosmos.stac.item.models.statistics import Statistics


class TestStac110BandObject(unittest.TestCase):
    """Tests for the STAC 1.1.0 unified Band object."""

    def setUp(self):
        """Set up valid band data with all 1.1.0 fields."""
        self.valid_band_data = {
            "name": "red",
            "description": "Red visible band",
            "data_type": "uint16",
            "nodata": 0,
            "unit": "W/m²/sr/µm",
            "statistics": {
                "minimum": 0,
                "maximum": 65535,
                "mean": 1234.5,
                "stddev": 500.2,
            },
        }

    def test_band_creation_with_all_fields(self):
        """Test that Band model accepts all STAC 1.1.0 common metadata fields."""
        band = Band(**self.valid_band_data)

        self.assertEqual(band.name, "red")
        self.assertEqual(band.description, "Red visible band")
        self.assertEqual(band.data_type, "uint16")
        self.assertEqual(band.nodata, 0)
        self.assertEqual(band.unit, "W/m²/sr/µm")
        self.assertIsNotNone(band.statistics)

    def test_band_statistics_object(self):
        """Test that Band model correctly handles nested Statistics object."""
        band = Band(**self.valid_band_data)

        self.assertIsInstance(band.statistics, Statistics)
        self.assertEqual(band.statistics.minimum, 0)
        self.assertEqual(band.statistics.maximum, 65535)
        self.assertEqual(band.statistics.mean, 1234.5)
        self.assertEqual(band.statistics.stddev, 500.2)

    def test_band_to_dict_serialization(self):
        """Test that Band model serializes to dict correctly."""
        band = Band(**self.valid_band_data)
        band_dict = band.model_dump()

        self.assertIsInstance(band_dict, dict)
        self.assertEqual(band_dict["name"], "red")
        self.assertEqual(band_dict["data_type"], "uint16")
        self.assertIn("statistics", band_dict)

    def test_band_with_minimal_fields(self):
        """Test that Band model works with minimal optional fields."""
        band = Band(name="nir")

        self.assertEqual(band.name, "nir")
        self.assertIsNone(band.data_type)
        self.assertIsNone(band.statistics)

    def test_band_allows_extra_fields(self):
        """Test that Band model allows extension fields (extra='allow')."""
        band_data = {**self.valid_band_data, "custom:field": "custom_value"}
        band = Band(**band_data)

        band_dict = band.model_dump()
        self.assertEqual(band_dict["custom:field"], "custom_value")


if __name__ == "__main__":
    unittest.main()

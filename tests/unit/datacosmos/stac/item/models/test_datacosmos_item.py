import unittest
from datetime import datetime

from shapely.geometry import Polygon

from datacosmos.exceptions.datacosmos_exception import DatacosmosException
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestDatacosmosItem(unittest.TestCase):
    """Unit tests for the DatacosmosItem model."""

    def setUp(self):
        """Set up a valid item dictionary for testing."""
        self.valid_item_data = {
            "id": "test-item-1",
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
                "datetime": "2023-01-01T12:00:00Z",
                "processing:level": "l1a",
                "sat:platform_international_designator": "TEST-SAT-1",
            },
            "links": [],
            "assets": {
                "thumbnail": {
                    "href": "http://example.com/thumb.jpg",
                    "title": "Thumbnail Image",
                    "description": "A preview thumbnail.",
                    "type": "image/jpeg",
                    "roles": ["thumbnail"],
                }
            },
            "collection": "test-collection",
            "bbox": [0.0, 0.0, 1.0, 1.0],
        }

    def test_valid_item_creation(self):
        """Test that a DatacosmosItem can be created from a valid dictionary."""
        try:
            item = DatacosmosItem(**self.valid_item_data)
            self.assertIsInstance(item, DatacosmosItem)
            self.assertEqual(item.id, "test-item-1")
            self.assertEqual(item.type, "Feature")
            self.assertEqual(item.collection, "test-collection")
        except Exception as e:
            self.fail(f"DatacosmosItem creation failed with valid data: {e}")

    def test_invalid_properties_validation(self):
        """Test that validation fails when mandatory properties are missing."""
        invalid_data = self.valid_item_data.copy()
        # Remove a mandatory key
        del invalid_data["properties"]["datetime"]

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)

        self.assertIn("datetime", str(cm.exception))

    def test_invalid_geometry_type(self):
        """Test that validation fails for a non-Polygon geometry type."""
        invalid_data = self.valid_item_data.copy()
        invalid_data["geometry"] = {"type": "Point", "coordinates": [0.0, 0.0]}

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)

        self.assertIn("Geometry must be a Polygon", str(cm.exception))

    def test_geometry_missing_coordinates(self):
        """Test that validation fails when geometry coordinates are missing."""
        invalid_data = self.valid_item_data.copy()
        invalid_data["geometry"] = {"type": "Polygon", "coordinates": None}

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)

        self.assertIn("Geometry must be a Polygon with coordinates.", str(cm.exception))

    def test_property_accessors(self):
        """Test that all properties and methods return the correct data."""
        item = DatacosmosItem(**self.valid_item_data)

        self.assertEqual(item.get_property("datetime"), "2023-01-01T12:00:00Z")
        self.assertEqual(item.get_property("non-existent"), None)

        self.assertEqual(
            item.get_asset("thumbnail").href, "http://example.com/thumb.jpg"
        )
        self.assertEqual(item.get_asset("non-existent"), None)

    def test_datacosmos_datetime_property(self):
        """Test the datetime property returns a valid datetime object."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertIsInstance(item.datacosmos_datetime, datetime)
        self.assertEqual(item.datacosmos_datetime, datetime(2023, 1, 1, 12, 0, 0))

    def test_level_property(self):
        """Test the level property returns a valid ProcessingLevel enum."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertIsInstance(item.level, ProcessingLevel)
        self.assertEqual(item.level, ProcessingLevel.L1A)

    def test_sat_int_designator_property(self):
        """Test the sat_int_designator property returns a string."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertEqual(item.sat_int_designator, "TEST-SAT-1")

    def test_polygon_property(self):
        """Test the polygon property returns a shapely Polygon object."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertIsInstance(item.polygon, Polygon)
        self.assertEqual(len(item.polygon.exterior.coords), 5)

    def test_to_dict_method(self):
        """Test that the to_dict method works correctly."""
        item = DatacosmosItem(**self.valid_item_data)
        item_dict = item.to_dict()
        self.assertIsInstance(item_dict, dict)
        self.assertEqual(item_dict["id"], "test-item-1")
        self.assertEqual(item_dict["properties"]["datetime"], "2023-01-01T12:00:00Z")

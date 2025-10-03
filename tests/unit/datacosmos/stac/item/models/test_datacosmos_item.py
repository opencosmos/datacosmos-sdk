import unittest
from datetime import datetime

from shapely.geometry import Polygon

from datacosmos.exceptions.datacosmos_exception import DatacosmosException
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem


class TestDatacosmosItem(unittest.TestCase):
    """Unit tests for the DatacosmosItem model."""

    def setUp(self):
        """Set up valid data dictionaries for testing."""
        # Minimal STAC-required fields
        self.stac_core_data = {
            "id": "test-item-1",
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                ],
            },
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "properties": {},
            "links": [],
            "assets": {},
        }

        # Datacosmos-specific required properties
        self.datacosmos_properties = {
            "datetime": "2023-01-01T12:00:00Z",
            "processing:level": "l1a",
            "sat:platform_international_designator": "TEST-SAT-1",
        }

        # Full, valid item data for most tests
        self.valid_item_data = {
            **self.stac_core_data,
            "properties": {**self.datacosmos_properties},
            "stac_version": "1.0.0",
            "stac_extensions": [],
            "collection": "test-collection",
            "assets": {
                "thumbnail": {
                    "href": "http://example.com/thumb.jpg",
                    "title": "Thumbnail Image",
                    "description": "A preview thumbnail.",
                    "type": "image/jpeg",
                    "roles": ["thumbnail"],
                }
            },
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

    def test_minimum_required_fields_are_valid(self):
        """
        Test that an item with only the Datacosmos-specific and
        STAC-required fields is considered valid.
        """
        min_valid_data = {
            "id": "minimal-item",
            "type": "Feature",
            "geometry": self.stac_core_data["geometry"],
            "bbox": self.stac_core_data["bbox"],
            "properties": self.datacosmos_properties,
            "links": [],
            "assets": {},
        }
        try:
            item = DatacosmosItem(**min_valid_data)
            self.assertIsInstance(item, DatacosmosItem)
        except Exception as e:
            self.fail(f"Minimum valid item creation failed: {e}")

    def test_invalid_properties_validation(self):
        """Test that validation fails when a mandatory Datacosmos property is missing."""
        invalid_data = self.valid_item_data.copy()
        del invalid_data["properties"]["datetime"]

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)
        self.assertIn("datetime", str(cm.exception))

    def test_multiple_invalid_properties_validation(self):
        """
        Test that validation fails and reports all missing mandatory properties.
        """
        invalid_data = self.valid_item_data.copy()
        del invalid_data["properties"]["datetime"]
        del invalid_data["properties"]["processing:level"]

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)
        self.assertIn("datetime", str(cm.exception))
        self.assertIn("processing:level", str(cm.exception))
        self.assertNotIn("sat:platform_international_designator", str(cm.exception))

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

    def test_bbox_mismatch_with_geometry(self):
        """
        Test that an item fails to validate when the bbox does not match the geometry.
        This tests for interdependency.
        """
        invalid_data = self.valid_item_data.copy()
        # Change bbox to a value that doesn't match the geometry
        invalid_data["bbox"] = [10.0, 10.0, 20.0, 20.0]

        with self.assertRaises(DatacosmosException) as cm:
            DatacosmosItem(**invalid_data)
        self.assertIn(
            "Provided bbox does not match geometry bounds.", str(cm.exception)
        )

    def test_valid_bbox_vs_geometry(self):
        """Test that an item with a matching bbox and geometry is valid."""
        # The setUp method already creates a valid item with a matching bbox and geometry.
        try:
            DatacosmosItem(**self.valid_item_data)
        except Exception as e:
            self.fail(f"Valid bbox/geometry consistency check failed: {e}")

    def test_property_accessors(self):
        """Test that all properties and methods return the correct data."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertEqual(item.get_property("datetime"), "2023-01-01T12:00:00Z")
        self.assertEqual(item.get_property("non-existent"), None)

    def test_datacosmos_datetime_property(self):
        """Test the datetime property returns a valid datetime object."""
        item = DatacosmosItem(**self.valid_item_data)
        self.assertIsInstance(item.datetime, datetime)
        self.assertEqual(item.datetime, datetime(2023, 1, 1, 12, 0, 0))

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

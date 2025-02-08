import pytest

from datacosmos.stac.models.item_update import ItemUpdate


class TestItemUpdate:
    """Unit tests for the ItemUpdate model validation."""

    def test_valid_item_update_with_datetime(self):
        """Test that ItemUpdate passes validation with a single datetime field."""
        update_data = ItemUpdate(
            properties={"new_property": "value", "datetime": "2023-12-01T12:00:00Z"}
        )
        assert update_data.properties["datetime"] == "2023-12-01T12:00:00Z"

    def test_valid_item_update_with_start_and_end_datetime(self):
        """Test that ItemUpdate passes validation with start_datetime and end_datetime."""
        update_data = ItemUpdate(
            properties={
                "new_property": "value",
                "start_datetime": "2023-12-01T12:00:00Z",
                "end_datetime": "2023-12-01T12:30:00Z",
            }
        )
        assert update_data.properties["start_datetime"] == "2023-12-01T12:00:00Z"
        assert update_data.properties["end_datetime"] == "2023-12-01T12:30:00Z"

    def test_invalid_item_update_missing_datetime(self):
        """Test that ItemUpdate fails validation when datetime is missing."""
        with pytest.raises(
            ValueError,
            match="Either 'datetime' or both 'start_datetime' and 'end_datetime' must be provided.",
        ):
            ItemUpdate(properties={"new_property": "value"})

    def test_invalid_item_update_empty_properties(self):
        """Test that ItemUpdate fails validation when properties are empty."""
        with pytest.raises(
            ValueError,
            match="Either 'datetime' or both 'start_datetime' and 'end_datetime' must be provided.",
        ):
            ItemUpdate(properties={})

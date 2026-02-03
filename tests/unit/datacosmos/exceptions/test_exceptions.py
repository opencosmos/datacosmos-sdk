"""Unit tests for the new exception classes."""

import unittest

from datacosmos.exceptions import (
    CollectionNotFoundError,
    DatacosmosError,
    DeleteError,
    ItemNotFoundError,
    StorageError,
)


class TestItemNotFoundError(unittest.TestCase):
    """Unit tests for ItemNotFoundError."""

    def test_basic_initialization(self):
        """Test basic error message initialization."""
        error = ItemNotFoundError("Item not found")
        self.assertIn("Item not found", str(error))
        self.assertIsInstance(error, DatacosmosError)

    def test_with_item_id_context(self):
        """Test that item_id is included in error message."""
        error = ItemNotFoundError("Item not found", item_id="test-item-123")
        self.assertEqual(error.item_id, "test-item-123")
        self.assertIn("item_id=test-item-123", str(error))

    def test_with_collection_id_context(self):
        """Test that collection_id is included in error message."""
        error = ItemNotFoundError(
            "Item not found", item_id="test-item", collection_id="test-collection"
        )
        self.assertEqual(error.collection_id, "test-collection")
        self.assertIn("collection_id=test-collection", str(error))

    def test_with_both_context_fields(self):
        """Test that both item_id and collection_id appear in message."""
        error = ItemNotFoundError(
            "Not found", item_id="item-1", collection_id="coll-1"
        )
        error_str = str(error)
        self.assertIn("item_id=item-1", error_str)
        self.assertIn("collection_id=coll-1", error_str)


class TestCollectionNotFoundError(unittest.TestCase):
    """Unit tests for CollectionNotFoundError."""

    def test_basic_initialization(self):
        """Test basic error message initialization."""
        error = CollectionNotFoundError("Collection not found")
        self.assertIn("Collection not found", str(error))
        self.assertIsInstance(error, DatacosmosError)

    def test_with_collection_id_context(self):
        """Test that collection_id is included in error message."""
        error = CollectionNotFoundError(
            "Collection not found", collection_id="my-collection"
        )
        self.assertEqual(error.collection_id, "my-collection")
        self.assertIn("collection_id=my-collection", str(error))


class TestStorageError(unittest.TestCase):
    """Unit tests for StorageError."""

    def test_basic_initialization(self):
        """Test basic error message initialization."""
        error = StorageError("Storage operation failed")
        self.assertIn("Storage operation failed", str(error))
        self.assertIsInstance(error, DatacosmosError)

    def test_with_path_and_operation(self):
        """Test that path and operation are included in error message."""
        error = StorageError(
            "Failed to upload", path="/bucket/file.tif", operation="upload"
        )
        self.assertEqual(error.path, "/bucket/file.tif")
        self.assertEqual(error.operation, "upload")
        error_str = str(error)
        self.assertIn("upload", error_str)
        self.assertIn("/bucket/file.tif", error_str)

    def test_delete_operation(self):
        """Test storage error with delete operation."""
        error = StorageError("File not found", path="/path/to/file", operation="delete")
        self.assertEqual(error.operation, "delete")
        self.assertIn("delete", str(error))


class TestDeleteError(unittest.TestCase):
    """Unit tests for DeleteError."""

    def test_basic_initialization(self):
        """Test basic error message initialization."""
        error = DeleteError("Delete failed")
        self.assertIn("Delete failed", str(error))
        self.assertIsInstance(error, DatacosmosError)
        self.assertEqual(error.failed_assets, [])

    def test_with_item_context(self):
        """Test that item_id and collection_id appear in message."""
        error = DeleteError(
            "Delete failed", item_id="item-123", collection_id="coll-abc"
        )
        self.assertEqual(error.item_id, "item-123")
        self.assertEqual(error.collection_id, "coll-abc")
        error_str = str(error)
        self.assertIn("item_id=item-123", error_str)
        self.assertIn("collection_id=coll-abc", error_str)

    def test_with_failed_assets(self):
        """Test that failed_assets are tracked and appear in message."""
        failed = [
            {"asset_key": "thumbnail", "error": "Not found"},
            {"asset_key": "data", "error": "Permission denied"},
        ]
        error = DeleteError("Delete failed", item_id="item-1", failed_assets=failed)
        self.assertEqual(len(error.failed_assets), 2)
        self.assertIn("thumbnail", str(error))
        self.assertIn("data", str(error))


if __name__ == "__main__":
    unittest.main()

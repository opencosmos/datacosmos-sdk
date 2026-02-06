"""Tests for normalize_collection_license function."""

import pytest

from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.validation.license import normalize_collection_license


class TestNormalizeCollectionLicense:
    """Tests for normalize_collection_license function."""

    def test_valid_spdx_license(self):
        """Test normalization of valid SPDX licenses."""
        result, warning = normalize_collection_license("Apache-2.0")
        assert result == "Apache-2.0"
        assert warning is None

    def test_deprecated_proprietary(self):
        """Test mapping of deprecated 'proprietary' license."""
        result, warning = normalize_collection_license("proprietary")
        assert result == "other"
        assert "deprecated" in warning
        assert "proprietary" in warning

    def test_deprecated_various(self):
        """Test mapping of deprecated 'various' license."""
        result, warning = normalize_collection_license("various")
        assert result == "other"
        assert "deprecated" in warning

    def test_other_license(self):
        """Test 'other' license passes through."""
        result, warning = normalize_collection_license("other")
        assert result == "other"
        assert warning is None

    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed."""
        result, warning = normalize_collection_license("  MIT  ")
        assert result == "MIT"
        assert warning is None

    def test_empty_license_raises(self):
        """Test that empty license raises error."""
        with pytest.raises(StacValidationError, match="license is required"):
            normalize_collection_license("")

    def test_whitespace_only_raises(self):
        """Test that whitespace-only license raises error."""
        with pytest.raises(StacValidationError, match="license is required"):
            normalize_collection_license("   ")

    def test_invalid_license_raises(self):
        """Test that invalid license raises error."""
        with pytest.raises(StacValidationError, match="must be an SPDX identifier"):
            normalize_collection_license("not a valid license")

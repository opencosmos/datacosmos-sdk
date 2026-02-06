"""Tests for ensure_license_links function."""

import pytest

from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.validation.license import ensure_license_links


class TestEnsureLicenseLinks:
    """Tests for ensure_license_links function."""

    def test_other_license_with_link_passes(self):
        """Test that 'other' license with license link passes."""
        links = [{"rel": "license", "href": "https://example.com/license"}]
        ensure_license_links("other", links)  # Should not raise

    def test_other_license_without_link_raises(self):
        """Test that 'other' license without license link raises error."""
        links = [{"rel": "self", "href": "https://example.com/self"}]
        with pytest.raises(StacValidationError, match="license links are required"):
            ensure_license_links("other", links)

    def test_license_ref_without_link_raises(self):
        """Test that LicenseRef- without license link raises error."""
        links = []
        with pytest.raises(StacValidationError, match="license links are required"):
            ensure_license_links("LicenseRef-Custom", links)

    def test_standard_license_without_link_passes(self):
        """Test that standard license without link passes."""
        links = []
        ensure_license_links("MIT", links)  # Should not raise

    def test_empty_href_not_valid(self):
        """Test that empty href is not considered a valid license link."""
        links = [{"rel": "license", "href": ""}]
        with pytest.raises(StacValidationError, match="license links are required"):
            ensure_license_links("other", links)

    def test_case_insensitive_rel(self):
        """Test that rel matching is case-insensitive."""
        links = [{"rel": "LICENSE", "href": "https://example.com/license"}]
        ensure_license_links("other", links)  # Should not raise

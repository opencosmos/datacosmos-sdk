"""Unit tests for STAC 1.1.0 license validation with SPDX expressions.

STAC 1.1.0 updated license handling:
- Support for SPDX expressions (e.g., "Apache-2.0 OR MIT")
- Deprecated "proprietary" and "various" in favor of "other"
- License links required when license is "other" or "LicenseRef-*"
Spec: https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#license
"""

import unittest

from datacosmos.exceptions.stac_validation_error import StacValidationError
from datacosmos.stac.validation.license import (
    ensure_license_links,
    is_valid_spdx_expression,
    normalize_collection_license,
)


class TestStac110LicenseValidation(unittest.TestCase):
    """Tests for STAC 1.1.0 license validation with SPDX expressions."""

    def test_spdx_identifier_valid(self):
        """Test that a simple SPDX identifier is valid."""
        normalized, warning = normalize_collection_license("Apache-2.0")

        self.assertEqual(normalized, "Apache-2.0")
        self.assertIsNone(warning)

    def test_spdx_expression_valid(self):
        """Test that SPDX compound expressions are valid."""
        normalized, warning = normalize_collection_license("Apache-2.0 OR MIT")

        self.assertEqual(normalized, "Apache-2.0 OR MIT")
        self.assertIsNone(warning)

    def test_spdx_expression_with_and(self):
        """Test that SPDX AND expressions are valid."""
        normalized, warning = normalize_collection_license("GPL-3.0-only AND Apache-2.0")

        self.assertEqual(normalized, "GPL-3.0-only AND Apache-2.0")
        self.assertIsNone(warning)

    def test_spdx_expression_with_exception(self):
        """Test that SPDX WITH exception clauses are valid."""
        self.assertTrue(
            is_valid_spdx_expression("GPL-2.0-only WITH Classpath-exception-2.0")
        )

    def test_proprietary_deprecated_maps_to_other(self):
        """Test that deprecated 'proprietary' value maps to 'other' with warning."""
        normalized, warning = normalize_collection_license("proprietary")

        self.assertEqual(normalized, "other")
        self.assertIsNotNone(warning)
        self.assertIn("deprecated", warning)

    def test_various_deprecated_maps_to_other(self):
        """Test that deprecated 'various' value maps to 'other' with warning."""
        normalized, warning = normalize_collection_license("various")

        self.assertEqual(normalized, "other")
        self.assertIsNotNone(warning)
        self.assertIn("deprecated", warning)

    def test_license_other_valid(self):
        """Test that 'other' is a valid license value."""
        normalized, warning = normalize_collection_license("other")

        self.assertEqual(normalized, "other")
        self.assertIsNone(warning)

    def test_license_other_requires_link(self):
        """Test that 'other' license requires a license link."""
        links = [{"rel": "self", "href": "https://example.com/collection"}]

        with self.assertRaises(StacValidationError) as context:
            ensure_license_links("other", links)

        self.assertIn("license links are required", str(context.exception))

    def test_license_other_with_link_valid(self):
        """Test that 'other' license with link passes validation."""
        links = [
            {"rel": "license", "href": "https://example.com/license.html"},
        ]

        # Should not raise
        ensure_license_links("other", links)

    def test_license_ref_requires_link(self):
        """Test that LicenseRef-* licenses require a license link."""
        links = [{"rel": "self", "href": "https://example.com/collection"}]

        with self.assertRaises(StacValidationError) as context:
            ensure_license_links("LicenseRef-Custom", links)

        self.assertIn("license links are required", str(context.exception))

    def test_spdx_license_no_link_required(self):
        """Test that standard SPDX licenses don't require a link."""
        links = []

        # Should not raise
        ensure_license_links("Apache-2.0", links)

    def test_empty_license_raises_error(self):
        """Test that empty license raises StacValidationError."""
        with self.assertRaises(StacValidationError) as context:
            normalize_collection_license("")

        self.assertIn("required", str(context.exception))


if __name__ == "__main__":
    unittest.main()

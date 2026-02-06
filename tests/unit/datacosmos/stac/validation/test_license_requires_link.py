"""Tests for license_requires_link function."""

from datacosmos.stac.validation.license import license_requires_link


class TestLicenseRequiresLink:
    """Tests for license_requires_link function."""

    def test_other_requires_link(self):
        """Test that 'other' license requires a link."""
        assert license_requires_link("other") is True

    def test_license_ref_requires_link(self):
        """Test that LicenseRef- licenses require a link."""
        assert license_requires_link("LicenseRef-Custom") is True
        assert license_requires_link("MIT OR LicenseRef-Proprietary") is True

    def test_standard_license_no_link_required(self):
        """Test that standard SPDX licenses don't require a link."""
        assert license_requires_link("MIT") is False
        assert license_requires_link("Apache-2.0") is False
        assert license_requires_link("GPL-3.0") is False

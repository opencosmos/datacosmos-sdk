"""Tests for is_valid_spdx_expression function."""

from datacosmos.stac.validation.license import is_valid_spdx_expression


class TestIsValidSpdxExpression:
    """Tests for is_valid_spdx_expression function."""

    def test_simple_license_identifiers(self):
        """Test simple SPDX license identifiers."""
        assert is_valid_spdx_expression("MIT") is True
        assert is_valid_spdx_expression("Apache-2.0") is True
        assert is_valid_spdx_expression("GPL-3.0") is True
        assert is_valid_spdx_expression("BSD-3-Clause") is True
        assert is_valid_spdx_expression("CC-BY-4.0") is True

    def test_or_later_suffix(self):
        """Test licenses with + suffix for 'or later' versions."""
        assert is_valid_spdx_expression("GPL-2.0+") is True
        assert is_valid_spdx_expression("LGPL-2.1+") is True
        assert is_valid_spdx_expression("GPL-3.0-or-later") is True

    def test_compound_expressions_with_and(self):
        """Test compound expressions using AND."""
        assert is_valid_spdx_expression("MIT AND Apache-2.0") is True
        assert is_valid_spdx_expression("GPL-2.0 AND BSD-3-Clause") is True

    def test_compound_expressions_with_or(self):
        """Test compound expressions using OR."""
        assert is_valid_spdx_expression("MIT OR Apache-2.0") is True
        assert is_valid_spdx_expression("GPL-2.0 OR MIT OR BSD-3-Clause") is True

    def test_with_clause(self):
        """Test expressions with WITH exception clause."""
        assert is_valid_spdx_expression("GPL-2.0 WITH Classpath-exception-2.0") is True
        assert is_valid_spdx_expression("Apache-2.0 WITH LLVM-exception") is True

    def test_parenthesized_expressions(self):
        """Test expressions with parentheses."""
        assert is_valid_spdx_expression("(MIT OR Apache-2.0)") is True
        assert is_valid_spdx_expression("(MIT AND Apache-2.0) OR GPL-3.0") is True
        assert is_valid_spdx_expression("MIT AND (Apache-2.0 OR GPL-3.0)") is True

    def test_license_ref(self):
        """Test LicenseRef- custom identifiers."""
        assert is_valid_spdx_expression("LicenseRef-Custom") is True
        assert is_valid_spdx_expression("LicenseRef-my-license-1.0") is True
        assert is_valid_spdx_expression("MIT OR LicenseRef-Proprietary") is True

    def test_document_ref(self):
        """Test DocumentRef- external document references."""
        assert is_valid_spdx_expression("DocumentRef-ext:LicenseRef-Custom") is True

    def test_complex_expression(self):
        """Test complex combined expressions."""
        assert is_valid_spdx_expression(
            "(MIT OR Apache-2.0) AND (GPL-2.0+ WITH Classpath-exception-2.0)"
        ) is True

    def test_invalid_expressions(self):
        """Test invalid SPDX expressions."""
        assert is_valid_spdx_expression("") is False
        assert is_valid_spdx_expression("   ") is False
        assert is_valid_spdx_expression("invalid license") is False  # space in identifier
        assert is_valid_spdx_expression("MIT AND") is False  # incomplete
        assert is_valid_spdx_expression("AND MIT") is False  # starts with operator
        assert is_valid_spdx_expression("(MIT") is False  # unclosed paren
        assert is_valid_spdx_expression("MIT)") is False  # unmatched paren
        assert is_valid_spdx_expression("MIT OR OR Apache-2.0") is False  # double operator

"""STAC 1.1.0 license validation utilities.

Provides utility functions for SPDX expression validation and license link requirements
as specified in STAC 1.1.0. These utilities can be used by consumers of the SDK to
validate collection license fields before submission.

Note: These validators are not automatically invoked by CollectionClient methods.
Users should call them explicitly when license validation is required.
"""

from datacosmos.exceptions.stac_validation_error import StacValidationError

# Deprecated license values that should be mapped to "other"
DEPRECATED_LICENSES = {
    "proprietary": "other",
    "various": "other",
}

# Link relation for license
LINK_REL_LICENSE = "license"


def normalize_collection_license(license_value: str) -> tuple[str, str | None]:
    """Normalize a collection license value according to STAC 1.1.0 rules.

    Args:
        license_value: The license string to normalize.

    Returns:
        A tuple of (normalized_license, deprecation_warning).
        The warning is None if no deprecation mapping occurred.

    Raises:
        StacValidationError: If the license is empty or invalid.
    """
    trimmed = license_value.strip() if license_value else ""

    if not trimmed:
        raise StacValidationError("license is required")

    lower = trimmed.lower()

    # Check for deprecated licenses
    if lower in DEPRECATED_LICENSES:
        replacement = DEPRECATED_LICENSES[lower]
        warning = f'license value "{license_value}" is deprecated; mapped to "{replacement}"'
        return replacement, warning

    if lower == "other":
        return "other", None

    # Validate as SPDX expression
    if not is_valid_spdx_expression(trimmed):
        raise StacValidationError(
            f'license value "{license_value}" must be an SPDX identifier, '
            'SPDX expression, or the string "other"'
        )

    return trimmed, None


def ensure_license_links(license_value: str, links: list[dict]) -> None:
    """Ensure license links are present when required.

    STAC 1.1.0 requires a link with rel="license" when the license is
    "other" or contains "LicenseRef-".

    Args:
        license_value: The normalized license string.
        links: List of link dictionaries.

    Raises:
        StacValidationError: If license links are required but missing.
    """
    if not license_requires_link(license_value):
        return

    for link in links:
        rel = link.get("rel", "")
        href = link.get("href", "")
        if rel.lower() == LINK_REL_LICENSE and href.strip():
            return

    raise StacValidationError(
        f'license links are required when license is "{license_value}"'
    )


def license_requires_link(license_value: str) -> bool:
    """Check if a license value requires a license link.

    Args:
        license_value: The license string to check.

    Returns:
        True if a license link is required, False otherwise.
    """
    if license_value == "other":
        return True
    return "LicenseRef-" in license_value


def is_valid_spdx_expression(value: str) -> bool:
    """Validate an SPDX license expression.

    Supports simple identifiers, compound expressions with AND/OR,
    WITH clauses, and LicenseRef- custom identifiers.

    Args:
        value: The SPDX expression to validate.

    Returns:
        True if the expression is valid, False otherwise.
    """
    tokens = _tokenize_spdx(value)
    if not tokens:
        return False

    parser = _SPDXParser(tokens)
    if not parser.parse_expression():
        return False

    return parser.at_end()


def _tokenize_spdx(value: str) -> list[str]:
    """Tokenize an SPDX expression into individual tokens.

    Args:
        value: The SPDX expression string.

    Returns:
        List of tokens.
    """
    tokens = []
    i = 0

    while i < len(value):
        ch = value[i]

        # Skip whitespace
        if ch in " \t\n\r":
            i += 1
            continue

        # Parentheses and + are single-character tokens
        if ch == "(":
            tokens.append("(")
            i += 1
            continue

        if ch == ")":
            tokens.append(")")
            i += 1
            continue

        if ch == "+":
            tokens.append("+")
            i += 1
            continue

        # Read identifier/keyword
        start = i
        while i < len(value):
            ch = value[i]
            if ch in " \t\n\r()+":
                break
            i += 1

        token = value[start:i]
        tokens.append(token)

    return tokens


class _SPDXParser:
    """Parser for SPDX license expressions."""

    def __init__(self, tokens: list[str]):
        """Initialize the parser with tokens.

        Args:
            tokens: List of tokens to parse.
        """
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str:
        """Return the current token without consuming it.

        Returns:
            The current token, or empty string if at end.
        """
        if self.pos >= len(self.tokens):
            return ""
        return self.tokens[self.pos]

    def at_end(self) -> bool:
        """Check if all tokens have been consumed.

        Returns:
            True if at end of tokens, False otherwise.
        """
        return self.pos >= len(self.tokens)

    def parse_expression(self) -> bool:
        """Parse an SPDX expression.

        Returns:
            True if parsing succeeded, False otherwise.
        """
        if not self.parse_term():
            return False

        while True:
            tok = self.peek()
            if tok in ("AND", "OR"):
                self.pos += 1
                if not self.parse_term():
                    return False
                continue
            break

        return True

    def parse_term(self) -> bool:
        """Parse a term (factor optionally followed by WITH clause).

        Returns:
            True if parsing succeeded, False otherwise.
        """
        if not self.parse_factor():
            return False

        if self.peek() == "WITH":
            self.pos += 1
            exception_id = self.peek()
            if not _is_license_identifier(exception_id):
                return False
            self.pos += 1

        return True

    def parse_factor(self) -> bool:
        """Parse a factor (identifier or parenthesized expression).

        Returns:
            True if parsing succeeded, False otherwise.
        """
        tok = self.peek()

        if not tok:
            return False

        if tok == "(":
            self.pos += 1
            if not self.parse_expression():
                return False
            if self.peek() != ")":
                return False
            self.pos += 1
            return True

        # Must be a license identifier
        if not _is_license_identifier(tok):
            return False

        self.pos += 1

        # Handle optional "+" suffix for "or later" versions
        if self.peek() == "+":
            self.pos += 1

        return True


def _is_license_identifier(token: str) -> bool:
    """Check if a token is a valid license identifier.

    Valid identifiers include:
    - Standard SPDX identifiers (alphanumeric with hyphens, dots, and underscores)
    - LicenseRef- custom identifiers
    - DocumentRef-...:LicenseRef-... external document references

    Args:
        token: The token to check.

    Returns:
        True if the token is a valid identifier, False otherwise.
    """
    if not token:
        return False

    # Keywords are not identifiers
    if token in ("AND", "OR", "WITH", "(", ")", "+"):
        return False

    # LicenseRef- and DocumentRef- are valid (may contain : for external refs)
    if token.startswith("LicenseRef-") or token.startswith("DocumentRef-"):
        return True

    # Standard SPDX identifier: alphanumeric, hyphens, dots, and underscores
    for ch in token:
        if not (ch.isalnum() or ch in "-._"):
            return False

    return True

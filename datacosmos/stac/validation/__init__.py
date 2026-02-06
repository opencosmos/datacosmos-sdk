"""STAC validation utilities.

This module provides utility functions for validating STAC metadata according to
STAC 1.1.0 specifications. These are helper utilities that can be called explicitly
by SDK consumers - they are not automatically invoked by the SDK's client methods.
"""

from datacosmos.stac.validation.license import (
    DEPRECATED_LICENSES,
    LINK_REL_LICENSE,
    ensure_license_links,
    is_valid_spdx_expression,
    license_requires_link,
    normalize_collection_license,
)

__all__ = [
    "DEPRECATED_LICENSES",
    "LINK_REL_LICENSE",
    "ensure_license_links",
    "is_valid_spdx_expression",
    "license_requires_link",
    "normalize_collection_license",
]

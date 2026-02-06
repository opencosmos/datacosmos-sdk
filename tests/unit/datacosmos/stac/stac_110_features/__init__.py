"""Unit tests demonstrating STAC 1.1.0 feature support in datacosmos-sdk.

This test package validates all key STAC 1.1.0 specification changes:
- Band object with common metadata (data_type, nodata, unit, statistics)
- Asset common metadata fields (keywords, bands, statistics)
- Link HTTP request metadata (method, headers, body)
- Absolute self-link validation requirement
- License validation with SPDX expressions
- Pystac roundtrip compatibility for 1.1.0 fields

Spec reference: https://github.com/radiantearth/stac-spec/releases/tag/v1.1.0
"""

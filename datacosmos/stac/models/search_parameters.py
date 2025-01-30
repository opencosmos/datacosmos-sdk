"""
Module defining the SearchParameters model for STAC API queries.

This module contains the `SearchParameters` model, which encapsulates
filtering criteria for searching STAC items, such as spatial, temporal,
and property-based filters.
"""

from typing import Optional, Union

from pydantic import BaseModel, Field, model_validator


class SearchParameters(BaseModel):
    """Encapsulates the parameters for the STAC search API with validation."""

    bbox: Optional[list[float]] = Field(
        None,
        description="Bounding box filter [minX, minY, maxX, maxY]. Optional six values for 3D bounding box.",
        example=[-180.0, -90.0, 180.0, 90.0],
    )
    datetime_range: Optional[str] = Field(
        None,
        alias="datetime",
        description=(
            "Temporal filter, either a single RFC 3339 datetime or an interval. "
            'Example: "2025-01-01T00:00:00Z/.."'
        ),
    )
    intersects: Optional[dict] = Field(
        None, description="GeoJSON geometry filter, e.g., a Polygon or Point."
    )
    ids: Optional[list[str]] = Field(
        None,
        description="Array of item IDs to filter by.",
        example=["item1", "item2"],
    )
    collections: Optional[list[str]] = Field(
        None,
        description="Array of collection IDs to filter by.",
        example=["collection1", "collection2"],
    )
    limit: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum number of items per page. Default: 10, Max: 10000.",
        example=10,
    )
    query: Optional[dict[str, dict[str, Union[str, int, float]]]] = Field(
        None,
        description="Additional property filters, e.g., { 'cloud_coverage': { 'lt': 10 } }.",
    )

    @model_validator(mode="before")
    def validate_bbox(cls, values):
        """Validate that the `bbox` field contains either 4 or 6 values."""
        bbox = values.get("bbox")
        if bbox and len(bbox) not in {4, 6}:
            raise ValueError("bbox must contain 4 or 6 values.")
        return values

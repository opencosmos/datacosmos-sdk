"""Query parameters for project item search."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectSearchParameters(BaseModel):
    """Query parameters for searching items within a project/scenario.

    This follows the STAC search parameters structure used by the project service.
    """

    ids: Optional[List[str]] = Field(
        None,
        description="Filter by specific item IDs",
    )
    collections: Optional[List[str]] = Field(
        None,
        description="Filter by specific collection IDs",
    )
    bbox: Optional[List[float]] = Field(
        None,
        description="Bounding box filter [west, south, east, north]",
    )
    datetime: Optional[str] = Field(
        None,
        description="Temporal filter (single datetime or interval)",
        examples=["2024-01-01T00:00:00Z/2024-12-31T23:59:59Z"],
    )
    intersects: Optional[Dict[str, Any]] = Field(
        None,
        description="GeoJSON geometry to intersect with",
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum number of items to return",
        ge=1,
    )
    query: Optional[Dict[str, Any]] = Field(
        None,
        description="Property-based query constraints",
    )

    def to_request_body(self) -> dict:
        """Convert parameters to request body for the search endpoint."""
        body = {}

        if self.ids is not None:
            body["ids"] = self.ids
        if self.collections is not None:
            body["collections"] = self.collections
        if self.bbox is not None:
            body["bbox"] = self.bbox
        if self.datetime is not None:
            body["datetime"] = self.datetime
        if self.intersects is not None:
            body["intersects"] = self.intersects
        if self.limit is not None:
            body["limit"] = self.limit
        if self.query is not None:
            body["query"] = self.query

        return body

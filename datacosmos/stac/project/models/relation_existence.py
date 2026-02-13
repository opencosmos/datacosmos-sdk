"""Model for relation existence response from project contains check."""

from typing import Optional

from pydantic import BaseModel, Field


class RelationExistence(BaseModel):
    """Response indicating whether a collection/item pair exists in a project."""

    collection: str = Field(..., description="Collection ID of the catalog item")
    item: str = Field(..., description="Item ID within the collection")
    relation: Optional[str] = Field(
        None, description="Relation ID if the item exists in the project"
    )
    exists: bool = Field(..., description="Whether the item exists in the project")

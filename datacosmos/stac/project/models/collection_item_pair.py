"""Model for collection/item pair used in project contains check."""

from pydantic import BaseModel, Field


class CollectionItemPair(BaseModel):
    """A pair of collection ID and item ID for checking existence in a project."""

    collection: str = Field(..., description="Collection ID of the catalog item")
    item: str = Field(..., description="Item ID within the collection")

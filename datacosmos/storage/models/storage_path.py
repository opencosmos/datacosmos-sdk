"""Represents a structured storage path for a file in DataCosmos storage."""

from pydantic import BaseModel, Field


class StoragePath(BaseModel):
    """Represents a structured storage path for a file in DataCosmos storage."""

    collection_id: str = Field(..., min_length=1, description="ID of the collection.")
    item_id: str = Field(..., min_length=1, description="ID of the STAC item.")
    filename: str = Field(
        ..., min_length=1, description="Filename of the uploaded file."
    )

    def as_url_path(self) -> str:
        """Generate the structured storage URL path."""
        return f"{self.collection_id}/{self.item_id}/{self.filename}"

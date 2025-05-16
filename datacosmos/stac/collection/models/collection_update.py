"""Represents a structured update model for STAC collections.

Allows partial updates where only the provided fields are modified.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pystac import Extent, Link, Provider, Summaries


class CollectionUpdate(BaseModel):
    """Represents a structured update model for STAC collections.

    Allows partial updates where only the provided fields are modified.
    """

    model_config = {"arbitrary_types_allowed": True}

    title: Optional[str] = Field(None, description="Title of the STAC collection.")
    description: Optional[str] = Field(
        None, description="Description of the collection."
    )
    keywords: Optional[List[str]] = Field(
        None, description="List of keywords associated with the collection."
    )
    license: Optional[str] = Field(None, description="Collection license information.")
    providers: Optional[List[Provider]] = Field(
        None, description="List of data providers."
    )
    extent: Optional[Extent] = Field(
        None, description="Spatial and temporal extent of the collection."
    )
    summaries: Optional[Summaries] = Field(
        None, description="Summaries for the collection."
    )
    links: Optional[List[Link]] = Field(
        None, description="List of links associated with the collection."
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model into a dictionary, excluding `None` values.

        Returns:
            Dict[str, Any]: Dictionary representation of the update payload.
        """
        return self.model_dump(by_alias=True, exclude_none=True)

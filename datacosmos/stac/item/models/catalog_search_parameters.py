"""Query parameters for catalog search."""

from datetime import datetime, timedelta
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from datacosmos.stac.constants.satellite_name_mapping import SATELLITE_NAME_MAPPING
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.enums.product_type import ProductType
from datacosmos.stac.enums.season import Season


class CatalogSearchParameters(BaseModel):
    """Query parameters for catalog search."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    seasons: Optional[List[Season]] = None
    satellite: Optional[List[str]] = None
    product_type: Optional[List[ProductType]] = None
    processing_level: Optional[List[ProcessingLevel]] = None
    collections: Optional[list[str]] = Field(
        None,
        description="Array of collection IDs to filter by.",
        example=["collection1", "collection2"],
    )

    # --- Field Validators ---

    @field_validator("seasons", mode="before")
    @classmethod
    def parse_seasons(cls, value):
        """Parses seasons values into a list of Season object."""
        if value is None:
            return None
        return [Season(v) if not isinstance(v, Season) else v for v in value]

    @field_validator("product_type", mode="before")
    @classmethod
    def parse_product_types(cls, value):
        """Parses product types values into a list of ProductType object."""
        if value is None:
            return None
        return [ProductType(v) if not isinstance(v, ProductType) else v for v in value]

    @field_validator("processing_level", mode="before")
    @classmethod
    def parse_processing_levels(cls, value):
        """Parses processing levels values into a list of ProcessingLevel object."""
        if value is None:
            return None
        return [
            ProcessingLevel(v) if not isinstance(v, ProcessingLevel) else v
            for v in value
        ]

    @field_validator("start_date", mode="before")
    @classmethod
    def parse_start_date(cls, value: Any) -> Optional[str]:
        """Validations on start_date."""
        if value is None:
            return None
        try:
            dt = datetime.strptime(value, "%m/%d/%Y")
        except Exception as e:
            raise ValueError(
                "Invalid start_date format. Use mm/dd/yyyy (e.g., 05/15/2024)"
            ) from e
        if dt < datetime(2015, 5, 15):
            raise ValueError("Date must be 5/15/2015 or later.")
        return dt.isoformat() + "Z"

    @field_validator("end_date", mode="before")
    @classmethod
    def parse_end_date(cls, value: Any) -> Optional[str]:
        """Validations on end_date."""
        if value is None:
            return None
        try:
            dt = datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            raise ValueError(
                "Invalid end_date format. Use mm/dd/yyyy (e.g., 05/15/2024)"
            )

        if dt < datetime(2015, 5, 15):
            raise ValueError("Date must be 5/15/2015 or later.")
        dt = dt + timedelta(days=1) - timedelta(milliseconds=1)
        return dt.isoformat() + "Z"

    # --- Model Validator ---

    @model_validator(mode="after")
    def validate_date_range(self) -> "CatalogSearchParameters":
        """Checks if end_date is after the start_date."""
        if self.start_date and self.end_date:
            start_dt = datetime.fromisoformat(self.start_date.rstrip("Z"))
            end_dt = datetime.fromisoformat(self.end_date.rstrip("Z"))
            if start_dt > end_dt:
                raise ValueError("end_date cannot be before start_date.")
        return self

    # --- Query Mapper ---

    def to_query(self) -> dict:
        """Map user-friendly input to STAC query structure."""
        query = {}

        if self.start_date or self.end_date:
            query["datetime"] = {"gte": self.start_date, "lte": self.end_date}

        if self.seasons:
            query["opencosmos:season"] = {
                "in": [seasons.value for seasons in self.seasons]
            }

        if self.product_type:
            query["opencosmos:product_type"] = {
                "in": [product_type.value for product_type in self.product_type]
            }

        if self.processing_level:
            query["processing:level"] = {
                "in": [
                    processing_level.value for processing_level in self.processing_level
                ]
            }

        if self.satellite:
            cospars = [
                SATELLITE_NAME_MAPPING[ui]
                for ui in self.satellite
                if ui in SATELLITE_NAME_MAPPING
            ]
            query["sat:platform_international_designator"] = {"in": cospars}

        return query

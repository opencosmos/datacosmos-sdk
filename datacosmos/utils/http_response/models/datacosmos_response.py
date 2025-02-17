"""Structured response for Datacosmos handling multiple API errors."""

from pydantic import BaseModel

from datacosmos.utils.http_response.models.datacosmos_error import DatacosmosError


class DatacosmosResponse(BaseModel):
    """Structured response for Datacosmos handling multiple API errors."""

    errors: list[DatacosmosError]

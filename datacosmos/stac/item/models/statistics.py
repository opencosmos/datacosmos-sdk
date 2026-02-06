"""Model representing STAC 1.1.0 statistics metadata."""

from pydantic import BaseModel, ConfigDict


class Statistics(BaseModel):
    """Model representing STAC 1.1.0 statistics metadata.

    Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#statistics-object
    """

    model_config = ConfigDict(extra="allow")

    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    stddev: float | None = None
    count: int | None = None
    valid_percent: float | None = None

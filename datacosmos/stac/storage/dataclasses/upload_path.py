"""Dataclass for retrieving the upload path of a file."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import structlog

from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem

logger = structlog.get_logger()


@dataclass
class UploadPath:
    """Dataclass for retrieving the upload path of a file."""

    mission: str
    level: ProcessingLevel
    day: int
    month: int
    year: int
    id: str
    path: str

    def __str__(self):
        """Return a human-readable string representation of the Path."""
        path = f"full/{self.mission.lower()}/{self.level.value.lower()}/{self.year:02}/{self.month:02}/{self.day:02}/{self.id}/{self.path}"
        return path.removesuffix("/")

    @classmethod
    def from_item_path(
        cls, item: DatacosmosItem, mission: str, item_path: str
    ) -> "Path":
        """Create a Path instance from a DatacosmosItem and a path."""
        dt = datetime.strptime(item.properties["datetime"], "%Y-%m-%dT%H:%M:%SZ")
        path = UploadPath(
            mission=mission,
            level=ProcessingLevel(item.properties["processing:level"].lower()),
            day=dt.day,
            month=dt.month,
            year=dt.year,
            id=item.id,
            path=item_path,
        )
        return cls(**path.__dict__)

    @classmethod
    def from_path(cls, path: str) -> "Path":
        """Create a Path instance from a string path."""
        parts = path.split("/")
        if len(parts) < 7:
            raise ValueError(f"Invalid path {path}")
        return cls(
            mission=parts[0],
            level=ProcessingLevel(parts[1]),
            day=int(parts[4]),
            month=int(parts[3]),
            year=int(parts[2]),
            id=parts[5],
            path="/".join(parts[6:]),
        )

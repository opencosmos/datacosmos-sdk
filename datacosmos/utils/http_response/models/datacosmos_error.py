"""Structured API error message for Datacosmos."""

from pydantic import BaseModel


class DatacosmosError(BaseModel):
    """Structured API error message for Datacosmos."""

    message: str
    field: str | None = None
    type: str | None = None
    source: str | None = None
    trace_id: str | None = None

    def human_readable(self) -> str:
        """Formats the error message into a readable format."""
        msg = self.message
        if self.type:
            msg += f" (type: {self.type})"
        if self.field:
            msg += f" (field: {self.field})"
        if self.source:
            msg += f" (source: {self.source})"
        if self.trace_id:
            msg += f" (trace_id: {self.trace_id})"
        return msg

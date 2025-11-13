"""Exception raised for HTTP request failures."""
from datacosmos.exceptions.datacosmos_error import DatacosmosError


class HTTPError(DatacosmosError):
    """Exception raised for HTTP request failures that wraps status codes."""

    pass

"""Base exception class for all Datacosmos SDK exceptions."""

from typing import Optional

from requests import Response
from requests.exceptions import RequestException


class DatacosmosError(RequestException):
    """Base exception class for all Datacosmos SDK exceptions."""

    def __init__(self, message: str, response: Optional[Response] = None):
        """Initialize DatacosmosError.

        Args:
            message (str): The error message.
            response (Optional[Response]): The HTTP response object, if available.
        """
        self.response = response
        self.status_code = response.status_code if response else None
        self.details = response.text if response else None
        full_message = (
            f"{message} (Status: {self.status_code}, Details: {self.details})"
            if response
            else message
        )
        super().__init__(full_message)

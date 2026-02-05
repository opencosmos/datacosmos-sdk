"""Validates an API response and raises a DatacosmosError if an error occurs."""

from pydantic import ValidationError
from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.utils.http_response.models.datacosmos_response import DatacosmosResponse


def check_api_response(response: Response) -> None:
    """Validates an API response and raises a DatacosmosError if an error occurs.

    Args:
        response (requests.Response): The response object to validate.

    Raises:
        DatacosmosError: If the response status code indicates an error (>= 400).
            The error message will include structured error details if available,
            or the raw response body otherwise.
    """
    if 200 <= response.status_code < 400:
        return

    # Capture request context for error messages
    request_url = response.url if hasattr(response, "url") else "unknown"
    request_method = (
        response.request.method if hasattr(response, "request") else "unknown"
    )

    try:
        parsed_response = DatacosmosResponse.model_validate_json(response.text)
        msg = parsed_response.errors[0].human_readable()
        if len(parsed_response.errors) > 1:
            msg = "\n  * " + "\n  * ".join(
                error.human_readable() for error in parsed_response.errors
            )
        # DatacosmosError will append status code and response details automatically
        raise DatacosmosError(
            f"API error during {request_method} {request_url}: {msg}",
            response=response,
        )

    except ValidationError:
        # Response doesn't match expected error schema
        # DatacosmosError will append status code and response details automatically
        raise DatacosmosError(
            f"API error during {request_method} {request_url}",
            response=response,
        )

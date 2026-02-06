"""Validates an API response and raises a DatacosmosError if an error occurs."""

from pydantic import ValidationError
from requests import Response

from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.utils.http_response.models.datacosmos_response import DatacosmosResponse


def check_api_response(response: Response) -> None:
    """Validates an API response and raises a DatacosmosError if an error occurs.

    Args:
        resp (requests.Response): The response object.

    Raises:
        DatacosmosError: If the response status code indicates an error.
    """
    if 200 <= response.status_code < 400:
        return

    try:
        response = DatacosmosResponse.model_validate_json(response.text)
        msg = response.errors[0].human_readable()
        if len(response.errors) > 1:
            msg = "\n  * " + "\n  * ".join(
                error.human_readable() for error in response.errors
            )
        raise DatacosmosError(msg, response=response)

    except ValidationError:
        raise DatacosmosError(
            f"HTTP {response.status_code}: {response.text}", response=response
        )

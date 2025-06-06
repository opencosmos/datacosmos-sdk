"""No authentication configuration.

This is used when running scripts in tests.
"""

from typing import Literal

from pydantic import BaseModel


class NoAuthenticationConfig(BaseModel):
    """No authentication configuration.

    This is used when running scripts in tests.
    """

    type: Literal["none"]

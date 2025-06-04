"""Module for configuring machine-to-machine (M2M) authentication.

Used when running scripts in the cluster that require automated authentication
without user interaction.
"""

from typing import Literal

from pydantic import BaseModel, Field


class M2MAuthenticationConfig(BaseModel):
    """Configuration for machine-to-machine authentication.

    This is used when running scripts in the cluster that require authentication
    with client credentials.
    """

    DEFAULT_TYPE: Literal["m2m"] = "m2m"
    DEFAULT_TOKEN_URL: str = "https://login.open-cosmos.com/oauth/token"
    DEFAULT_AUDIENCE: str = "https://beeapp.open-cosmos.com"

    type: Literal["m2m"] = Field(default=DEFAULT_TYPE)
    client_id: str
    token_url: str = Field(default=DEFAULT_TOKEN_URL)
    audience: str = Field(default=DEFAULT_AUDIENCE)
    client_secret: str

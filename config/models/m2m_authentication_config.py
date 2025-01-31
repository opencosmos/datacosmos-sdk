"""Module for configuring machine-to-machine (M2M) authentication.

Used when running scripts in the cluster that require automated authentication
without user interaction.
"""

from typing import Literal

from pydantic import BaseModel


class M2MAuthenticationConfig(BaseModel):
    """Configuration for machine-to-machine authentication.

    This is used when running scripts in the cluster that require authentication
    with client credentials.
    """

    type: Literal["m2m"]
    client_id: str
    token_url: str
    audience: str
    # Some infrastructure deployments do not require a client secret.
    client_secret: str = ""
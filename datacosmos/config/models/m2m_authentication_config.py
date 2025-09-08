"""Module for configuring machine-to-machine (M2M) authentication.

Used when running scripts in the cluster that require automated authentication
without user interaction.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class M2MAuthenticationConfig(BaseModel):
    """Configuration for machine-to-machine authentication.

    This is used when running scripts in the cluster that require authentication
    with client credentials. Required fields are enforced by `normalize_authentication` after merge.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["m2m"] = "m2m"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    audience: Optional[str] = None

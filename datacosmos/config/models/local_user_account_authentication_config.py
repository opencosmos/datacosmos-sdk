"""Configuration for local user account authentication.

When this is chosen, the user will be prompted to log in using their OPS credentials.
This will be used for running scripts locally.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class LocalUserAccountAuthenticationConfig(BaseModel):
    """Configuration for local user account authentication.

    When this is chosen, the user will be prompted to log in using their OPS credentials.
    This will be used for running scripts locally. Required fields are enforced by `normalize_authentication` after merge.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["local"] = "local"
    client_id: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    redirect_port: Optional[int] = None
    scopes: Optional[str] = None
    audience: Optional[str] = None
    cache_file: Optional[str] = None

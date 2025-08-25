"""Configuration for local user account authentication.

When this is chosen, the user will be prompted to log in using their OPS credentials.
This will be used for running scripts locally.
"""

from typing import Literal, Optional

from pydantic import BaseModel


class LocalUserAccountAuthenticationConfig(BaseModel):
    """Configuration for local user account authentication.

    When this is chosen, the user will be prompted to log in using their OPS credentials.
    This will be used for running scripts locally.
    """

    type: Literal["local"] = "local"
    client_id: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    redirect_port: Optional[int] = None
    scopes: Optional[str] = None
    audience: Optional[str] = None
    cache_file: Optional[str] = None

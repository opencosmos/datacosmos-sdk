"""Configuration for local user account authentication.

When this is chosen, the user will be prompted to log in using their OPS credentials.
This will be used for running scripts locally.
"""

from typing import Literal

from pydantic import BaseModel


class LocalUserAccountAuthenticationConfig(BaseModel):
    """Configuration for local user account authentication.

    When this is chosen, the user will be prompted to log in using their OPS credentials.
    This will be used for running scripts locally.
    """

    type: Literal["local"]
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_port: int
    scopes: str
    audience: str
    cache_file: str

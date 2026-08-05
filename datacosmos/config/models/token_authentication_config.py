"""User-token authentication configuration.

Reads a pre-obtained bearer token from an environment variable at client
construction. Intended for environments where a per-user access token is
injected into the process (e.g. JupyterHub single-user servers and the
custom-app papermill runner), so notebooks authenticate as the logged-in user
without handling the token explicitly.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from datacosmos.config.constants import DEFAULT_USER_TOKEN_ENV_VAR


class TokenAuthenticationConfig(BaseModel):
    """Configuration for pre-obtained bearer-token authentication from the environment.

    The token itself is not stored here; it is read from the environment
    variable named by ``token_env_var`` when the client is constructed.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["token"] = "token"
    token_env_var: str = DEFAULT_USER_TOKEN_ENV_VAR

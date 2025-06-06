"""Authentication configuration options."""

from typing import Union

from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.no_authentication_config import NoAuthenticationConfig

AuthenticationConfig = Union[
    NoAuthenticationConfig,
    LocalUserAccountAuthenticationConfig,
    M2MAuthenticationConfig,
]

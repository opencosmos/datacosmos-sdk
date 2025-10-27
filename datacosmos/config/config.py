"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from datacosmos.config.auth.factory import normalize_authentication, parse_auth_config
from datacosmos.config.constants import (
    DEFAULT_CONFIG_YAML,
    DEFAULT_STAC,
    DEFAULT_STORAGE,
)
from datacosmos.config.loaders.yaml_source import yaml_settings_source
from datacosmos.config.models.authentication_config import AuthenticationConfig
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.url import URL


class Config(BaseSettings):
    """Centralized configuration for the Datacosmos SDK."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="allow",
    )

    authentication: Optional[AuthenticationConfig] = None

    stac: URL = Field(default_factory=lambda: URL(**DEFAULT_STAC))
    datacosmos_cloud_storage: URL = Field(
        default_factory=lambda: URL(**DEFAULT_STORAGE)
    )
    datacosmos_public_cloud_storage: URL = Field(
        default_factory=lambda: URL(**DEFAULT_STORAGE)
    )

    @classmethod
    def settings_customise_sources(cls, *args, **kwargs):
        """Sets customised sources."""
        init_settings = kwargs.get("init_settings") or (
            args[1] if len(args) > 1 else None
        )
        env_settings = kwargs.get("env_settings") or (
            args[2] if len(args) > 2 else None
        )
        dotenv_settings = kwargs.get("dotenv_settings") or (
            args[3] if len(args) > 3 else None
        )
        file_secret_settings = kwargs.get("file_secret_settings") or (
            args[4] if len(args) > 4 else None
        )

        sources = [
            init_settings,
            yaml_settings_source(DEFAULT_CONFIG_YAML),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        ]
        return tuple(s for s in sources if s is not None)

    @field_validator("authentication", mode="before")
    @classmethod
    def _parse_authentication(cls, raw):
        if raw is None:
            return None
        if isinstance(
            raw, (M2MAuthenticationConfig, LocalUserAccountAuthenticationConfig)
        ):
            return raw
        if isinstance(raw, dict):
            return parse_auth_config(raw)
        return raw

    @field_validator("authentication", mode="after")
    @classmethod
    def _validate_authentication(cls, auth: Optional[AuthenticationConfig]):
        return normalize_authentication(auth)

"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from datacosmos.config.constants import (
    DEFAULT_CONFIG_YAML,
    DEFAULT_STAC,
    DEFAULT_STORAGE,
)
from datacosmos.config.loaders.yaml_source import yaml_settings_source
from datacosmos.config.auth.factory import normalize_authentication
from datacosmos.config.models.authentication_config import AuthenticationConfig
from datacosmos.config.models.url import URL


class Config(BaseSettings):
    """Centralized configuration for the Datacosmos SDK."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="allow",
    )

    authentication: Optional[AuthenticationConfig] = None
    stac: URL | None = None
    datacosmos_cloud_storage: URL | None = None
    datacosmos_public_cloud_storage: URL | None = None

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (
            init_settings,
            yaml_settings_source(DEFAULT_CONFIG_YAML),
            env_settings,
            file_secret_settings,
        )

    # --- Validators ---

    @field_validator("authentication", mode="after")
    @classmethod
    def _validate_authentication(cls, auth: Optional[AuthenticationConfig]):
        return normalize_authentication(auth)

    @field_validator("stac", mode="before")
    @classmethod
    def _default_stac(cls, value: URL | None) -> URL:
        return value or URL(**DEFAULT_STAC)

    @field_validator("datacosmos_cloud_storage", mode="before")
    @classmethod
    def _default_cloud_storage(cls, value: URL | None) -> URL:
        return value or URL(**DEFAULT_STORAGE)

    @field_validator("datacosmos_public_cloud_storage", mode="before")
    @classmethod
    def _default_public_cloud_storage(cls, value: URL | None) -> URL:
        return value or URL(**DEFAULT_STORAGE)
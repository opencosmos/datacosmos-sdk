"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from datacosmos.config.auth.factory import normalize_authentication, parse_auth_config
from datacosmos.config.constants import DEFAULT_CONFIG_YAML, DEFAULT_STORAGE_EXTERNAL
from datacosmos.config.environment import (
    get_default_project,
    get_default_stac,
    get_default_storage,
    is_running_in_opencosmos_cluster,
)
from datacosmos.config.loaders.yaml_source import yaml_settings_source
from datacosmos.config.models.authentication_config import AuthenticationConfig
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.config.models.no_authentication_config import NoAuthenticationConfig
from datacosmos.config.models.token_authentication_config import (
    TokenAuthenticationConfig,
)
from datacosmos.config.models.url import URL


class Config(BaseSettings):
    """Centralized configuration for the Datacosmos SDK."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="allow",
    )

    authentication: Optional[AuthenticationConfig] = None

    stac: URL = Field(default_factory=lambda: URL(**get_default_stac()))
    datacosmos_cloud_storage: URL = Field(
        default_factory=lambda: URL(**get_default_storage())
    )
    datacosmos_public_cloud_storage: URL = Field(
        default_factory=lambda: URL(**DEFAULT_STORAGE_EXTERNAL)
    )
    project: URL = Field(default_factory=lambda: URL(**get_default_project()))

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

    @model_validator(mode="after")
    def _default_public_storage_from_storage(self):
        """Mirror datacosmos_cloud_storage unless public storage is set explicitly.

        Outside the cluster datacosmos_cloud_storage is the external,
        per-environment URL, so it is also the correct public URL. Inside the
        cluster datacosmos_cloud_storage resolves to an internal service URL
        that is not publicly reachable, so the external default is kept there.
        """
        if (
            "datacosmos_public_cloud_storage" not in self.model_fields_set
            and not is_running_in_opencosmos_cluster()
        ):
            self.datacosmos_public_cloud_storage = (
                self.datacosmos_cloud_storage.model_copy()
            )
        return self

    @field_validator("authentication", mode="before")
    @classmethod
    def _parse_authentication(cls, raw):
        if raw is None:
            return None
        if isinstance(
            raw,
            (
                M2MAuthenticationConfig,
                LocalUserAccountAuthenticationConfig,
                NoAuthenticationConfig,
                TokenAuthenticationConfig,
            ),
        ):
            return raw
        if isinstance(raw, dict):
            return parse_auth_config(raw)
        return raw

    @field_validator("authentication", mode="after")
    @classmethod
    def _validate_authentication(cls, auth: Optional[AuthenticationConfig]):
        return normalize_authentication(auth)

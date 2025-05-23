"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

import os
from typing import ClassVar, Optional

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.models.m2m_authentication_config import M2MAuthenticationConfig
from config.models.url import URL


class Config(BaseSettings):
    """Centralized configuration for the Datacosmos SDK."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="allow",
    )

    authentication: Optional[M2MAuthenticationConfig] = None
    stac: Optional[URL] = None
    datacosmos_cloud_storage: Optional[URL] = None
    mission_id: int = 0

    DEFAULT_AUTH_TYPE: ClassVar[str] = "m2m"
    DEFAULT_AUTH_TOKEN_URL: ClassVar[str] = "https://login.open-cosmos.com/oauth/token"
    DEFAULT_AUTH_AUDIENCE: ClassVar[str] = "https://beeapp.open-cosmos.com"

    @classmethod
    def from_yaml(cls, file_path: str = "config/config.yaml") -> "Config":
        """Load configuration from a YAML file and override defaults.

        Args:
            file_path (str): The path to the YAML configuration file.

        Returns:
            Config: An instance of the Config class with loaded settings.
        """
        config_data: dict = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
                # Remove empty values from YAML to avoid overwriting with `None`
                config_data = {
                    key: value
                    for key, value in yaml_data.items()
                    if value not in [None, ""]
                }

        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config: An instance of the Config class with settings loaded from environment variables.
        """
        authentication_config = M2MAuthenticationConfig(
            type=os.getenv("OC_AUTH_TYPE", cls.DEFAULT_AUTH_TYPE),
            client_id=os.getenv("OC_AUTH_CLIENT_ID"),
            client_secret=os.getenv("OC_AUTH_CLIENT_SECRET"),
            token_url=os.getenv("OC_AUTH_TOKEN_URL", cls.DEFAULT_AUTH_TOKEN_URL),
            audience=os.getenv("OC_AUTH_AUDIENCE", cls.DEFAULT_AUTH_AUDIENCE),
        )

        stac_config = URL(
            protocol=os.getenv("OC_STAC_PROTOCOL", "https"),
            host=os.getenv("OC_STAC_HOST", "app.open-cosmos.com"),
            port=int(os.getenv("OC_STAC_PORT", "443")),
            path=os.getenv("OC_STAC_PATH", "/api/data/v0/stac"),
        )

        datacosmos_cloud_storage_config = URL(
            protocol=os.getenv("DC_CLOUD_STORAGE_PROTOCOL", "https"),
            host=os.getenv("DC_CLOUD_STORAGE_HOST", "app.open-cosmos.com"),
            port=int(os.getenv("DC_CLOUD_STORAGE_PORT", "443")),
            path=os.getenv("DC_CLOUD_STORAGE_PATH", "/api/data/v0/storage"),
        )

        return cls(
            authentication=authentication_config,
            stac=stac_config,
            datacosmos_cloud_storage=datacosmos_cloud_storage_config,
            mission_id=int(os.getenv("MISSION_ID", "0")),
            environment=os.getenv("ENVIRONMENT", "test"),
        )

    @field_validator("authentication", mode="before")
    @classmethod
    def validate_authentication(
        cls, auth_data: Optional[dict]
    ) -> M2MAuthenticationConfig:
        """Ensure authentication is provided and apply defaults.

        Args:
            auth_data (Optional[dict]): The authentication config as a dictionary.

        Returns:
            M2MAuthenticationConfig: The validated authentication configuration.

        Raises:
            ValueError: If authentication is missing or required fields are not set.
        """
        if not auth_data:
            return cls.apply_auth_defaults(M2MAuthenticationConfig())

        auth = cls.parse_auth_config(auth_data)
        auth = cls.apply_auth_defaults(auth)

        cls.check_required_auth_fields(auth)
        return auth

    @staticmethod
    def apply_auth_defaults(auth: M2MAuthenticationConfig) -> M2MAuthenticationConfig:
        """Apply default authentication values if they are missing."""
        auth.type = auth.type or Config.DEFAULT_AUTH_TYPE
        auth.token_url = auth.token_url or Config.DEFAULT_AUTH_TOKEN_URL
        auth.audience = auth.audience or Config.DEFAULT_AUTH_AUDIENCE
        return auth

    @classmethod
    def parse_auth_config(cls, auth_data: dict) -> M2MAuthenticationConfig:
        """Parse authentication config from a dictionary."""
        return M2MAuthenticationConfig(
            type=auth_data.get("type", cls.DEFAULT_AUTH_TYPE),
            token_url=auth_data.get("token_url", cls.DEFAULT_AUTH_TOKEN_URL),
            audience=auth_data.get("audience", cls.DEFAULT_AUTH_AUDIENCE),
            client_id=auth_data.get("client_id"),
            client_secret=auth_data.get("client_secret"),
        )

    @staticmethod
    def check_required_auth_fields(auth: M2MAuthenticationConfig):
        """Ensure required fields (client_id, client_secret) are provided."""
        missing_fields = [
            field
            for field in ("client_id", "client_secret")
            if not getattr(auth, field)
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required authentication fields: {', '.join(missing_fields)}"
            )

    @field_validator("stac", mode="before")
    @classmethod
    def validate_stac(cls, stac_config: Optional[URL]) -> URL:
        """Ensure STAC configuration has a default if not explicitly set.

        Args:
            stac_config (Optional[URL]): The STAC config to validate.

        Returns:
            URL: The validated STAC configuration.
        """
        if stac_config is None:
            return URL(
                protocol="https",
                host="app.open-cosmos.com",
                port=443,
                path="/api/data/v0/stac",
            )
        return stac_config

    @field_validator("datacosmos_cloud_storage", mode="before")
    @classmethod
    def validate_datacosmos_cloud_storage(
        cls, datacosmos_cloud_storage_config: Optional[URL]
    ) -> URL:
        """Ensure datacosmos cloud storage configuration has a default if not explicitly set.

        Args:
            datacosmos_cloud_storage_config (Optional[URL]): The datacosmos cloud storage config to validate.

        Returns:
            URL: The validated datacosmos cloud storage configuration.
        """
        if datacosmos_cloud_storage_config is None:
            return URL(
                protocol="https",
                host="app.open-cosmos.com",
                port=443,
                path="/api/data/v0/storage",
            )
        return datacosmos_cloud_storage_config

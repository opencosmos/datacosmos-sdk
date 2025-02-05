"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

import os
from typing import ClassVar, Literal, Optional

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
    )

    environment: Literal["local", "test", "prod"] = "test"
    log_format: Literal["json", "text"] = "text"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    authentication: Optional[M2MAuthenticationConfig] = None
    stac: Optional[URL] = None

    DEFAULT_AUTH_TYPE: ClassVar[str] = "m2m"
    DEFAULT_AUTH_TOKEN_URL: ClassVar[str] = "https://login.open-cosmos.com/oauth/token"
    DEFAULT_AUTH_AUDIENCE: ClassVar[str] = "https://test.beeapp.open-cosmos.com"

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
            host=os.getenv("OC_STAC_HOST", "test.app.open-cosmos.com"),
            port=int(os.getenv("OC_STAC_PORT", "443")),
            path=os.getenv("OC_STAC_PATH", "/api/data/v0/stac"),
        )

        return cls(authentication=authentication_config, stac=stac_config)

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
            ValueError: If client_id or client_secret is missing.
        """
        if not auth_data:
            raise ValueError(
                "M2M authentication is required. Provide it via:\n"
                "1. Explicit instantiation (Config(authentication=...))\n"
                "2. A YAML config file (config.yaml)\n"
                "3. Environment variables (OC_AUTH_CLIENT_ID, OC_AUTH_CLIENT_SECRET, etc.)"
            )

        # Convert dict to M2MAuthenticationConfig
        auth = (
            M2MAuthenticationConfig(**auth_data)
            if isinstance(auth_data, dict)
            else auth_data
        )

        # Apply defaults where necessary
        auth.type = auth.type or cls.DEFAULT_AUTH_TYPE
        auth.token_url = auth.token_url or cls.DEFAULT_AUTH_TOKEN_URL
        auth.audience = auth.audience or cls.DEFAULT_AUTH_AUDIENCE

        # Validate required fields
        missing_fields = [
            field
            for field in ("client_id", "client_secret")
            if not getattr(auth, field)
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        return auth

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
                host="test.app.open-cosmos.com",
                port=443,
                path="/api/data/v0/stac",
            )
        return stac_config

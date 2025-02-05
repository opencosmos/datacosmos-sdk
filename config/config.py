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
        cls, auth_config: Optional[M2MAuthenticationConfig]
    ) -> M2MAuthenticationConfig:
        """Ensure authentication is provided and defaults are applied where necessary.

        Args:
            auth_config (Optional[M2MAuthenticationConfig]): The authentication config to validate.

        Returns:
            M2MAuthenticationConfig: The validated authentication configuration.

        Raises:
            ValueError: If client_id or client_secret is missing.
        """
        if auth_config is None:
            raise ValueError(
                "M2M authentication is required. Please provide it via:"
                "\n1. Explicit instantiation (Config(authentication=...))"
                "\n2. A YAML config file (config.yaml)"
                "\n3. Environment variables (OC_AUTH_CLIENT_ID, OC_AUTH_CLIENT_SECRET, etc.)"
            )

        if isinstance(auth_config, dict):
            auth_config = M2MAuthenticationConfig(**auth_config)

        # Apply defaults for missing values
        auth_config.type = auth_config.type or cls.DEFAULT_AUTH_TYPE
        auth_config.token_url = auth_config.token_url or cls.DEFAULT_AUTH_TOKEN_URL
        auth_config.audience = auth_config.audience or cls.DEFAULT_AUTH_AUDIENCE

        # Ensure critical values are provided
        if not auth_config.client_id or not auth_config.client_secret:
            raise ValueError(
                "client_id and client_secret are required for authentication."
            )

        return auth_config

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

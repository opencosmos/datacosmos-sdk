"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

import os
from typing import Literal, Optional

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

    # General configurations
    environment: Literal["local", "test", "prod"] = "test"
    log_format: Literal["json", "text"] = "text"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Authentication configuration (must be explicitly provided)
    authentication: Optional[M2MAuthenticationConfig] = None

    # STAC API configuration
    stac: URL = URL(
        protocol="https",
        host="test.app.open-cosmos.com",
        port=443,
        path="/api/data/v0/stac",
    )

    @classmethod
    def from_yaml(cls, file_path: str = "config/config.yaml") -> "Config":
        """Load configuration from a YAML file and override defaults.

        Args:
            file_path (str): The path to the YAML configuration file.

        Returns:
            Config: An instance of the Config class with loaded settings.
        """
        config_data = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
                # Remove empty values from YAML to avoid overwriting with `None`
                config_data = {
                    k: v for k, v in yaml_data.items() if v not in [None, ""]
                }

        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        env_auth = {
            "type": "m2m",
            "client_id": os.getenv("OC_AUTH_CLIENT_ID"),
            "token_url": os.getenv("OC_AUTH_TOKEN_URL"),
            "audience": os.getenv("OC_AUTH_AUDIENCE"),
            "client_secret": os.getenv("OC_AUTH_CLIENT_SECRET"),
        }

        if all(env_auth.values()):  # Ensure all values exist
            env_auth_config = M2MAuthenticationConfig(**env_auth)
        else:
            env_auth_config = None  # If missing, let validation handle it

        return cls(authentication=env_auth_config)

    @field_validator("authentication", mode="before")
    @classmethod
    def validate_authentication(cls, v):
        """Ensure authentication is provided through one of the allowed methods."""
        if v is None:
            raise ValueError(
                "M2M authentication is required. Please provide it via:"
                "\n1. Explicit instantiation (Config(authentication=...))"
                "\n2. A YAML config file (config.yaml)"
                "\n3. Environment variables (OC_AUTH_CLIENT_ID, OC_AUTH_TOKEN_URL, etc.)"
            )
        return v

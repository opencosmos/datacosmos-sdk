"""Configuration module for the Datacosmos SDK.

Handles configuration management using Pydantic and Pydantic Settings.
It loads default values, allows overrides via YAML configuration files,
and supports environment variable-based overrides.
"""

import os
from typing import Literal

import yaml
from pydantic import model_validator
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

    # Authentication configuration
    authentication: M2MAuthenticationConfig = M2MAuthenticationConfig(
        type="m2m",
        client_id="zCeZWJamwnb8ZIQEK35rhx0hSAjsZI4D",
        token_url="https://login.open-cosmos.com/oauth/token",
        audience="https://test.beeapp.open-cosmos.com",
        client_secret="tAeaSgLds7g535ofGq79Zm2DSbWMCOsuRyY5lbyObJe9eAeSN_fxoy-5kaXnVSYa",
    )

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

    @model_validator(mode="before")
    @classmethod
    def merge_with_env(cls, values):
        """Override settings with environment variables if set.

        This method checks if any environment variables corresponding to the
        config fields are set and updates their values accordingly.

        Args:
            values (dict): The configuration values before validation.

        Returns:
            dict: The updated configuration values with environment variable overrides.
        """
        for field in cls.model_fields:
            env_value = os.getenv(f"OC_{field.upper()}")
            if env_value:
                values[field] = env_value
        return values

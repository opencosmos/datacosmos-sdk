"""Module for managing configuration settings for the Datacosmos SDK.

Supports loading from YAML files and environment variables.
"""

import os
from dataclasses import dataclass

import yaml


@dataclass
class Config:
    """Configuration for the Datacosmos SDK.

    Contains authentication details such as client ID, secret, token
    URL, and audience.
    """

    client_id: str
    client_secret: str
    token_url: str
    audience: str

    @staticmethod
    def from_yaml(file_path: str = "config/config.yaml") -> "Config":
        """Load configuration from a YAML file.

        Defaults to 'config/config.yaml' unless otherwise specified.
        """
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        auth = data.get("auth", {})
        return Config(
            client_id=auth["client-id"],
            client_secret=auth["client-secret"],
            token_url=auth["token-url"],
            audience=auth["audience"],
        )

    @staticmethod
    def from_env() -> "Config":
        """Load configuration from environment variables.

        Raises an exception if any required variable is missing.
        """
        return Config(
            client_id=os.getenv("OC_AUTH_CLIENT_ID"),
            client_secret=os.getenv("OC_AUTH_CLIENT_SECRET"),
            token_url=os.getenv("OC_AUTH_TOKEN_URL"),
            audience=os.getenv("OC_AUTH_AUDIENCE"),
        )

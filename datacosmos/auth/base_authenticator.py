"""Base authenticator class for DatacosmosClient."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import requests

    from datacosmos.config.config import Config


class AuthResult:
    """Authentication result object."""

    def __init__(
        self,
        http_client: requests.Session,
        token: Optional[str] = None,
        token_expiry: Optional[datetime] = None,
    ):
        """Authentication result object."""
        self.http_client = http_client
        self.token = token
        self.token_expiry = token_expiry


class BaseAuthenticator(ABC):
    """Abstract base class for all authenticators."""

    def __init__(self, config: Config):
        """Abstract base class for all authenticators."""
        self.config = config

    @abstractmethod
    def authenticate_and_build_session(self) -> AuthResult:
        """Authenticates and builds a requests.Session object.

        Returns:
            AuthResult: An object containing the authenticated session, token, and token expiry.
        """
        ...

    @abstractmethod
    def refresh_token(self) -> AuthResult:
        """Refreshes the authentication token.

        Returns:
            AuthResult: An object with the new token and expiry.
        """
        ...

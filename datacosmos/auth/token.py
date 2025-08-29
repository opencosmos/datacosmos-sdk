"""Authentication Token class."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Optional

DEFAULT_TOKEN_TTL_FALLBACK = 300  # seconds


@dataclass
class Token:
    """Authentication token class."""

    access_token: str
    refresh_token: Optional[str]
    expires_at: int  # unix epoch seconds

    @classmethod
    def from_json_response(cls, data: dict) -> Token:
        """Build a Token from an OAuth2 response.

        Prefer `expires_at` (absolute epoch seconds), then `expires_in`
        (relative per RFC 6749). If both are missing, try to derive `exp`
        from a JWT access token; otherwise fall back to a short TTL.
        """
        exp: Optional[int] = None

        if data.get("expires_at") is not None:
            try:
                exp = int(float(data["expires_at"]))
            except (TypeError, ValueError):
                exp = None

        if exp is None and data.get("expires_in") is not None:
            try:
                exp = int(time.time()) + int(data["expires_in"])
            except (TypeError, ValueError, OverflowError):
                exp = None

        if exp is None:
            exp = cls.__jwt_exp(data.get("access_token", ""))

        if exp is None:
            exp = int(time.time()) + DEFAULT_TOKEN_TTL_FALLBACK

        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=exp,
        )

    def is_expired(self, skew_seconds: int = 30) -> bool:
        """Treat the token as expired slightly early to account for clock skew."""
        return time.time() >= (self.expires_at - skew_seconds)

    @staticmethod
    def __jwt_exp(access_token: str) -> Optional[int]:
        """Best-effort extract of `exp` (epoch seconds) from a JWT access token.

        We do NOT validate the signature here; this is only used as a heuristic
        when the IdP omits both `expires_at` and `expires_in`.
        """
        if not access_token:
            return None
        try:
            parts = access_token.split(".")
            if len(parts) != 3:
                return None
            payload_b64 = parts[1]
            padding = "=" * (-len(payload_b64) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode(payload_b64 + padding).decode()
            )
            if "exp" in payload:
                return int(payload["exp"])
        except Exception:
            return None
        return None

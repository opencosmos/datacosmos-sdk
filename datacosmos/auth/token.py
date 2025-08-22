from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Token:
    access_token: str
    refresh_token: Optional[str]
    expires_at: float  # epoch seconds

    @classmethod
    def from_json_response(cls, data: dict) -> "Token":
        # Some IdPs return expires_in, others return expires_at
        exp = float(
            data.get("expires_at")
            or (time.time() + float(data.get("expires_in", 3600)))
        )
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=exp,
        )

    def is_expired(self, skew_seconds: int = 30) -> bool:
        return (self.expires_at - time.time()) <= skew_seconds

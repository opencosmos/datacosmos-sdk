"""Opens a browser for the user to log in (Authorization Code), caches token to a file, and refreshes when expired."""

from __future__ import annotations

import http.server
import json
import socketserver
import time
import urllib.parse
import webbrowser
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from datacosmos.auth.token import Token


@dataclass
class LocalTokenFetcher:
    """Opens a browser for the user to log in (Authorization Code), caches token to a file, and refreshes when expired."""

    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_port: int
    audience: str
    scopes: str
    token_file: Path

    def get_token(self) -> Token:
        """Return a valid token from cache, or refresh / interact as needed."""
        tok = self.__load()
        if not tok:
            return self.__interactive_login()

        if tok.is_expired():
            # Try to refresh; if that fails for any reason, fall back to interactive login.
            try:
                return self.__refresh(tok)
            except (requests.HTTPError, RuntimeError):
                return self.__interactive_login()

        return tok

    def __save(self, token: Token) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump(
                {
                    "access_token": token.access_token,
                    "refresh_token": token.refresh_token,
                    "expires_at": token.expires_at,
                },
                f,
            )

    def __load(self) -> Optional[Token]:
        if not self.token_file.exists():
            return None
        with open(self.token_file, "r") as f:
            data = json.load(f)
        return Token(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=int(data["expires_at"]),
        )

    def __exchange_code(self, code: str) -> Token:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"http://localhost:{self.redirect_port}/oauth/callback",
            "client_id": self.client_id,
            "audience": self.audience,
        }
        resp = requests.post(self.token_endpoint, data=data, timeout=30)
        resp.raise_for_status()
        return Token.from_json_response(resp.json())

    def __refresh(self, token: Token) -> Token:
        """Refresh the token, persist it on success, and return it.

        Raises:
            RuntimeError: if no refresh_token is available.
            requests.HTTPError: if the token endpoint returns an error.
        """
        if not token.refresh_token:
            raise RuntimeError("No refresh_token available for local auth refresh")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": self.client_id,
            "audience": self.audience,
        }
        resp = requests.post(self.token_endpoint, data=data, timeout=30)
        resp.raise_for_status()  # will raise requests.HTTPError on non-2xx

        payload = resp.json()
        refreshed = Token(
            access_token=payload["access_token"],
            refresh_token=token.refresh_token,
            expires_at=time.time() + int(payload.get("expires_in", 3600)),
        )
        self.__save(refreshed)
        return refreshed

    def __interactive_login(self) -> Token:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": f"http://localhost:{self.redirect_port}/oauth/callback",
            "audience": self.audience,
            "scope": self.scopes,
        }
        url = f"{self.authorization_endpoint}?{urllib.parse.urlencode(params)}"

        with suppress(Exception):
            webbrowser.open(url, new=1, autoraise=True)

        class Handler(http.server.BaseHTTPRequestHandler):
            code: Optional[str] = None

            def do_GET(self):  # noqa: N802
                qs = urllib.parse.urlparse(self.path).query
                data = urllib.parse.parse_qs(qs)
                if "code" in data:
                    Handler.code = data["code"][0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Login complete. You can close this window.")
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"No authorization code found.")

            def log_message(self, *_args, **_kwargs) -> None:
                return

        with socketserver.TCPServer(
            ("localhost", int(self.redirect_port)), Handler
        ) as httpd:
            httpd.timeout = 300  # 5 minutes
            httpd.handle_request()

        if not Handler.code:
            raise RuntimeError(
                f"Login timed out. If your browser did not open, visit:\n{url}"
            )

        token = self.__exchange_code(Handler.code)
        self.__save(token)
        return token

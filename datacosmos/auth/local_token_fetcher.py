from __future__ import annotations

import http.server
import json
import socketserver
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from datacosmos.auth.token import Token


@dataclass
class LocalTokenFetcher:
    """
    Opens a browser for the user to log in (Authorization Code),
    caches token to a file, and refreshes when expired.
    """
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_port: int
    audience: str
    scopes: str
    token_file: Path

    def get_token(self) -> Token:
        tok = self.__load()
        if tok and not tok.is_expired():
            return tok
        if tok and tok.is_expired():
            refreshed = self.__refresh(tok)
            if refreshed:
                self.__save(refreshed)
                return refreshed
        # No token or failed refresh -> interactive login
        return self.__interactive_login()

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
            expires_at=float(data["expires_at"]),
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

    def __refresh(self, token: Token) -> Optional[Token]:
        if not token.refresh_token:
            return None
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": self.client_id,
            "audience": self.audience,
        }
        resp = requests.post(self.token_endpoint, data=data, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return Token(
            access_token=data["access_token"],
            refresh_token=token.refresh_token,  # some IdPs omit it on refresh
            expires_at=time.time() + float(data.get("expires_in", 3600)),
        )


    def __interactive_login(self) -> Token:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": f"http://localhost:{self.redirect_port}/oauth/callback",
            "audience": self.audience,
            "scope": self.scopes,
        }
        url = f"{self.authorization_endpoint}?{urllib.parse.urlencode(params)}"
        try:
            webbrowser.open(url, new=1, autoraise=True)
        except Exception:
            pass  # user can copy-paste URL if needed

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

            def log_message(self, *_args, **_kwargs) -> None:  # silence
                return

        with socketserver.TCPServer(("localhost", int(self.redirect_port)), Handler) as httpd:
            httpd.timeout = 300  # 5 minutes
            httpd.handle_request()

        if not Handler.code:
            raise RuntimeError(
                f"Login timed out. If your browser did not open, visit:\n{url}"
            )

        token = self.__exchange_code(Handler.code)
        self.__save(token)
        return token


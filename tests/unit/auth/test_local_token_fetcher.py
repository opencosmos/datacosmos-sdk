import json
import time
from pathlib import Path

import pytest

from datacosmos.auth.local_token_fetcher import LocalTokenFetcher
from datacosmos.auth.token import Token


class TestLocalTokenFetcher:
    def _read_cache(self, p: Path) -> dict:
        with open(p, "r") as f:
            return json.load(f)

    def test_get_token_returns_cached_valid_token(self, tmp_path, monkeypatch):
        cache = tmp_path / "token.json"
        tok = {
            "access_token": "cached-access",
            "refresh_token": "cached-refresh",
            "expires_at": int(time.time()) + 3600,
        }
        cache.write_text(json.dumps(tok))

        fetcher = LocalTokenFetcher(
            client_id="cid",
            authorization_endpoint="https://auth.example/authorize",
            token_endpoint="https://auth.example/token",
            redirect_port=8765,
            audience="https://api.example",
            scopes="openid profile",
            token_file=cache,
        )

        t = fetcher.get_token()
        assert isinstance(t, Token)
        assert t.access_token == "cached-access"
        assert t.refresh_token == "cached-refresh"
        assert t.expires_at == tok["expires_at"]

    def test_get_token_refreshes_expired_token_and_saves(self, tmp_path, monkeypatch):
        cache = tmp_path / "token.json"

        # freeze time for deterministic expiry checks
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr(
            "datacosmos.auth.local_token_fetcher.time.time", lambda: fixed_now
        )

        expired = {
            "access_token": "old-access",
            "refresh_token": "r1",
            "expires_at": fixed_now - 100,  # expired
        }
        cache.write_text(json.dumps(expired))

        fetcher = LocalTokenFetcher(
            client_id="cid",
            authorization_endpoint="https://auth.example/authorize",
            token_endpoint="https://auth.example/token",
            redirect_port=8765,
            audience="https://api.example",
            scopes="openid profile",
            token_file=cache,
        )

        class DummyResp:
            status_code = 200

            def raise_for_status(self):  # <-- needed by __refresh
                return None

            def json(self):
                return {"access_token": "new-access", "expires_in": 1800}

        def fake_post(url, data=None, timeout=None):
            assert data["grant_type"] == "refresh_token"
            assert data["refresh_token"] == "r1"
            assert data["client_id"] == "cid"
            return DummyResp()

        monkeypatch.setattr(
            "datacosmos.auth.local_token_fetcher.requests.post", fake_post
        )

        t = fetcher.get_token()
        assert t.access_token == "new-access"
        assert t.expires_at == pytest.approx(fixed_now + 1800, rel=0, abs=1e-9)

        saved = self._read_cache(cache)
        assert saved["access_token"] == "new-access"
        assert saved["refresh_token"] == "r1"
        assert saved["expires_at"] == pytest.approx(fixed_now + 1800, rel=0, abs=1e-9)

    def test_get_token_interactive_when_no_token(self, tmp_path, monkeypatch):
        cache = tmp_path / "token.json"

        fetcher = LocalTokenFetcher(
            client_id="cid",
            authorization_endpoint="https://auth.example/authorize",
            token_endpoint="https://auth.example/token",
            redirect_port=8765,
            audience="https://api.example",
            scopes="openid profile",
            token_file=cache,
        )

        fake_token = Token("interactive-access", "rr", time.time() + 1000)

        # stub that preserves the side-effect of the real method
        def fake_interactive_login():
            fetcher._LocalTokenFetcher__save(fake_token)
            return fake_token

        monkeypatch.setattr(
            fetcher, "_LocalTokenFetcher__interactive_login", fake_interactive_login
        )

        t = fetcher.get_token()
        assert t.access_token == "interactive-access"

        # now the cache exists
        with open(cache, "r") as f:
            saved = json.load(f)
        assert saved["access_token"] == "interactive-access"
        assert saved["refresh_token"] == "rr"
        assert saved["expires_at"] == pytest.approx(
            fake_token.expires_at, rel=0, abs=1e-6
        )

    def test_get_token_interactive_when_refresh_fails(self, tmp_path, monkeypatch):
        cache = tmp_path / "token.json"

        # freeze time so expiry math is deterministic
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr(
            "datacosmos.auth.local_token_fetcher.time.time", lambda: fixed_now
        )

        expired = {
            "access_token": "old-access",
            "refresh_token": "r1",
            "expires_at": fixed_now - 100,
        }
        cache.write_text(json.dumps(expired))

        fetcher = LocalTokenFetcher(
            client_id="cid",
            authorization_endpoint="https://auth.example/authorize",
            token_endpoint="https://auth.example/token",
            redirect_port=8765,
            audience="https://api.example",
            scopes="openid profile",
            token_file=cache,
        )

        class FailResp:
            status_code = 400

            def raise_for_status(self):
                import requests

                raise requests.HTTPError("400 Bad Request")

            def json(self):  # pragma: no cover
                return {"error": "bad_refresh"}

        def fake_post(url, data=None, timeout=None):
            assert data["grant_type"] == "refresh_token"
            return FailResp()

        monkeypatch.setattr(
            "datacosmos.auth.local_token_fetcher.requests.post", fake_post
        )

        fake_token = Token("interactive-after-fail", "r2", fixed_now + 500)

        # preserve side-effect: save the token like the real method would
        def fake_interactive_login():
            fetcher._LocalTokenFetcher__save(fake_token)
            return fake_token

        monkeypatch.setattr(
            fetcher, "_LocalTokenFetcher__interactive_login", fake_interactive_login
        )

        t = fetcher.get_token()
        assert t.access_token == "interactive-after-fail"

        saved = self._read_cache(cache)
        assert saved["access_token"] == "interactive-after-fail"
        assert saved["refresh_token"] == "r2"

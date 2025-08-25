import pytest

from datacosmos.auth.token import Token


class TestToken:
    def test_from_json_response_uses_expires_at(self, monkeypatch):
        fixed_now = 1_700_000_000.0
        # Freeze time to prove we're using expires_at directly
        monkeypatch.setattr("datacosmos.auth.token.time.time", lambda: fixed_now)

        data = {
            "access_token": "abc",
            "refresh_token": "r1",
            "expires_at": fixed_now + 1234.0,
        }
        t = Token.from_json_response(data)
        assert t.access_token == "abc"
        assert t.refresh_token == "r1"
        assert t.expires_at == pytest.approx(fixed_now + 1234.0, rel=0, abs=1e-9)

    def test_from_json_response_uses_expires_in(self, monkeypatch):
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr("datacosmos.auth.token.time.time", lambda: fixed_now)

        data = {
            "access_token": "abc",
            # refresh_token omitted on purpose
            "expires_in": 120,  # can be int or str; both should work
        }
        t = Token.from_json_response(data)
        assert t.access_token == "abc"
        assert t.refresh_token is None
        assert t.expires_at == pytest.approx(fixed_now + 120, rel=0, abs=1e-9)

    def test_is_expired_default_skew(self, monkeypatch):
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr("datacosmos.auth.token.time.time", lambda: fixed_now)

        # Not expired: expires 100s from now; default skew is 30s
        t_ok = Token("tok", "r", fixed_now + 100)
        assert t_ok.is_expired() is False

        # Boundary: exactly at skew -> counts as expired (<= skew)
        t_boundary = Token("tok", "r", fixed_now + 30)
        assert t_boundary.is_expired() is True

        # Clearly expired: in the past
        t_past = Token("tok", "r", fixed_now - 1)
        assert t_past.is_expired() is True

    def test_is_expired_custom_skew(self, monkeypatch):
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr("datacosmos.auth.token.time.time", lambda: fixed_now)

        # With a smaller skew, token 10s away is NOT expired
        t = Token("tok", None, fixed_now + 10)
        assert t.is_expired(skew_seconds=5) is False
        # With a larger skew, same token IS expired
        assert t.is_expired(skew_seconds=15) is True

    def test_missing_access_token_raises_keyerror(self, monkeypatch):
        fixed_now = 1_700_000_000.0
        monkeypatch.setattr("datacosmos.auth.token.time.time", lambda: fixed_now)

        data = {"expires_in": 60}
        with pytest.raises(KeyError):
            Token.from_json_response(data)

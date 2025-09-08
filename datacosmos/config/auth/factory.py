"""Config authentication factory.

This module normalizes the `authentication` config into a concrete model:
- `parse_auth_config` converts raw dicts (e.g., from YAML/env) into a model instance.
- `apply_auth_defaults` fills sensible defaults per auth type without inventing secrets.
- `check_required_auth_fields` enforces the minimum required inputs.
- `normalize_authentication` runs the whole pipeline.

Design notes:
- Auth models accept partial data (fields are Optional with None defaults).
- We DO NOT pass `None` explicitly when constructing models here.
- Required-ness is enforced centrally by `check_required_auth_fields`, not by model init.
"""

from typing import Optional, Union, cast

from datacosmos.config.constants import (
    DEFAULT_AUTH_AUDIENCE,
    DEFAULT_AUTH_TOKEN_URL,
    DEFAULT_AUTH_TYPE,
    DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT,
    DEFAULT_LOCAL_CACHE_FILE,
    DEFAULT_LOCAL_REDIRECT_PORT,
    DEFAULT_LOCAL_SCOPES,
    DEFAULT_LOCAL_TOKEN_ENDPOINT,
)
from datacosmos.config.models.local_user_account_authentication_config import (
    LocalUserAccountAuthenticationConfig,
)
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig

AuthModel = Union[M2MAuthenticationConfig, LocalUserAccountAuthenticationConfig]


def parse_auth_config(raw: dict | AuthModel | None) -> Optional[AuthModel]:
    """Turn a raw dict (e.g., from YAML) into a concrete auth model.

    - If `raw` is already an auth model (M2M or local), return it unchanged.
    - If `raw` is a dict, choose/validate the type using `raw['type']`
      (or DEFAULT_AUTH_TYPE), then construct the corresponding model.
      For missing fields we *may* apply non-secret defaults (endpoints, etc.).
    """
    if raw is None or isinstance(
        raw, (M2MAuthenticationConfig, LocalUserAccountAuthenticationConfig)
    ):
        return cast(Optional[AuthModel], raw)

    auth_type = _normalize_auth_type(raw.get("type") or DEFAULT_AUTH_TYPE)

    if auth_type == "local":
        return LocalUserAccountAuthenticationConfig(
            type="local",
            client_id=raw.get("client_id"),
            authorization_endpoint=raw.get(
                "authorization_endpoint", DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT
            ),
            token_endpoint=raw.get("token_endpoint", DEFAULT_LOCAL_TOKEN_ENDPOINT),
            redirect_port=raw.get("redirect_port", DEFAULT_LOCAL_REDIRECT_PORT),
            scopes=raw.get("scopes", DEFAULT_LOCAL_SCOPES),
            audience=raw.get("audience", DEFAULT_AUTH_AUDIENCE),
            cache_file=raw.get("cache_file", DEFAULT_LOCAL_CACHE_FILE),
        )

    return M2MAuthenticationConfig(
        type="m2m",
        token_url=raw.get("token_url", DEFAULT_AUTH_TOKEN_URL),
        audience=raw.get("audience", DEFAULT_AUTH_AUDIENCE),
        client_id=raw.get("client_id"),
        client_secret=raw.get("client_secret"),
    )


def apply_auth_defaults(auth: AuthModel | None) -> AuthModel:
    """Fill in any missing defaults by type (non-secret values only).

    If `auth` is None, construct a default "shell" based on DEFAULT_AUTH_TYPE,
    without passing None for unknown credentials.
    """
    if auth is None:
        default_type = _normalize_auth_type(DEFAULT_AUTH_TYPE)
        if default_type == "local":
            auth = LocalUserAccountAuthenticationConfig(
                type="local",
                authorization_endpoint=DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT,
                token_endpoint=DEFAULT_LOCAL_TOKEN_ENDPOINT,
                redirect_port=DEFAULT_LOCAL_REDIRECT_PORT,
                scopes=DEFAULT_LOCAL_SCOPES,
                audience=DEFAULT_AUTH_AUDIENCE,
                cache_file=DEFAULT_LOCAL_CACHE_FILE,
            )
        else:  # "m2m"
            auth = M2MAuthenticationConfig(
                type="m2m",
                token_url=DEFAULT_AUTH_TOKEN_URL,
                audience=DEFAULT_AUTH_AUDIENCE,
            )

    if isinstance(auth, M2MAuthenticationConfig):
        auth.type = auth.type or "m2m"
        auth.token_url = auth.token_url or DEFAULT_AUTH_TOKEN_URL
        auth.audience = auth.audience or DEFAULT_AUTH_AUDIENCE
        return auth

    # Local defaults (Pydantic already coerces types; only set when missing)
    auth.type = auth.type or "local"
    auth.authorization_endpoint = (
        auth.authorization_endpoint or DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT
    )
    auth.token_endpoint = auth.token_endpoint or DEFAULT_LOCAL_TOKEN_ENDPOINT
    if auth.redirect_port is None:
        auth.redirect_port = DEFAULT_LOCAL_REDIRECT_PORT
    auth.scopes = auth.scopes or DEFAULT_LOCAL_SCOPES
    auth.audience = auth.audience or DEFAULT_AUTH_AUDIENCE
    auth.cache_file = auth.cache_file or DEFAULT_LOCAL_CACHE_FILE
    return auth


def check_required_auth_fields(auth: AuthModel) -> None:
    """Enforce required fields per auth type.

    - m2m requires client_id and client_secret.
    - local requires client_id.
    """
    if isinstance(auth, M2MAuthenticationConfig):
        missing = [f for f in ("client_id", "client_secret") if not getattr(auth, f)]
        if missing:
            raise ValueError(
                f"Missing required authentication fields for m2m: {', '.join(missing)}"
            )
        return

    if isinstance(auth, LocalUserAccountAuthenticationConfig):
        if not auth.client_id:
            raise ValueError(
                "Missing required authentication field for local: client_id"
            )
        return

    raise ValueError(f"Unsupported authentication model: {type(auth).__name__}")


def normalize_authentication(raw: dict | AuthModel | None) -> AuthModel:
    """End-to-end auth normalization: parse -> apply defaults -> required-field checks."""
    model = parse_auth_config(raw)
    model = apply_auth_defaults(model)
    check_required_auth_fields(model)
    return model


def _normalize_auth_type(value: str) -> str:
    """Return a normalized auth type or raise for unsupported values."""
    v = (value or "").strip().lower()
    if v in {"m2m", "local"}:
        return v
    raise ValueError(
        f"Unsupported authentication type: {value!r}. Expected 'm2m' or 'local'."
    )

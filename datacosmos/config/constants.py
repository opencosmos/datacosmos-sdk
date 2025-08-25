"""Config constants."""

# ---- Authentication defaults ----
DEFAULT_AUTH_TYPE = "m2m"

# M2M
DEFAULT_AUTH_TOKEN_URL = "https://login.open-cosmos.com/oauth/token"
DEFAULT_AUTH_AUDIENCE = "https://beeapp.open-cosmos.com"

# Local (interactive)
DEFAULT_LOCAL_AUTHORIZATION_ENDPOINT = "https://login.open-cosmos.com/authorize"
DEFAULT_LOCAL_TOKEN_ENDPOINT = DEFAULT_AUTH_TOKEN_URL
DEFAULT_LOCAL_REDIRECT_PORT = 8765
DEFAULT_LOCAL_SCOPES = "openid profile email offline_access"
DEFAULT_LOCAL_CACHE_FILE = "~/.datacosmos/token_cache.json"

# ---- Service URLs ----
DEFAULT_STAC = dict(
    protocol="https", host="app.open-cosmos.com", port=443, path="/api/data/v0/stac"
)
DEFAULT_STORAGE = dict(
    protocol="https", host="app.open-cosmos.com", port=443, path="/api/data/v0/storage"
)

# ---- Config file path ----
DEFAULT_CONFIG_YAML = "config/config.yaml"

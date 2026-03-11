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

# ---- Open Cosmos cluster detection ----
# Custom environment variable to identify Open Cosmos's internal cluster.
# Only when this is set will the SDK use internal cluster URLs.
# This prevents customers running the SDK in their own K8s clusters
# from incorrectly trying to use Open Cosmos internal services.
OPENCOSMOS_INTERNAL_CLUSTER_ENV = "OPENCOSMOS_INTERNAL_CLUSTER"

# ---- Service URLs ----
# External URLs (default, used outside Kubernetes)
DEFAULT_STAC_EXTERNAL = dict(
    protocol="https", host="app.open-cosmos.com", port=443, path="/api/data/v0/stac"
)
DEFAULT_STORAGE_EXTERNAL = dict(
    protocol="https", host="app.open-cosmos.com", port=443, path="/api/data/v0/storage"
)
DEFAULT_PROJECT = dict(
    protocol="https", host="app.open-cosmos.com", port=443, path="/api/data/v0"
)

# Internal URLs (used inside Kubernetes cluster)
DEFAULT_STAC_INTERNAL = dict(
    protocol="http", host="catalog.default.svc.cluster.local", port=80, path="/"
)
DEFAULT_STORAGE_INTERNAL = dict(
    protocol="http",
    host="storage.default.svc.cluster.local",
    port=80,
    path="/",
)
DEFAULT_PROJECT_INTERNAL = dict(
    protocol="http",
    host="stac-scenario-service.default.svc.cluster.local",
    port=80,
    path="",
)

# Legacy aliases for backward compatibility
DEFAULT_STAC = DEFAULT_STAC_EXTERNAL
DEFAULT_STORAGE = DEFAULT_STORAGE_EXTERNAL

# ---- Config file path ----
DEFAULT_CONFIG_YAML = "config/config.yaml"

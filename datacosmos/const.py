"""Stores constants used in the datacosmos package."""

from enum import Enum

DATACOSMOS_PRODUCTION_BASE_URL = "https://app.open-cosmos.com/api/data/v0"
DATACOSMOS_PRODUCTION_AUDIENCE = "https://beeapp.open-cosmos.com"
DATACOSMOS_TOKEN_URL = "https://opencosmos.eu.auth0.com/oauth/token"  # nosec: B105


class Constellations(Enum):
    """Enumeration of constellations for queries to the DataCosmos API."""

    SENTINEL_1 = "sentinel-1"
    SENTINEL_2 = "sentinel-2"
    OPEN_CONSTELLATION = "open-constellation"

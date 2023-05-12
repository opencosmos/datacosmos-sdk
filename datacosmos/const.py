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


class Levels(Enum):
    """Enumeration of data levels for queries to the DataCosmos API.

    See the following link for more information about data-processing levels:
    https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-information-policy/data-levels
    """

    L0 = "L0"
    L1A = "L1A"
    L1B = "L1B"
    L1C = "L1C"
    L1D = "L1D"
    L2A = "L2A"

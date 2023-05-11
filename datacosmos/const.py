"""Stores constants used in the datacosmos package."""

from enum import Enum

DATACOSMOS_PRODUCTION_BASE_URL = "https://app.open-cosmos.com/api/data/v0"
DATACOSMOS_PRODUCTION_AUDIENCE = "https://beeapp.open-cosmos.com"
DATACOSMOS_TOKEN_URL = "https://opencosmos.eu.auth0.com/oauth/token"  # nosec: B105


class Satellites(Enum):
    """Enumeration of satellites used for queries to the DataCosmos API.

    The names of the members are the human readable names of the satellites,
    and the values are the COSPAR IDs of the satellites.
    """

    # Sentinel-1A is a European radar imaging satellite launched in 2014
    SENTINEL_1A = "2014-016A"

    # Sentinel-1B is a European radar imaging satellite launched on 25 April 2016
    SENTINEL_1B = "2016-025A"

    # Sentinel-2A is a European optical imaging satellite launched in 2015
    SENTINEL_2A = "2015-028A"

    # Sentinel-2B is a European optical imaging satellite that was launched on 7
    # March 2017
    SENTINEL_2B = "2017-013A"

    # Sentinel-3A is a European Space Agency Earth observation satellite dedicated to
    # oceanography which launched on 16 February 2016
    SENTINEL_3A = "2016-011A"

    # Sentinel-3B is a European Space Agency Earth observation satellite
    # dedicated to oceanography which launched on 25 April 2018
    SENTINEL_3B = "2018-039A"

    # Sentinel-5P is an Earth observation satellite developed by ESA as part of
    # the Copernicus Programme to close the gap in continuity of observations
    # between Envisat and Sentinel-5
    SENTINEL_5P = "2017-064A"

    # The Sentinel-6 Michael Freilich satellite is a radar altimeter satellite
    # developed in partnership between several European and American
    # organizations
    SENTINEL_6 = "2020-086A"

    # Landsat 7 is the seventh satellite of the Landsat program launched on 15
    # April 1999
    LANDSAT_7 = "1999-020A"

    # Landsat 8 is an American Earth observation satellite launched on 11
    # February 2013
    LANDSAT_8 = "2013-008A"

    # Landsat 9 is an Earth observation satellite launched on 27 September 2021
    LANDSAT_9 = "2021-088A"

    # Geosat-2 is a Spanish remote sensing Earth observation satellite built for
    # Elecnor Deimos under an agreement with Satrec Initiative
    GEOSAT_2 = "2014-033D"

    # Menut is an Open Cosmos medium-resolution multispectral Earth observation
    # satellite
    MENUT = "2023-001B"


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

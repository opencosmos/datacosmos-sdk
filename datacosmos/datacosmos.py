"""Contains the main entry point for the DataCosmos API SDK."""

from __future__ import annotations

import datetime
import os
from typing import Dict, List

import geojson

from datacosmos.auth import DataCosmosCredentials
from datacosmos.const import (
    DATACOSMOS_PRODUCTION_BASE_URL,
    Constellations,
    Levels,
    Satellites,
)
from datacosmos.stac import search as stac_search


class DataCosmos:
    """This is the main entry point for the DataCosmos API SDK.

    You can use this to search for items in the DataCosmos catalogue and then
    download them.

    The SDK can be initialised in two ways:

    1. With credentials loaded from environment variables
    2. With credentials loaded from a file

    With credentials from environment variables DATACOSMOS_KEY_ID and
    DATACOSMOS_KEY_SECRET:

    .. code-block:: python

        from datacosmos import DataCosmos

        dc = DataCosmos() results = dc.search(number=10) for item in results:
            print(item.id)

    With credentials from a file:

    .. code-block:: python

        from datacosmos import DataCosmos

        dc = DataCosmos.with_credentials_from("path/to/credentials.json")
        results = dc.search(number=10) for item in results:
            print(item.id)

    :param credentials: DataCosmosCredentials object containing client ID and
        secret. If not provided, will be loaded from environment variables.
    :param api_url: Override the default API URL (useful for development)
    """

    def __init__(
        self,
        credentials: DataCosmosCredentials | None = None,
        api_url: str = DATACOSMOS_PRODUCTION_BASE_URL,
    ):
        """Initialise a new DataCosmos instance.

        :param credentials: DataCosmosCredentials object containing client ID
            and secret. If not provided, will be loaded from environment
            variables.
        :param api_url: Override the default API URL (useful for development).
        """
        self.credentials = credentials
        if self.credentials is None:
            self.credentials = DataCosmosCredentials.from_env()

        self.base_url = api_url
        self.http_session = self.credentials.authenticated_session()

    @classmethod
    def with_credentials_from(cls, path: os.PathLike | str) -> "DataCosmos":
        """Load credentials from the provided file path.

        The file should be a JSON file with the following format:

        {
            "id": "your_client_id", "secret": "your_client_secret"
        }

        :param path: Location of the file to load credentials from.
        :return: DataCosmos instance with credentials loaded from the given
            file.
        """
        credentials = DataCosmosCredentials.from_file(path)
        return cls(credentials=credentials)

    def search(
        self,
        number: int | None = None,
        constellations: List[Constellations] | None = None,
        satellites: List[Satellites] | None = None,
        levels: List[Levels] | None = None,
        after: datetime.datetime | None = None,
        before: datetime.datetime | None = None,
        bbox: List[float] | None = None,
        intersects: geojson.GeoJSON | None = None,
        min_cloud_cover_pct: float | None = None,
        max_cloud_cover_pct: float | None = None,
        min_resolution_m: float | None = None,
        max_resolution_m: float | None = None,
        query: Dict | None = None,
    ) -> stac_search.SearchResults:
        """Search for items in the DataCosmos catalogue.

        Returns a SearchResults object which can be iterated over to get the
        resulting items.

        :param number: Maximum number of results to return. If not provided,
            will return all results.
        :param constellations: List of constellations to search for. If not
            provided, will search all constellations. See the constellations
            enum in datacosmos.const for a list of available constellations.
        :param satellites: List of satellites to search for. If not provided,
            will search all satellites. See the Satellites enum in
            datacosmos.const for a list of available satellites.
        :param levels: List of data processing levels to search for. If not
            provided, will search all levels.
        :param after: Search for items after this datetime.
        :param before: Search for items before this datetime.
        :param bbox: Search for items within this bounding box, as a list of
            four floats: [min_lon, min_lat, max_lon, max_lat].
        :param intersects: Search for items intersecting with this GeoJSON
            geometry.
        :param min_cloud_cover_pct: Minimum cloud cover percentage.
        :param max_cloud_cover_pct: Maximum cloud cover percentage.
        :param min_resolution_m: Minimum resolution in metres.
        :param max_resolution_m: Maximum resolution in metres.
        :param query: Additional query parameters to pass through to the search
            API. See
            https://github.com/radiantearth/stac-api-spec/tree/main/item-search
            for more details regarding the STAC API specification.
        :return: Iterable SearchResults object containing the results of the
            search.
        """
        params = stac_search.SearchParams(
            number=number,
            constellations=constellations,
            satellites=satellites,
            levels=levels,
            before=before,
            after=after,
            bbox=bbox,
            intersects=intersects,
            min_cloud_cover_pct=min_cloud_cover_pct,
            max_cloud_cover_pct=max_cloud_cover_pct,
            min_resolution_m=min_resolution_m,
            max_resolution_m=max_resolution_m,
            query=query,
        )
        return stac_search.SearchResults(
            params, http_session=self.http_session, api_base_url=self.base_url
        )

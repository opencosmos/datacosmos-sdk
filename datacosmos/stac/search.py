"""Handles searching for STAC items using the DataCosmos POST API."""

import datetime
import json
from dataclasses import dataclass
from typing import Dict, Iterator, List

import geojson
import requests
from requests_oauthlib import OAuth2Session

from datacosmos.const import Constellations, Levels, Satellites
from datacosmos.errors import DataCosmosRequestError
from datacosmos.stac.item import STACItem

MAX_ITEMS_PER_REQUEST = 20_000


@dataclass
class SearchParams:
    """STAC search parameters.

    Structure for storing STAC search parameters and formatting them into the
    request body.
    """

    number: int | None = None
    constellations: List[Constellations] | None = None
    satellites: List[Satellites] | None = None
    levels: List[Levels] | None = None
    after: datetime.datetime | None = None
    before: datetime.datetime | None = None
    bbox: List[float] | None = None
    intersects: geojson.GeoJSON | Dict | None = None
    min_cloud_cover_pct: float | None = None
    max_cloud_cover_pct: float | None = None
    min_resolution_m: float | None = None
    max_resolution_m: float | None = None
    query: Dict | None = None

    def _add_constellations(self, body: Dict) -> None:
        if self.constellations is not None:
            body["query"]["constellation"] = {
                "in": [c.value for c in self.constellations]
            }

    def _add_satellites(self, body: Dict) -> None:
        if self.satellites is not None:
            body["query"]["sat:platform_international_designator"] = {
                "in": [c.value for c in self.satellites]
            }

    def _add_levels(self, body: Dict) -> None:
        if self.levels is not None:
            body["query"]["processing:level"] = {"in": [c.value for c in self.levels]}

    def _add_datetimes(self, body: Dict) -> None:
        expr = {}
        if self.after is not None:
            expr["gte"] = self.after.isoformat()
        if self.before is not None:
            expr["lte"] = self.before.isoformat()
        if expr:
            body["query"]["datetime"] = expr

    def _add_bbox(self, body: Dict) -> None:
        if self.bbox is not None:
            body["bbox"] = self.bbox

    def _add_intersects(self, body: Dict) -> None:
        if self.intersects is not None:
            body["intersects"] = self.intersects

    def _add_cloud_cover(self, body: Dict) -> None:
        expr = {}
        if self.min_cloud_cover_pct is not None:
            expr["gte"] = self.min_cloud_cover_pct
        if self.max_cloud_cover_pct is not None:
            expr["lte"] = self.max_cloud_cover_pct
        if expr:
            body["query"]["eo:cloud_cover"] = expr

    def _add_resolution(self, body: Dict) -> None:
        expr = {}
        if self.min_resolution_m is not None:
            expr["gte"] = self.min_resolution_m
        if self.max_resolution_m is not None:
            expr["lte"] = self.max_resolution_m
        if expr:
            body["query"]["gsd"] = expr

    def _add_query(self, body: Dict) -> None:
        if self.query is not None:
            body["query"].update(self.query)

    def build(self) -> Dict:
        """Build the search query body to be sent to the API."""
        body = {}
        body["query"] = {}

        self._add_constellations(body)
        self._add_satellites(body)
        self._add_levels(body)
        self._add_datetimes(body)
        self._add_bbox(body)
        self._add_intersects(body)
        self._add_cloud_cover(body)
        self._add_resolution(body)
        self._add_query(body)

        if not body["query"]:
            del body["query"]

        return body


class SearchResults:
    """The results of a search query.

    SearchResults is an iterable object that represents the results of a search query.

    It can be iterated over to get the individual STACItem objects.
    It is also possible to use the `all()` method to get the results as a list
    without iterating over the items.

    Results are fetched in batches of 20,000 items. If the number of items matched
    by the query is greater than 20,000, pages will be fetched as needed.
    """

    def __init__(
        self, params: SearchParams, http_session: OAuth2Session, api_base_url: str
    ):
        """Initialise the SearchResults object.

        This should only be called by DataCosmos.search.
        """
        self.params = params
        self._body = params.build()

        self._http_session = http_session
        self._next_link = f"{api_base_url}/stac/search"
        self._cursor = 0
        self.items = []
        self.matched = 0

        self._fetch_next_page()

    def __repr__(self):
        """Return a string representation of the SearchResults object."""
        return (
            f"<SearchResults matched={self.matched} fetched={len(self.items)} "
            f"params={self.params}>"
        )

    def __iter__(self) -> Iterator[STACItem]:
        """Return an iterator over the STAC items returned from the search request."""
        return self

    def __next__(self) -> STACItem:
        """Return the next STAC item from the search results.

        If necessary this will fetch additional pages from the API.
        """
        if self._cursor >= len(self.items):
            self._fetch_next_page()

        if self._cursor >= len(self.items):
            raise StopIteration()

        result = self.items[self._cursor]
        self._cursor += 1
        return result

    def all(self) -> List[STACItem]:
        """Return all results as a list.

        This will fetch all pages and return the results as a single list of
        STACItem objects.

        :return: List of STACItem objects matching the query.
        """
        while not self._all_fetched():
            self._fetch_next_page()
        return self.items

    def _fetch_next_page(self):
        """Fetch the next page of results.

        This will update the `items` attribute with the new results, and update
        the `matched` attribute with the total number of items matched by the
        query.
        """
        if self._all_fetched() or self._next_link is None:
            return

        self._body["limit"] = self._next_limit()
        response = self._http_session.post(self._next_link, json=self._body)
        self._check_response(response)
        response.raise_for_status()

        items = [STACItem.from_dict(i) for i in response.json()["features"]]
        self.items.extend(items)
        self._next_link = self._next_link_from(response)
        self.matched = self._total_matched_from(response)

    def _next_limit(self) -> int:
        """Return the limit to use for the next request.

        If the number of items required to reach params.number is less than the
        maximum number of items per request, return that number, otherwise
        return the maximum number of items per request.
        """
        if self.params.number is None:
            return MAX_ITEMS_PER_REQUEST
        return min(MAX_ITEMS_PER_REQUEST, self.params.number - len(self.items))

    def _next_link_from(self, response: requests.Response) -> str | None:
        """Return the next page link from the response or None if there isn't one."""
        js = response.json()
        if "links" not in js:
            return None
        nexts = [link for link in js["links"] if link["rel"] == "next"]
        if len(nexts) == 0:
            return None
        else:
            return nexts[0]["href"]

    def _total_matched_from(self, response: requests.Response) -> int:
        """Return the total number of items matched by the query."""
        js = response.json()
        return js["context"]["matched"]

    def _check_response(self, response: requests.Response):
        """Check the response for errors.

        If there is an error, raise a DataCosmosRequestError with as much
        information as possible included.
        """
        if response.ok:
            return
        try:
            js = response.json()
            # OpenCosmos standard error format
            if "errors" in js and len(js["errors"]) > 0:
                err_strings = [str(d) for d in js["errors"]]
                errs = "\n  - " + "\n  - ".join(err_strings)
            else:
                errs = "\n  - " + str(js)
        except json.decoder.JSONDecodeError:
            errs = ""
        raise DataCosmosRequestError(
            f"{response.status_code} {response.reason} for {response.url}:{errs}"
        )

    def _all_fetched(self) -> bool:
        """Return True if no more results need to be or can be fetched."""
        got_enough = (
            self.params.number is not None and len(self.items) >= self.params.number
        )
        return self._next_link is None or got_enough

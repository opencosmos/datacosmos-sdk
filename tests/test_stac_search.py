from datetime import datetime
from typing import Dict

import geojson
import pytest
from responses import matchers

from datacosmos import DataCosmos, DataCosmosCredentials
from datacosmos.const import (
    DATACOSMOS_PRODUCTION_BASE_URL,
    Constellations,
    Levels,
    Satellites,
)
from datacosmos.stac.search import SearchParams


def test_simple_search(testdata, mocked_responses):
    auth = DataCosmosCredentials("id", "secret")
    dc = DataCosmos(credentials=auth)

    mocked_responses.post(
        url=f"{DATACOSMOS_PRODUCTION_BASE_URL}/stac/search",
        json=testdata.json_from("001_search_simple/results.json"),
    )

    results = dc.search()
    assert len(results.items) == 2
    assert len(list(results)) == 2


def test_simple_search_with_parameters(testdata, mocked_responses):
    auth = DataCosmosCredentials("id", "secret")
    dc = DataCosmos(credentials=auth)

    mocked_responses.post(
        url=f"{DATACOSMOS_PRODUCTION_BASE_URL}/stac/search",
        json=testdata.json_from("001_search_simple/results.json"),
        match=[
            matchers.json_params_matcher(
                {
                    "bbox": [-180, -90, 180, 90],
                    "intersects": {"coordinates": [1, 2], "type": "Point"},
                    "limit": 20000,
                    "query": {
                        "datetime": {
                            "gte": "2021-01-01T00:00:00",
                            "lte": "2021-01-02T00:00:00",
                        },
                        "eo:cloud_cover": {"gte": 20, "lte": 40},
                        "foo": "bar",
                        "gsd": {"gte": 1, "lte": 2},
                        "processing:level": {"in": ["L2A"]},
                        "sat:platform_international_designator": {"in": ["2014-033D"]},
                    },
                }
            )
        ],
    )

    results = dc.search(
        satellites=[Satellites.GEOSAT_2],
        levels=[Levels.L2A],
        after=datetime(2021, 1, 1),
        before=datetime(2021, 1, 2),
        bbox=[-180, -90, 180, 90],
        intersects=geojson.Point([1, 2]),
        min_cloud_cover_pct=20,
        max_cloud_cover_pct=40,
        min_resolution_m=1,
        max_resolution_m=2,
        query={"foo": "bar"},
    )
    assert len(results.items) == 2
    assert len(list(results)) == 2
    assert results.matched == 937433


def test_search_pagination(testdata, mocked_responses):
    auth = DataCosmosCredentials("id", "secret")
    dc = DataCosmos(credentials=auth)

    mocked_responses.post(
        url=f"{DATACOSMOS_PRODUCTION_BASE_URL}/stac/search",
        json=testdata.json_from("002_search_pagination/page_1.json"),
    )

    results = dc.search(number=2)

    assert len(results.items) == 1
    assert results.items[0].id == "L2A-30-T-TK-2023-5-4-0"
    assert not results._all_fetched()

    mocked_responses.post(
        url=f"{DATACOSMOS_PRODUCTION_BASE_URL}/stac/search?cursor=L2A-30-T-TK-2023-5-4-0",
        json=testdata.json_from("002_search_pagination/page_2.json"),
    )

    # list() will exhaust the iterator, fetching all pages until we reach the desired number
    assert len(list(results)) == 2
    assert len(results.items) == 2
    assert results.items[1].id == "L2A-30-U-XC-2023-5-4-0"
    assert results._all_fetched()


@pytest.mark.parametrize(
    "params,expected",
    [
        (
            SearchParams(constellations=[Constellations.OPEN_CONSTELLATION]),
            {"query": {"constellation": {"in": ["open-constellation"]}}},
        ),
        (
            SearchParams(satellites=[Satellites.GEOSAT_2]),
            {"query": {"sat:platform_international_designator": {"in": ["2014-033D"]}}},
        ),
        (
            SearchParams(levels=[Levels.L2A]),
            {"query": {"processing:level": {"in": ["L2A"]}}},
        ),
        (
            SearchParams(after=datetime(2021, 1, 1), before=datetime(2021, 1, 2)),
            {
                "query": {
                    "datetime": {
                        "gte": "2021-01-01T00:00:00",
                        "lte": "2021-01-02T00:00:00",
                    }
                }
            },
        ),
        (
            SearchParams(bbox=[-180, -90, 180, 90]),
            {"bbox": [-180, -90, 180, 90]},
        ),
        (
            SearchParams(intersects=geojson.Point([1, 2])),
            {"intersects": {"type": "Point", "coordinates": [1, 2]}},
        ),
        (
            SearchParams(min_cloud_cover_pct=20, max_cloud_cover_pct=40),
            {"query": {"eo:cloud_cover": {"gte": 20, "lte": 40}}},
        ),
        (
            SearchParams(min_resolution_m=1, max_resolution_m=2),
            {"query": {"gsd": {"gte": 1, "lte": 2}}},
        ),
        (
            SearchParams(min_resolution_m=1, max_resolution_m=2, query={"foo": "bar"}),
            {"query": {"gsd": {"gte": 1, "lte": 2}, "foo": "bar"}},
        ),
    ],
)
def test_params_build(params: SearchParams, expected: Dict):
    assert params.build() == expected

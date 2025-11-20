import pytest

from datacosmos.exceptions import StacValidationError
from datacosmos.stac.constants.satellite_name_mapping import SATELLITE_NAME_MAPPING
from datacosmos.stac.enums.processing_level import ProcessingLevel
from datacosmos.stac.enums.product_type import ProductType
from datacosmos.stac.enums.season import Season
from datacosmos.stac.item.models.catalog_search_parameters import (
    CatalogSearchParameters,
)


class TestCatalogSearchParameters:
    def test_valid_parameters_parsing(self):
        params = CatalogSearchParameters(
            start_date="05/15/2024",
            end_date="05/16/2024",
            seasons=["Winter"],
            satellite=["MANTIS"],
            product_type=["Satellite"],
            processing_level=["l1A"],
            collections=["collection1"],
        )

        assert params.start_date == "2024-05-15T00:00:00Z"
        assert params.end_date.startswith("2024-05-16T")
        assert params.seasons == [Season.WINTER]
        assert params.product_type == [ProductType.SATELLITE]
        assert params.processing_level == [ProcessingLevel.L1A]
        assert params.collections == ["collection1"]

    def test_invalid_start_date_format(self):
        with pytest.raises(StacValidationError):
            CatalogSearchParameters(start_date="2024/222/1")

    def test_invalid_end_date_format(self):
        with pytest.raises(StacValidationError):
            CatalogSearchParameters(end_date="May 15, 2024")

    def test_start_date_before_2015(self):
        with pytest.raises(
            StacValidationError, match="Date must be 5/15/2015 or later."
        ):
            CatalogSearchParameters(start_date="05/10/2015")

    def test_end_date_before_start_date(self):
        with pytest.raises(
            StacValidationError, match="end_date cannot be before start_date"
        ):
            CatalogSearchParameters(start_date="05/20/2024", end_date="05/19/2024")

    def test_to_query_output(self):
        params = CatalogSearchParameters(
            start_date="05/15/2024",
            end_date="05/16/2024",
            seasons=["Summer"],
            satellite=["MANTIS"],
            product_type=["Satellite"],
            processing_level=["l1A"],
        )

        query = params.to_query()

        assert query["datetime"] == {
            "gte": "2024-05-15T00:00:00Z",
            "lte": params.end_date,
        }
        assert query["opencosmos:season"] == {"in": ["Summer"]}
        assert query["opencosmos:product_type"] == {"in": ["Satellite"]}
        assert query["processing:level"] == {"in": ["l1A"]}
        assert query["sat:platform_international_designator"] == {
            "in": [SATELLITE_NAME_MAPPING["MANTIS"]]
        }

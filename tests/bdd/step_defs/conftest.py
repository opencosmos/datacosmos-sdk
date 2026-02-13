"""Step-level fixtures for BDD tests."""

import pytest
from pytest_bdd import given, parsers

from tests.bdd.conftest import (
    STAC_BASE_URL,
    STORAGE_BASE_URL,
    PROJECT_BASE_URL,
    sample_item_dict,
    sample_collection_dict,
)


"""Shared fixtures for BDD tests."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import responses

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient

# Base URLs matching the project's config.yaml
# These must match what the SDK config loads from config/config.yaml
STAC_BASE_URL = "https://test.app.open-cosmos.com/api/data/v0/stac"
STORAGE_BASE_URL = "https://test.app.open-cosmos.com/api/data/v0/storage"
PUBLIC_STORAGE_BASE_URL = "https://test.app.open-cosmos.com/api/data/v0/storage"
PROJECT_BASE_URL = "https://test.app.open-cosmos.com/api/data/v0/scenario"
TOKEN_URL = "https://login.open-cosmos.com/oauth/token"


@dataclass
class ScenarioContext:
    """Context object to pass state between Given/When/Then steps."""

    # Request/response state
    result: Any = None
    exception: Exception | None = None
    response_status: int = 200

    # Items
    item_id: str = ""
    collection_id: str = ""
    items: list = field(default_factory=list)

    # Collections
    collections: list = field(default_factory=list)

    # Projects
    scenario_id: str = ""
    project_items: list = field(default_factory=list)

    # Storage
    assets_path: str = ""
    upload_result: Any = None
    download_result: Any = None
    delete_result: Any = None

    # Search parameters
    search_params: Any = None

    # Additional context
    extra: dict = field(default_factory=dict)


@pytest.fixture
def context():
    """Provide a fresh context for each scenario."""
    return ScenarioContext()


@pytest.fixture
def mock_responses():
    """Provide responses mock for HTTP request mocking."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        # Mock OAuth token endpoint by default
        rsps.add(
            responses.POST,
            TOKEN_URL,
            json={
                "access_token": "mock-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status=200,
        )
        yield rsps


@pytest.fixture
def mock_config():
    """Provide a mock configuration for the DatacosmosClient."""
    return Config(
        authentication=M2MAuthenticationConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
    )


@pytest.fixture
def mock_datacosmos_client(mock_responses, mock_config):
    """Provide a DatacosmosClient with mocked authentication."""
    import requests
    from datetime import timedelta

    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        # Create a real requests session with Bearer token
        mock_http_client = requests.Session()
        mock_http_client.headers["Authorization"] = "Bearer mock-access-token"
        mock_auth.return_value = mock_http_client

        # Create client that uses the mock
        client = DatacosmosClient(config=mock_config)
        client._http_client = mock_http_client
        
        # Set token attributes to prevent refresh
        client.token = "mock-access-token"
        client.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        client._owns_session = True
        
        # Set authenticator to prevent refresh errors
        mock_authenticator = MagicMock()
        mock_authenticator.refresh_token.return_value = MagicMock(
            token="mock-access-token",
            token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            http_client=mock_http_client,
        )
        client._authenticator = mock_authenticator

        yield client


@pytest.fixture
def stac_client(mock_datacosmos_client):
    """Provide a STACClient wrapping the mocked DatacosmosClient."""
    return STACClient(mock_datacosmos_client)


# Sample data fixtures


def sample_item_dict(
    item_id: str = "test-item",
    collection_id: str = "test-collection",
    geometry: dict | None = None,
    bbox: list | None = None,
    properties: dict | None = None,
    assets: dict | None = None,
) -> dict:
    """Generate a sample STAC item dictionary."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": item_id,
        "geometry": geometry or {"type": "Point", "coordinates": [102.0, 0.5]},
        "bbox": bbox or [101.0, 0.0, 103.0, 1.0],
        "properties": properties
        or {"datetime": now, "processing:level": "L1A"},
        "links": [
            {
                "rel": "self",
                "href": f"{STAC_BASE_URL}/collections/{collection_id}/items/{item_id}",
            },
            {
                "rel": "parent",
                "href": f"{STAC_BASE_URL}/collections/{collection_id}",
            },
            {"rel": "collection", "href": f"{STAC_BASE_URL}/collections/{collection_id}"},
        ],
        "assets": assets
        or {
            "thumbnail": {
                "href": f"{PUBLIC_STORAGE_BASE_URL}/{collection_id}/{item_id}/thumbnail.png",
                "type": "image/png",
                "roles": ["thumbnail"],
            }
        },
        "collection": collection_id,
    }


def sample_collection_dict(
    collection_id: str = "test-collection",
    title: str = "Test Collection",
    description: str = "A test collection",
    license: str = "MIT",
) -> dict:
    """Generate a sample STAC collection dictionary."""
    return {
        "type": "Collection",
        "stac_version": "1.0.0",
        "id": collection_id,
        "title": title,
        "description": description,
        "license": license,
        "extent": {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {"interval": [["2023-01-01T00:00:00Z", None]]},
        },
        "links": [
            {"rel": "self", "href": f"{STAC_BASE_URL}/collections/{collection_id}"},
            {"rel": "root", "href": STAC_BASE_URL},
        ],
    }


def sample_search_response(
    items: list[dict], next_link: str | None = None
) -> dict:
    """Generate a sample STAC search response."""
    response = {
        "type": "FeatureCollection",
        "features": items,
        "links": [{"rel": "self", "href": f"{STAC_BASE_URL}/search"}],
        "numberMatched": len(items),
        "numberReturned": len(items),
    }
    if next_link:
        response["links"].append({"rel": "next", "href": next_link})
    return response


def sample_collections_response(
    collections: list[dict], next_link: str | None = None
) -> dict:
    """Generate a sample collections list response."""
    response = {
        "collections": collections,
        "links": [{"rel": "self", "href": f"{STAC_BASE_URL}/collections"}],
    }
    if next_link:
        response["links"].append({"rel": "next", "href": next_link})
    return response


def sample_error_response(
    status: int, message: str, error_code: str = "ERROR"
) -> dict:
    """Generate a sample API error response."""
    return {
        "statusCode": status,
        "error": error_code,
        "message": message,
    }

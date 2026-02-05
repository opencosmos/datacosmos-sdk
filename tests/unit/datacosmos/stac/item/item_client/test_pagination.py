"""Tests for STAC search pagination behavior."""

from unittest.mock import MagicMock, patch

import pytest

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.catalog_search_parameters import (
    CatalogSearchParameters,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://mock.token.url/oauth/token",
            audience="https://mock.audience",
        )
    )


@pytest.fixture
def mock_item():
    """Create a mock STAC item for testing."""
    return {
        "id": "item-1",
        "collection": "test-collection",
        "type": "Feature",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {"datetime": "2025-02-09T12:00:00Z"},
        "assets": {},
        "links": [],
    }


class TestExtractPaginationToken:
    """Tests for _extract_pagination_token method."""

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    def test_extracts_cursor_from_valid_url(self, mock_fetch_token, mock_config):
        """Test that cursor is correctly extracted from a valid next link URL."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        next_url = (
            "https://api.example.com/stac/search?"
            "token=next%3Acollection%3Aitem123&"
            "cursor=next%3Acollection%3Aitem123&"
            "limit=50"
        )

        token = stac_client._extract_pagination_token(next_url)

        assert token == "next:collection:item123"

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    def test_returns_none_when_no_cursor_param(self, mock_fetch_token, mock_config):
        """Test that None is returned when cursor parameter is missing."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        next_url = "https://api.example.com/stac/search?limit=50"

        token = stac_client._extract_pagination_token(next_url)

        assert token is None

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    def test_handles_url_with_encoded_characters(self, mock_fetch_token, mock_config):
        """Test that URL-encoded cursor values are properly decoded."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        # URL with encoded colons (%3A)
        next_url = (
            "https://api.example.com/stac/search?"
            "cursor=next%3Acollection%3Aitem%3A123"
        )

        token = stac_client._extract_pagination_token(next_url)

        assert token == "next:collection:item:123"


class TestPaginationLoop:
    """Tests for pagination loop behavior in _paginate_items."""

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    @patch("datacosmos.stac.item.item_client.check_api_response")
    @patch.object(DatacosmosClient, "post")
    def test_cursor_added_to_body_for_subsequent_requests(
        self, mock_post, mock_check_api_response, mock_fetch_token, mock_config, mock_item
    ):
        """Test that cursor is added to the POST body for pagination requests."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        # First response with next link
        first_response = MagicMock()
        first_response.status_code = 200
        first_response.json.return_value = {
            "features": [mock_item],
            "links": [
                {
                    "rel": "next",
                    "href": "https://api.example.com/stac/search?cursor=page2token",
                }
            ],
        }

        # Second response without next link (last page)
        second_response = MagicMock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "features": [dict(mock_item, id="item-2")],
            "links": [],
        }

        mock_post.side_effect = [first_response, second_response]
        mock_check_api_response.return_value = None

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        parameters = CatalogSearchParameters(
            start_date="2/9/2025",
            end_date="2/9/2025",
        )

        results = list(stac_client.search_items(parameters, project_id="test-project"))

        assert len(results) == 2
        assert mock_post.call_count == 2

        # Verify second call includes cursor in body
        second_call_body = mock_post.call_args_list[1][1]["json"]
        assert "cursor" in second_call_body
        assert second_call_body["cursor"] == "page2token"

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    @patch("datacosmos.stac.item.item_client.check_api_response")
    @patch.object(DatacosmosClient, "post")
    def test_pagination_stops_when_no_next_link(
        self, mock_post, mock_check_api_response, mock_fetch_token, mock_config, mock_item
    ):
        """Test that pagination stops when no next link is present."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [mock_item],
            "links": [],  # No next link
        }
        mock_post.return_value = mock_response
        mock_check_api_response.return_value = None

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        parameters = CatalogSearchParameters(
            start_date="2/9/2025",
            end_date="2/9/2025",
        )

        results = list(stac_client.search_items(parameters, project_id="test-project"))

        assert len(results) == 1
        assert mock_post.call_count == 1

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    @patch("datacosmos.stac.item.item_client.check_api_response")
    @patch.object(DatacosmosClient, "post")
    def test_pagination_stops_when_next_link_has_no_cursor(
        self, mock_post, mock_check_api_response, mock_fetch_token, mock_config, mock_item
    ):
        """Test that pagination stops when next link URL has no cursor parameter."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [mock_item],
            "links": [
                {
                    "rel": "next",
                    "href": "https://api.example.com/stac/search?limit=50",  # No cursor
                }
            ],
        }
        mock_post.return_value = mock_response
        mock_check_api_response.return_value = None

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        parameters = CatalogSearchParameters(
            start_date="2/9/2025",
            end_date="2/9/2025",
        )

        results = list(stac_client.search_items(parameters, project_id="test-project"))

        assert len(results) == 1
        assert mock_post.call_count == 1

    @patch("requests_oauthlib.OAuth2Session.fetch_token")
    @patch("datacosmos.stac.item.item_client.check_api_response")
    @patch.object(DatacosmosClient, "post")
    def test_original_body_not_mutated(
        self, mock_post, mock_check_api_response, mock_fetch_token, mock_config, mock_item
    ):
        """Test that the original body dict is not mutated during pagination."""
        mock_fetch_token.return_value = {
            "access_token": "mock-token",
            "expires_in": 3600,
        }

        # Two pages of results
        first_response = MagicMock()
        first_response.status_code = 200
        first_response.json.return_value = {
            "features": [mock_item],
            "links": [
                {
                    "rel": "next",
                    "href": "https://api.example.com/stac/search?cursor=page2",
                }
            ],
        }

        second_response = MagicMock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "features": [dict(mock_item, id="item-2")],
            "links": [],
        }

        mock_post.side_effect = [first_response, second_response]
        mock_check_api_response.return_value = None

        client = DatacosmosClient(config=mock_config)
        stac_client = ItemClient(client)

        # Create body and keep reference
        original_body = {"project": "test", "limit": 50, "query": {}}

        # Call _paginate_items directly
        url = stac_client.base_url.with_suffix("/search")
        list(stac_client._paginate_items(url, original_body))

        # Original body should not have cursor
        assert "cursor" not in original_body

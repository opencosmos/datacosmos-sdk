"""Tests for ProjectItemClient.search_project_items method."""

from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient
from datacosmos.stac.project.models.project_search_parameters import (
    ProjectSearchParameters,
)


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_search_project_items(mock_post, mock_check_api_response, mock_fetch_token):
    """Test searching for items in a project/scenario."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "item-1",
                "type": "Feature",
                "stac_version": "1.1.0",
                "stac_extensions": [],
                "collection": "test-collection",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
                    ],
                },
                "bbox": [0.0, 0.0, 1.0, 1.0],
                "properties": {"datetime": "2023-01-01T10:30:09Z"},
                "links": [],
                "assets": {},
            },
        ],
        "links": [],
    }
    mock_post.return_value = mock_response
    mock_check_api_response.return_value = None

    config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://mock.token.url/oauth/token",
            audience="https://mock.audience",
        )
    )

    client = DatacosmosClient(config=config)
    project_client = ProjectItemClient(client)

    params = ProjectSearchParameters(
        collections=["test-collection"],
        limit=10,
    )
    items = list(project_client.search_project_items("scenario-123", params))

    assert len(items) == 1
    assert items[0].id == "item-1"
    mock_post.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_search_project_items_no_params(
    mock_post, mock_check_api_response, mock_fetch_token
):
    """Test searching for items in a project without parameters."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "type": "FeatureCollection",
        "features": [],
        "links": [],
    }
    mock_post.return_value = mock_response
    mock_check_api_response.return_value = None

    config = Config(
        authentication=M2MAuthenticationConfig(
            type="m2m",
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://mock.token.url/oauth/token",
            audience="https://mock.audience",
        )
    )

    client = DatacosmosClient(config=config)
    project_client = ProjectItemClient(client)

    items = list(project_client.search_project_items("scenario-123"))

    assert len(items) == 0
    mock_post.assert_called_once()

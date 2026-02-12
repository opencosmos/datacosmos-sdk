"""Tests for ProjectItemClient.create_project_item method."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pystac import Item

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_create_project_item(mock_post, mock_check_api_response, mock_fetch_token):
    """Test creating a new item in a project/scenario."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 201
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

    item = Item(
        id="new-item-789",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
            ],
        },
        bbox=[0.0, 0.0, 1.0, 1.0],
        datetime=datetime(2023, 1, 1, 10, 30, 9, tzinfo=timezone.utc),
        properties={},
    )

    project_client.create_project_item("scenario-123", item)

    mock_post.assert_called_once_with(
        project_client.project_base_url.with_suffix("/scenario/scenario-123/items"),
        json=item.to_dict(),
    )
    mock_check_api_response.assert_called_once_with(mock_response)


@patch("requests_oauthlib.OAuth2Session.fetch_token")
def test_create_project_item_no_id(mock_fetch_token):
    """Test creating an item without ID raises ValueError."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

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

    item = Item(
        id="",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
            ],
        },
        bbox=[0.0, 0.0, 1.0, 1.0],
        datetime=datetime(2023, 1, 1, 10, 30, 9, tzinfo=timezone.utc),
        properties={},
    )

    with pytest.raises(ValueError, match="no item_id found on item"):
        project_client.create_project_item("scenario-123", item)

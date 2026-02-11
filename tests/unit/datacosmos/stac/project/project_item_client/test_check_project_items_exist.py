"""Tests for ProjectItemClient.check_project_items_exist method."""

from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient
from datacosmos.stac.project.models.collection_item_pair import CollectionItemPair


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_check_project_items_exist(
    mock_post, mock_check_api_response, mock_fetch_token
):
    """Test checking if items exist in a project/scenario."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "collection": "collection-1",
            "item": "item-1",
            "relation": "rel-123",
            "exists": True,
        },
        {
            "collection": "collection-2",
            "item": "item-2",
            "relation": None,
            "exists": False,
        },
    ]
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

    items = [
        CollectionItemPair(collection="collection-1", item="item-1"),
        CollectionItemPair(collection="collection-2", item="item-2"),
    ]
    results = project_client.check_project_items_exist("scenario-123", items)

    assert len(results) == 2
    assert results[0].collection == "collection-1"
    assert results[0].item == "item-1"
    assert results[0].exists is True
    assert results[0].relation == "rel-123"
    assert results[1].collection == "collection-2"
    assert results[1].item == "item-2"
    assert results[1].exists is False
    assert results[1].relation is None
    mock_post.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)

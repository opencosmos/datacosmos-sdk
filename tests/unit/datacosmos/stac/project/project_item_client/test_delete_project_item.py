"""Tests for ProjectItemClient.delete_project_item method."""

from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "delete")
def test_delete_project_item(mock_delete, mock_check_api_response, mock_fetch_token):
    """Test deleting an item from a project/scenario."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_delete.return_value = mock_response
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

    project_client.delete_project_item("scenario-123", "item-456")

    mock_delete.assert_called_once_with(
        project_client.project_base_url.with_suffix(
            "/scenario/scenario-123/items/item-456"
        )
    )
    mock_check_api_response.assert_called_once_with(mock_response)

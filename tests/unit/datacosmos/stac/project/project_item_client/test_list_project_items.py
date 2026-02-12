"""Tests for ProjectItemClient.list_project_items method."""

from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.project.project_item_client import ProjectItemClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.project.project_item_client.check_api_response")
@patch.object(DatacosmosClient, "get")
def test_list_project_items(mock_get, mock_check_api_response, mock_fetch_token):
    """Test listing items in a project/scenario."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
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
                {
                    "id": "item-2",
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
                    "properties": {"datetime": "2023-01-02T10:30:09Z"},
                    "links": [],
                    "assets": {},
                },
            ],
        }
    }
    mock_get.return_value = mock_response
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

    items = list(project_client.list_project_items("scenario-123"))

    assert len(items) == 2
    assert items[0].id == "item-1"
    assert items[1].id == "item-2"
    mock_get.assert_called_once_with(
        project_client.project_base_url.with_suffix("/scenario/scenario-123/items")
    )
    mock_check_api_response.assert_called_once_with(mock_response)

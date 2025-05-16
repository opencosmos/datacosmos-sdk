from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.item.item_client import ItemClient
from datacosmos.stac.item.models.catalog_search_parameters import (
    CatalogSearchParameters,
)


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.item.item_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_search_items(mock_post, mock_check_api_response, mock_fetch_token):
    """Test searching STAC items with CatalogSearchParameters."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "features": [
            {
                "id": "item-1",
                "collection": "test-collection",
                "type": "Feature",
                "stac_version": "1.0.0",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"datetime": "2025-02-09T12:00:00Z"},
                "assets": {},
                "links": [],
            }
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
    stac_client = ItemClient(client)

    parameters = CatalogSearchParameters(
        start_date="2/9/2025",
        end_date="2/9/2025",
        satellite=["MANTIS"],
        product_type=["Satellite"],
        processing_level=["L1A"],
    )

    project_id = "mock-project"

    results = list(stac_client.search_items(parameters, project_id=project_id))

    assert len(results) == 1
    assert results[0].id == "item-1"

    expected_body = {"project": project_id, "limit": 50, "query": parameters.to_query()}

    mock_post.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)
    mock_post.assert_called_with(
        stac_client.base_url.with_suffix("/search"), json=expected_body
    )

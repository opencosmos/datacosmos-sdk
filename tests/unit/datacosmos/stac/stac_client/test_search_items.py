from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient
from datacosmos.stac.models.search_parameters import SearchParameters
from datacosmos.stac.stac_client import STACClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.stac_client.check_api_response")
@patch.object(DatacosmosClient, "post")
def test_search_items(mock_post, mock_check_api_response, mock_fetch_token):
    """Test searching STAC items with filters and pagination."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200  # Ensure the mock behaves like a real response
    mock_response.json.return_value = {
        "features": [
            {
                "id": "item-1",
                "collection": "test-collection",
                "type": "Feature",
                "stac_version": "1.0.0",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"datetime": "2023-12-01T12:00:00Z"},
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
    stac_client = STACClient(client)
    parameters = SearchParameters(collections=["test-collection"])

    results = list(stac_client.search_items(parameters))

    assert len(results) == 1
    assert results[0].id == "item-1"
    mock_post.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)  # Ensure the API check was called

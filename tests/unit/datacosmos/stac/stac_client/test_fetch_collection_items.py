from unittest.mock import MagicMock, patch

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.client import DatacosmosClient
from datacosmos.stac.stac_client import STACClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch("datacosmos.stac.stac_client.check_api_response")
@patch.object(STACClient, "search_items")
def test_fetch_collection_items(
    mock_search_items, mock_check_api_response, mock_fetch_token
):
    """Test fetching all items in a collection."""
    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response_1 = MagicMock(id="item-1")
    mock_response_2 = MagicMock(id="item-2")

    mock_search_items.return_value = iter([mock_response_1, mock_response_2])

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

    results = list(stac_client.fetch_collection_items("test-collection"))

    assert len(results) == 2
    assert results[0].id == "item-1"
    assert results[1].id == "item-2"

    mock_search_items.assert_called_once()
    mock_check_api_response.assert_not_called()

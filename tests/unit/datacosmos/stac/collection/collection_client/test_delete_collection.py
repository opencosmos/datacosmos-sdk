from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.collection.collection_client import CollectionClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "delete")
@patch("datacosmos.stac.collection.collection_client.check_api_response")
def test_delete_collection(mock_check_api_response, mock_delete, mock_fetch_token):
    """Test deleting a STAC collection."""

    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 204
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
    collection_client = CollectionClient(client)

    collection_client.delete_collection("test-collection")

    mock_delete.assert_called_once_with(
        client.config.stac.as_domain_url().with_suffix("/collections/test-collection")
    )

    mock_check_api_response.assert_called_once_with(mock_response)
    mock_delete.assert_called_with(
        collection_client.base_url.with_suffix("/collections/test-collection")
    )

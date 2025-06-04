from unittest.mock import MagicMock, patch

from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.collection.collection_client import CollectionClient
from datacosmos.stac.collection.models.collection_update import CollectionUpdate


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "patch")
@patch("datacosmos.stac.collection.collection_client.check_api_response")
def test_update_collection(mock_check_api_response, mock_patch, mock_fetch_token):
    """Test updating a STAC collection."""

    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response
    mock_check_api_response.return_value = None

    update_data = CollectionUpdate(
        title="Updated Collection Title",
        description="Updated description",
        keywords=["updated", "collection"],
        license="proprietary",
    )

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

    collection_client.update_collection("test-collection", update_data)

    mock_patch.assert_called_once_with(
        client.config.stac.as_domain_url().with_suffix("/collections/test-collection"),
        json=update_data.model_dump(by_alias=True, exclude_none=True),
    )

    mock_check_api_response.assert_called_once_with(mock_response)
    mock_patch.assert_called_with(
        collection_client.base_url.with_suffix("/collections/test-collection"),
        json=update_data.model_dump(by_alias=True, exclude_none=True),
    )

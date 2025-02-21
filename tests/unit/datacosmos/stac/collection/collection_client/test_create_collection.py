from unittest.mock import MagicMock, patch

from pystac import Collection, Extent, SpatialExtent, TemporalExtent
from pystac.utils import str_to_datetime

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.collection.collection_client import CollectionClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "post")
@patch("datacosmos.stac.collection.collection_client.check_api_response")
def test_create_collection(mock_check_api_response, mock_post, mock_fetch_token):
    """Test creating a STAC collection."""

    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    mock_check_api_response.return_value = None

    collection = Collection(
        id="test-collection",
        description="A test STAC collection",
        extent=Extent(
            SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            TemporalExtent(
                [
                    [
                        str_to_datetime("2020-01-01T00:00:00Z"),
                        str_to_datetime("2023-12-31T23:59:59Z"),
                    ]
                ]
            ),
        ),
        license="proprietary",
        stac_extensions=[],
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

    collection_client.create_collection(collection)

    mock_post.assert_called_once_with(
        client.config.stac.as_domain_url().with_suffix("/collections"),
        json=collection.to_dict(),
    )

    mock_check_api_response.assert_called_once_with(mock_response)

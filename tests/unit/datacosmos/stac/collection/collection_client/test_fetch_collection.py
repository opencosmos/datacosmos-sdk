from unittest.mock import MagicMock, patch

from pystac import Collection
from pystac.utils import datetime_to_str

from config.config import Config
from config.models.m2m_authentication_config import M2MAuthenticationConfig
from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.stac.collection.collection_client import CollectionClient


@patch("requests_oauthlib.OAuth2Session.fetch_token")
@patch.object(DatacosmosClient, "get")
@patch("datacosmos.stac.collection.collection_client.check_api_response")
def test_fetch_collection(mock_check_api_response, mock_get, mock_fetch_token):
    """Test fetching a single STAC collection by ID."""

    mock_fetch_token.return_value = {"access_token": "mock-token", "expires_in": 3600}

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "type": "Collection",
        "id": "test-collection",
        "stac_version": "1.1.0",
        "description": "A test STAC collection",
        "license": "proprietary",
        "extent": {
            "spatial": {"bbox": [[-180.0, -90.0, 180.0, 90.0]]},
            "temporal": {
                "interval": [["2020-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]]
            },
        },
        "links": [],
        "stac_extensions": [],
    }
    mock_response.status_code = 200
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
    collection_client = CollectionClient(client)

    collection = collection_client.fetch_collection("test-collection")

    assert isinstance(collection, Collection)
    assert collection.id == "test-collection"
    assert collection.description == "A test STAC collection"
    assert collection.license == "proprietary"
    assert collection.extent.spatial.bboxes == [[-180.0, -90.0, 180.0, 90.0]]

    actual_temporal_intervals = [
        [datetime_to_str(interval[0]), datetime_to_str(interval[1])]
        for interval in collection.extent.temporal.intervals
    ]
    expected_temporal_intervals = [["2020-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]]

    assert actual_temporal_intervals == expected_temporal_intervals

    mock_get.assert_called_once()
    mock_check_api_response.assert_called_once_with(mock_response)
    mock_get.assert_called_with(
        collection_client.base_url.with_suffix("/collections/test-collection")
    )

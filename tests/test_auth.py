import json

import responses
from responses import matchers

from datacosmos import DataCosmos, DataCosmosCredentials
from datacosmos.const import DATACOSMOS_PRODUCTION_BASE_URL, DATACOSMOS_TOKEN_URL


def test_credentials_from_environment(monkeypatch):
    monkeypatch.setenv("DATACOSMOS_KEY_ID", "id")
    monkeypatch.setenv("DATACOSMOS_KEY_SECRET", "secret")
    credentials = DataCosmosCredentials.from_env()
    assert credentials.client_id == "id"
    assert credentials.client_secret == "secret"


def test_credentials_from_environment_by_default(monkeypatch, mocked_responses):
    monkeypatch.setenv("DATACOSMOS_KEY_ID", "id")
    monkeypatch.setenv("DATACOSMOS_KEY_SECRET", "secret")
    responses.post(
        url=DATACOSMOS_TOKEN_URL,
        json={
            "access_token": "my_token",
            "scope": "data",
            "expires_in": 86400,
            "token_type": "Bearer",
        },
    )
    dc = DataCosmos()
    assert dc.credentials.client_id == "id"
    assert dc.credentials.client_secret == "secret"


def test_credentials_from_file_helper(tmp_path, mocked_responses):
    filename = tmp_path / "credentials.json"
    data = {"id": "id", "secret": "secret"}
    filename.write_text(json.dumps(data))
    dc = DataCosmos.with_credentials_from(filename)
    assert dc.credentials.client_id == "id"
    assert dc.credentials.client_secret == "secret"


def test_credentials_from_file(tmp_path):
    filename = tmp_path / "credentials.json"
    data = {"id": "id", "secret": "secret"}
    filename.write_text(json.dumps(data))
    credentials = DataCosmosCredentials.from_file(filename, audience="abc")
    assert credentials.client_id == "id"
    assert credentials.client_secret == "secret"
    assert credentials.audience == "abc"


@responses.activate
def test_simple_search_contains_token(testdata):
    responses.post(
        url=DATACOSMOS_TOKEN_URL,
        json={
            "access_token": "my_token",
            "scope": "data",
            "expires_in": 86400,
            "token_type": "Bearer",
        },
    )

    credentials = DataCosmosCredentials("id", "secret")
    dc = DataCosmos(credentials=credentials)

    responses.post(
        url=f"{DATACOSMOS_PRODUCTION_BASE_URL}/stac/search",
        json=testdata.json_from("001_search_simple/results.json"),
        match=[matchers.header_matcher({"Authorization": "Bearer my_token"})],
    )

    # responses will error if the token is not matched in the search request
    dc.search()

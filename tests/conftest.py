import json
from pathlib import Path

import pytest
import responses

from datacosmos.const import DATACOSMOS_TOKEN_URL


class TestData:
    testdata_dir = Path(__file__).parent.parent / "testdata"

    @staticmethod
    def string_from(filename: str) -> str:
        return (TestData.testdata_dir / filename).read_text()

    @staticmethod
    def json_from(filename: str) -> dict:
        return json.loads(TestData.string_from(filename))


@pytest.fixture
def testdata():
    return TestData


@pytest.fixture(scope="function")
def mocked_responses():
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=DATACOSMOS_TOKEN_URL,
            json={
                "access_token": "my_token",
                "scope": "data",
                "expires_in": 86400,
                "token_type": "Bearer",
            },
        )
        yield rsps

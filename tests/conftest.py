import json
from pathlib import Path

import pytest

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

import pytest
from pydantic import ValidationError

from config.models.url import URL
from datacosmos.utils.url import URL as DomainURL


class TestURL:
    def test_valid_url_initialization(self):
        url = URL(protocol="https", host="example.com", port=443, path="/api/v1")
        assert url.protocol == "https"
        assert url.host == "example.com"
        assert url.port == 443
        assert url.path == "/api/v1"

    def test_as_domain_url(self):
        url = URL(protocol="http", host="localhost", port=8080, path="/test")
        domain_url = url.as_domain_url()

        assert isinstance(domain_url, DomainURL)
        assert domain_url.protocol == "http"
        assert domain_url.host == "localhost"
        assert domain_url.port == 8080
        assert domain_url.base == "/test"

    def test_missing_required_fields_raises_validation_error(self):
        with pytest.raises(ValidationError):
            URL(protocol="https", port=443, path="/missing-host")

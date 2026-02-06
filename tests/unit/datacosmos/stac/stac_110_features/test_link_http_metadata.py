"""Unit tests for STAC 1.1.0 HTTP request metadata on Link objects.

STAC 1.1.0 added new fields to the Link object for HTTP request metadata:
- method: HTTP method for the request
- headers: HTTP headers for the request
- body: Request body for POST/PUT requests
Spec: https://github.com/radiantearth/stac-spec/blob/master/commons/links.md
"""

import unittest

from datacosmos.stac.item.models.link import Link


class TestStac110LinkHttpMetadata(unittest.TestCase):
    """Tests for STAC 1.1.0 HTTP request metadata on Link objects."""

    def setUp(self):
        """Set up valid link data with HTTP metadata."""
        self.valid_link_data = {
            "href": "https://api.example.com/items/123",
            "rel": "self",
            "type": "application/geo+json",
            "title": "This item",
            "method": "GET",
            "headers": {"Authorization": ["Bearer token123"]},
        }

    def test_link_with_method_field(self):
        """Test that Link model accepts the 1.1.0 method field."""
        link = Link(**self.valid_link_data)

        self.assertEqual(link.method, "GET")

    def test_link_with_headers_field(self):
        """Test that Link model accepts the 1.1.0 headers field."""
        link = Link(**self.valid_link_data)

        self.assertIsNotNone(link.headers)
        self.assertEqual(link.headers["Authorization"], ["Bearer token123"])

    def test_link_with_body_field(self):
        """Test that Link model accepts the 1.1.0 body field."""
        link_data = {**self.valid_link_data}
        link_data["method"] = "POST"
        link_data["body"] = {"query": "test"}
        link = Link(**link_data)

        self.assertEqual(link.body, {"query": "test"})

    def test_link_post_with_full_metadata(self):
        """Test Link with full HTTP request metadata for POST."""
        link = Link(
            href="https://api.example.com/search",
            rel="search",
            type="application/json",
            method="POST",
            headers={"Content-Type": ["application/json"]},
            body={"collections": ["test-collection"], "limit": 10},
        )

        self.assertEqual(link.method, "POST")
        self.assertEqual(link.body["limit"], 10)

    def test_link_without_http_metadata(self):
        """Test that Link works without HTTP metadata (backward compatible)."""
        link = Link(href="https://example.com/item", rel="self")

        self.assertEqual(link.href, "https://example.com/item")
        self.assertEqual(link.rel, "self")
        self.assertIsNone(link.method)
        self.assertIsNone(link.headers)
        self.assertIsNone(link.body)


if __name__ == "__main__":
    unittest.main()

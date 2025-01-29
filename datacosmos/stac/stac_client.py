"""STAC Client module for interacting with a STAC (SpatioTemporal Asset Catalog) API.

Provides methods for querying, fetching, and paginating STAC items.
"""

from typing import Generator, Optional

import pystac

from datacosmos.client import DatacosmosClient
from datacosmos.stac.models.search_parameters import SearchParameters

class STACClient:
    """Client for interacting with the STAC API."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the STACClient with a DatacosmosClient.

        Args:
            client (DatacosmosClient): The authenticated Datacosmos client instance.
        """
        self.client = client
        self.base_url = client.config.stac.as_domain_url()

    def search_items(
        self, parameters: SearchParameters
    ) -> Generator[pystac.Item, None, None]:
        """Query the STAC catalog using the POST endpoint with filtering and pagination.

        Args:
            parameters (SearchParameters): The search parameters.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        url = self.base_url.with_suffix("/search")
        body = parameters.model_dump(by_alias=True, exclude_none=True)
        return self._paginate_items(url, body)

    def fetch_item(self, item_id: str, collection_id: str) -> pystac.Item:
        """Fetch a single STAC item by ID.

        Args:
            item_id (str): The ID of the item to fetch.
            collection_id (str): The ID of the collection containing the item.

        Returns:
            pystac.Item: The fetched STAC item.
        """
        url = self.base_url.with_suffix(f"/collections/{collection_id}/items/{item_id}")
        response = self.client.get(url)
        response.raise_for_status()
        return pystac.Item.from_dict(response.json())

    def fetch_collection_items(
        self, collection_id: str
    ) -> Generator[pystac.Item, None, None]:
        """Fetch all items in a collection with pagination.

        Args:
            collection_id (str): The ID of the collection.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        parameters = SearchParameters(collections=[collection_id])
        return self.search_items(parameters)

    def _paginate_items(
        self, url: str, body: dict
    ) -> Generator[pystac.Item, None, None]:
        """Handle pagination for the STAC search POST endpoint.

        Fetches items one page at a time using the 'next' link.

        Args:
            url (str): The base URL for the search endpoint.
            body (dict): The request body containing search parameters.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        params = {"limit": body.get("limit", 10)}  # Default limit to 10 if not provided

        while True:
            response = self.client.post(url, json=body, params=params)
            response.raise_for_status()
            data = response.json()

            yield from (
                pystac.Item.from_dict(feature) for feature in data.get("features", [])
            )

            # Get next pagination link
            next_href = self._get_next_link(data)
            if not next_href:
                break

            # Extract token for next page
            token = self._extract_pagination_token(next_href)
            if not token:
                break
            params["cursor"] = token

    def _get_next_link(self, data: dict) -> Optional[str]:
        """Extract the next page link from the response.

        Args:
            data (dict): The response JSON from the STAC API.

        Returns:
            Optional[str]: The URL for the next page, or None if no next page exists.
        """
        next_link = next(
            (link for link in data.get("links", []) if link.get("rel") == "next"), None
        )
        return next_link.get("href", "") if next_link else None

    def _extract_pagination_token(self, next_href: str) -> Optional[str]:
        """Extract the pagination token from the next link URL.

        Args:
            next_href (str): The next page URL.

        Returns:
            Optional[str]: The extracted token, or None if parsing fails.
        """
        try:
            return next_href.split("?")[1].split("=")[-1]
        except (IndexError, AttributeError):
            self.client.logger.error(
                f"Failed to parse pagination token from {next_href}"
            )
            return None

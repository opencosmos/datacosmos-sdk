"""STAC Client module for interacting with a STAC (SpatioTemporal Asset Catalog) API.

Provides methods for querying, fetching, creating, updating, and deleting STAC items.
"""

from typing import Generator, Optional

from pystac import Item

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.datacosmos_exception import DatacosmosException
from datacosmos.stac.item.models.item_update import ItemUpdate
from datacosmos.stac.item.models.search_parameters import SearchParameters
from datacosmos.utils.http_response.check_api_response import check_api_response


class ItemClient:
    """Client for interacting with the STAC API."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the STACClient with a DatacosmosClient.

        Args:
            client (DatacosmosClient): The authenticated Datacosmos client instance.
        """
        self.client = client
        self.base_url = client.config.stac.as_domain_url()

    def fetch_item(self, item_id: str, collection_id: str) -> Item:
        """Fetch a single STAC item by ID.

        Args:
            item_id (str): The ID of the item to fetch.
            collection_id (str): The ID of the collection containing the item.

        Returns:
            Item: The fetched STAC item.
        """
        url = self.base_url.with_suffix(f"/collections/{collection_id}/items/{item_id}")
        response = self.client.get(url)
        check_api_response(response)
        return Item.from_dict(response.json())

    def fetch_collection_items(
        self, collection_id: str, parameters: Optional[SearchParameters] = None
    ) -> Generator[Item, None, None]:
        """Fetch all items in a collection with optional filtering.

        Args:
            collection_id (str): The ID of the collection.
            parameters (Optional[SearchParameters]): Filtering parameters (spatial, temporal, etc.).

        Yields:
            Item: Parsed STAC item.
        """
        if parameters is None:
            parameters = SearchParameters(collections=[collection_id])

        return self.search_items(parameters)

    def search_items(self, parameters: SearchParameters) -> Generator[Item, None, None]:
        """Query the STAC catalog using the POST endpoint with filtering and pagination.

        Args:
            parameters (SearchParameters): The search parameters.

        Yields:
            Item: Parsed STAC item.
        """
        url = self.base_url.with_suffix("/search")
        body = parameters.model_dump(by_alias=True, exclude_none=True)
        return self._paginate_items(url, body)

    def create_item(self, collection_id: str, item: Item) -> None:
        """Create a new STAC item in a specified collection.

        Args:
            collection_id (str): The ID of the collection where the item will be created.
            item (Item): The STAC Item to be created.

        Raises:
            RequestError: If the API returns an error response.
        """
        url = self.base_url.with_suffix(f"/collections/{collection_id}/items")
        item_json: dict = item.to_dict()

        response = self.client.post(url, json=item_json)
        check_api_response(response)

    def update_item(
        self, item_id: str, collection_id: str, update_data: ItemUpdate
    ) -> None:
        """Partially update an existing STAC item.

        Args:
            item_id (str): The ID of the item to update.
            collection_id (str): The ID of the collection containing the item.
            update_data (ItemUpdate): The structured update payload.
        """
        url = self.base_url.with_suffix(f"/collections/{collection_id}/items/{item_id}")

        update_payload = update_data.model_dump(by_alias=True, exclude_none=True)

        if "assets" in update_payload:
            update_payload["assets"] = {
                key: asset.to_dict() for key, asset in update_payload["assets"].items()
            }
        if "links" in update_payload:
            update_payload["links"] = [
                link.to_dict() for link in update_payload["links"]
            ]

        response = self.client.patch(url, json=update_payload)
        check_api_response(response)

    def delete_item(self, item_id: str, collection_id: str) -> None:
        """Delete a STAC item by its ID.

        Args:
            item_id (str): The ID of the item to delete.
            collection_id (str): The ID of the collection containing the item.

        Raises:
            OCError: If the item is not found or deletion is forbidden.
        """
        url = self.base_url.with_suffix(f"/collections/{collection_id}/items/{item_id}")
        response = self.client.delete(url)
        check_api_response(response)

    def _paginate_items(self, url: str, body: dict) -> Generator[Item, None, None]:
        """Handle pagination for the STAC search POST endpoint.

        Fetches items one page at a time using the 'next' link.

        Args:
            url (str): The base URL for the search endpoint.
            body (dict): The request body containing search parameters.

        Yields:
            Item: Parsed STAC item.
        """
        params = {"limit": body.get("limit", 10)}

        while True:
            response = self.client.post(url, json=body, params=params)
            check_api_response(response)
            data = response.json()

            yield from (Item.from_dict(feature) for feature in data.get("features", []))

            next_href = self._get_next_link(data)
            if not next_href:
                break

            token = self._extract_pagination_token(next_href)
            if not token:
                break
            params["cursor"] = token

    def _get_next_link(self, data: dict) -> Optional[str]:
        """Extract the next page link from the response."""
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

        Raises:
            DatacosmosException: If pagination token extraction fails.
        """
        try:
            return next_href.split("?")[1].split("=")[-1]
        except (IndexError, AttributeError) as e:
            raise DatacosmosException(
                f"Failed to parse pagination token from {next_href}",
                response=e.response,
            ) from e

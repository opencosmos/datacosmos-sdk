import pystac
from typing import Generator
from datacosmos.client import DatacosmosClient
from datacosmos.stac.models.search_parameters import SearchParameters

class STACClient:
    """
    A client for interacting with the STAC API.
    """

    def __init__(self, client: DatacosmosClient):
        """
        Initialize the STACClient with a DatacosmosClient.

        Args:
            client (DatacosmosClient): The authenticated Datacosmos client instance.
        """
        self.client = client
        self.base_url = client.config.stac.as_domain_url()

    def search_items(
        self, parameters: SearchParameters
    ) -> Generator[pystac.Item, None, None]:
        """
        Query the STAC catalog using the POST endpoint with flexible filters and pagination.

        Args:
            parameters (SearchParameters): The search parameters.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        url = self.base_url.with_suffix("/search")
        body = parameters.model_dump(by_alias=True, exclude_none=True)
        return self.__paginate_items(url, body)

    def fetch_item(self, item_id: str, collection_id: str) -> pystac.Item:
        """
        Fetch a single STAC item by ID.

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

    def fetch_collection_items(self, collection_id: str) -> Generator[pystac.Item, None, None]:
        """
        Fetch all items in a collection with pagination.

        Args:
            collection_id (str): The ID of the collection.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        parameters = SearchParameters(collections=[collection_id])
        return self.search_items(parameters)

    def __paginate_items(self, url: str, body: dict) -> Generator[pystac.Item, None, None]:
        """
        Handles pagination for the STAC search POST endpoint.
        Fetches items one page at a time using the 'next' link.

        Args:
            url (str): The base URL for the search endpoint.
            body (dict): The request body containing search parameters.

        Yields:
            pystac.Item: Parsed STAC item.
        """
        params = {"limit": body.get("limit", 10)}  # Default limit to 10 if not provided

        while True:
            # Make the POST request
            response = self.client.post(url, json=body, params=params)
            response.raise_for_status()
            data = response.json()

            # Process features (STAC items)
            for feature in data.get("features", []):
                yield pystac.Item.from_dict(feature)

            # Handle pagination via the 'next' link
            next_link = next(
                (link for link in data.get("links", []) if link.get("rel") == "next"),
                None,
            )
            if next_link:
                next_href = next_link.get("href", "")

                # Validate the href
                if not next_href:
                    self.client.logger.warning("Next link href is empty. Stopping pagination.")
                    break

                # Extract token from the href
                try:
                    token = next_href.split("?")[1].split("=")[-1]
                    params["cursor"] = token
                except IndexError:
                    self.client.logger.error(f"Failed to parse pagination token from {next_href}")
                    break
            else:
                break


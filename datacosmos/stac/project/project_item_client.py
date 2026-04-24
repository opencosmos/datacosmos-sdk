"""Project Item Client module for interacting with project/scenario items.

Provides methods for listing, fetching, creating, updating, deleting, and searching
items within projects (scenarios) via the Project Service API.
"""

from typing import Generator, List, Optional
from urllib.parse import parse_qs, urlparse

from pystac import Item

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.stac.item.models.datacosmos_item import DatacosmosItem
from datacosmos.stac.project.models.collection_item_pair import CollectionItemPair
from datacosmos.stac.project.models.project_search_parameters import (
    ProjectSearchParameters,
)
from datacosmos.stac.project.models.relation_existence import RelationExistence
from datacosmos.utils.http_response.check_api_response import check_api_response


class ProjectItemClient:
    """Client for interacting with project/scenario items via the Project Service API."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the ProjectItemClient with a DatacosmosClient.

        Args:
            client (DatacosmosClient): The authenticated Datacosmos client instance.
        """
        self.client = client
        self.project_base_url = client.config.project.as_domain_url()

    def list_project_items(self, scenario_id: str) -> Generator[Item, None, None]:
        """List all items in a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.

        Yields:
            Item: STAC items belonging to the scenario.
        """
        url = self.project_base_url.with_suffix(f"/scenario/{scenario_id}/items")
        response = self.client.get(url)
        check_api_response(response)

        data = response.json()
        # Handle OC API response format with 'data' wrapper
        items_data = data.get("data", data)

        if isinstance(items_data, dict) and "features" in items_data:
            # Use `or []` to handle both missing key and null value
            features = items_data.get("features") or []
        elif isinstance(items_data, list):
            features = items_data
        else:
            features = []

        yield from (Item.from_dict(feature) for feature in features)

    def get_project_item(self, scenario_id: str, item_id: str) -> DatacosmosItem:
        """Fetch a specific item from a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.
            item_id (str): The ID of the item to fetch.

        Returns:
            DatacosmosItem: The fetched STAC item.
        """
        url = self.project_base_url.with_suffix(
            f"/scenario/{scenario_id}/items/{item_id}"
        )
        response = self.client.get(url)
        check_api_response(response)

        data = response.json()
        # Handle OC API response format with 'data' wrapper
        item_data = data.get("data", data)
        return DatacosmosItem.from_dict(item_data)

    def create_project_item(
        self, scenario_id: str, item: Item | DatacosmosItem
    ) -> None:
        """Create a new item in a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.
            item (Item | DatacosmosItem): The STAC item to create.

        Raises:
            ValueError: If the item has no ID.
        """
        if not item.id:
            raise ValueError("Cannot create item: no item_id found on item")

        url = self.project_base_url.with_suffix(f"/scenario/{scenario_id}/items")
        item_json: dict = item.to_dict()
        response = self.client.post(url, json=item_json)
        check_api_response(response)

    def add_project_item(self, scenario_id: str, item: Item | DatacosmosItem) -> None:
        """Add or update an item in a project/scenario (upsert).

        Args:
            scenario_id (str): The ID of the scenario/project.
            item (Item | DatacosmosItem): The STAC item to add or update.

        Raises:
            ValueError: If the item has no ID.
        """
        if not item.id:
            raise ValueError("Cannot add item: no item_id found on item")

        url = self.project_base_url.with_suffix(
            f"/scenario/{scenario_id}/items/{item.id}"
        )
        item_json: dict = item.to_dict()
        response = self.client.put(url, json=item_json)
        check_api_response(response)

    def delete_project_item(self, scenario_id: str, item_id: str) -> None:
        """Delete an item from a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.
            item_id (str): The ID of the item to delete.
        """
        url = self.project_base_url.with_suffix(
            f"/scenario/{scenario_id}/items/{item_id}"
        )
        response = self.client.delete(url)
        check_api_response(response)

    def search_project_items(
        self,
        scenario_id: str,
        parameters: Optional[ProjectSearchParameters] = None,
    ) -> Generator[Item, None, None]:
        """Search for items within a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.
            parameters (ProjectSearchParameters, optional): Search parameters.

        Yields:
            Item: Matching STAC items.
        """
        url = self.project_base_url.with_suffix(f"/scenario/{scenario_id}/search")
        body = parameters.to_request_body() if parameters else {}

        return self._paginate_project_items(url, body)

    def check_project_items_exist(
        self, scenario_id: str, items: List[CollectionItemPair]
    ) -> List[RelationExistence]:
        """Check if catalog items exist in a project/scenario.

        Args:
            scenario_id (str): The ID of the scenario/project.
            items (List[CollectionItemPair]): List of collection/item pairs to check.

        Returns:
            List[RelationExistence]: Existence status for each pair.
        """
        url = self.project_base_url.with_suffix(f"/scenario/{scenario_id}/contains")
        body = [item.model_dump() for item in items]
        response = self.client.post(url, json=body)
        check_api_response(response)

        data = response.json()
        # Handle both direct list response and OC API wrapper
        results = data if isinstance(data, list) else data.get("data", [])

        return [RelationExistence.model_validate(result) for result in results]

    def _paginate_project_items(
        self, url: str, body: dict
    ) -> Generator[Item, None, None]:
        """Handle pagination for the project search endpoint.

        Args:
            url: The project search endpoint URL.
            body: The request body containing search parameters.

        Yields:
            Item: Parsed STAC items from the search results.
        """
        request_body = body.copy()

        while True:
            response = self.client.post(url, json=request_body)
            check_api_response(response)
            data = response.json()

            # Use `or []` to handle both missing key and null value
            features = data.get("features") or []
            yield from (Item.from_dict(feature) for feature in features)

            next_href = self._get_next_link(data)
            if not next_href:
                break

            token = self._extract_pagination_token(next_href)
            if not token:
                break

            request_body["cursor"] = token

    def _get_next_link(self, data: dict) -> Optional[str]:
        """Extract the next page link from the response.

        Args:
            data: The JSON response data from the search endpoint.

        Returns:
            The href of the next page link, or None if not found.
        """
        next_link = next(
            (link for link in data.get("links", []) if link.get("rel") == "next"), None
        )
        return next_link.get("href", "") if next_link else None

    def _extract_pagination_token(self, next_href: str) -> Optional[str]:
        """Extract the pagination token (cursor) from the next link URL.

        Args:
            next_href: The URL of the next page from the response.

        Returns:
            The cursor token for the next page, or None if not found.
        """
        try:
            parsed = urlparse(next_href)
            query_params = parse_qs(parsed.query)
            cursor_values = query_params.get("cursor", [])
            return cursor_values[0] if cursor_values else None
        except (ValueError, TypeError) as e:
            raise DatacosmosError(
                f"Failed to parse pagination cursor from next link: {next_href}. "
                f"Expected URL with 'cursor' query parameter. Error: {e}"
            ) from e

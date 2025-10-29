"""Handles operations related to STAC collections."""

from typing import Generator, Optional

from pystac import Collection, Extent, SpatialExtent, TemporalExtent
from pystac.utils import str_to_datetime

from datacosmos.datacosmos_client import DatacosmosClient
from datacosmos.exceptions.datacosmos_error import DatacosmosError
from datacosmos.stac.collection.models.collection_update import CollectionUpdate
from datacosmos.utils.http_response.check_api_response import check_api_response


class CollectionClient:
    """Handles operations related to STAC collections."""

    def __init__(self, client: DatacosmosClient):
        """Initialize the CollectionClient with a DatacosmosClient."""
        self.client = client
        self.base_url = client.config.stac.as_domain_url()

    def fetch_collection(self, collection_id: str) -> Collection:
        """Fetch details of an existing STAC collection."""
        url = self.base_url.with_suffix(f"/collections/{collection_id}")
        response = self.client.get(url)
        check_api_response(response)
        return Collection.from_dict(response.json())

    def create_collection(self, collection: Collection) -> None:
        """Create a new STAC collection.

        Args:
            collection (Collection): The STAC collection to create.

        Raises:
            InvalidRequest: If the collection data is malformed.
        """
        if isinstance(collection.extent, dict):
            spatial_data = collection.extent.get("spatial", {}).get("bbox", [[]])
            temporal_data = collection.extent.get("temporal", {}).get("interval", [[]])

            # Convert string timestamps to datetime objects
            parsed_temporal = []
            for interval in temporal_data:
                start = str_to_datetime(interval[0]) if interval[0] else None
                end = (
                    str_to_datetime(interval[1])
                    if len(interval) > 1 and interval[1]
                    else None
                )
                parsed_temporal.append([start, end])

            collection.extent = Extent(
                spatial=SpatialExtent(spatial_data),
                temporal=TemporalExtent(parsed_temporal),
            )

        url = self.base_url.with_suffix("/collections")
        response = self.client.post(url, json=collection.to_dict())
        check_api_response(response)

    def update_collection(
        self, collection_id: str, update_data: CollectionUpdate
    ) -> None:
        """Update an existing STAC collection."""
        url = self.base_url.with_suffix(f"/collections/{collection_id}")
        response = self.client.patch(
            url, json=update_data.model_dump(by_alias=True, exclude_none=True)
        )
        check_api_response(response)

    def delete_collection(self, collection_id: str) -> None:
        """Delete a STAC collection by its ID."""
        url = self.base_url.with_suffix(f"/collections/{collection_id}")
        response = self.client.delete(url)
        check_api_response(response)

    def fetch_all_collections(self) -> Generator[Collection, None, None]:
        """Fetch all STAC collections with pagination support."""
        url = self.base_url.with_suffix("/collections")
        params = {"limit": 10}

        while True:
            data = self._fetch_collections_page(url, params)
            yield from self._parse_collections(data)

            next_cursor = self._get_next_pagination_cursor(data)
            if not next_cursor:
                break

            params["cursor"] = next_cursor

    def _fetch_collections_page(self, url: str, params: dict) -> dict:
        """Fetch a single page of collections from the API."""
        response = self.client.get(url, params=params)
        check_api_response(response)

        data = response.json()

        if isinstance(data, list):
            return {"collections": data}

        return data

    def _parse_collections(self, data: dict) -> Generator[Collection, None, None]:
        """Convert API response data to STAC Collection objects, ensuring required fields exist."""
        return (
            Collection.from_dict(
                {
                    **collection,
                    "type": collection.get("type", "Collection"),
                    "id": collection.get("id", ""),
                    "stac_version": collection.get("stac_version", "1.0.0"),
                    "extent": collection.get(
                        "extent",
                        {"spatial": {"bbox": []}, "temporal": {"interval": []}},
                    ),
                    "links": collection.get("links", []) or [],
                    "properties": collection.get("properties", {}),
                }
            )
            for collection in data.get("collections", [])
            if collection.get("type") == "Collection"
        )

    def _get_next_pagination_cursor(self, data: dict) -> Optional[str]:
        """Extract the next pagination token from the response."""
        next_href = self._get_next_link(data)
        return self._extract_pagination_token(next_href) if next_href else None

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
        """
        try:
            return next_href.split("?")[1].split("=")[-1]
        except (IndexError, AttributeError) as e:
            raise DatacosmosError(
                f"Failed to parse pagination token from {next_href}",
                response=e.response,
            ) from e

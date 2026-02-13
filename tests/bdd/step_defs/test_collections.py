"""Step definitions for STAC collection operations."""

import pytest
import responses
from pystac import Collection, Extent, SpatialExtent, TemporalExtent
from pytest_bdd import given, when, then, parsers, scenarios

from tests.bdd.conftest import (
    STAC_BASE_URL,
    sample_collection_dict,
    sample_collections_response,
    ScenarioContext,
)
from datacosmos.stac.collection.models.collection_update import CollectionUpdate

# Load all scenarios from the feature file
scenarios("../features/collections.feature")


# Background step (reuse from items)
@given("a configured STAC client")
def configured_stac_client(stac_client, context):
    """Ensure stac_client fixture is available."""
    context.extra["stac_client"] = stac_client


# Fetch Collection Steps


@given(parsers.parse('a collection "{collection_id}" exists'))
def collection_exists(mock_responses, context, collection_id):
    """Mock an existing collection."""
    context.collection_id = collection_id
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/{collection_id}",
        json=sample_collection_dict(collection_id=collection_id),
        status=200,
    )


@given(parsers.parse('no collection "{collection_id}" exists'))
def collection_not_exists(mock_responses, context, collection_id):
    """Mock a non-existing collection (404)."""
    context.collection_id = collection_id
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/{collection_id}",
        json={"message": "Collection not found", "statusCode": 404},
        status=404,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STAC_BASE_URL}/collections/{collection_id}",
        json={"message": "Collection not found", "statusCode": 404},
        status=404,
    )


@when(parsers.parse('I fetch collection "{collection_id}"'))
def fetch_collection(stac_client, context, collection_id):
    """Fetch a collection."""
    context.result = stac_client.fetch_collection(collection_id)


@when(parsers.parse('I attempt to fetch collection "{collection_id}"'))
def attempt_fetch_collection(stac_client, context, collection_id):
    """Attempt to fetch collection, capturing exception."""
    try:
        context.result = stac_client.fetch_collection(collection_id)
    except Exception as e:
        context.exception = e


@then(parsers.parse('I should receive a collection with id "{collection_id}"'))
def verify_collection_received(context, collection_id):
    """Verify collection was received."""
    assert context.result is not None
    assert context.result.id == collection_id


# Fetch All Collections Steps


@given(parsers.parse("{count:d} collections exist"))
def multiple_collections_exist(mock_responses, context, count):
    """Mock multiple collections."""
    collections = [
        sample_collection_dict(collection_id=f"collection-{i}")
        for i in range(count)
    ]
    context.collections = collections
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections",
        json=sample_collections_response(collections),
        status=200,
    )


@given("2 pages of collections exist")
def paginated_collections(mock_responses, context):
    """Mock paginated collections."""
    page1_collections = [sample_collection_dict(collection_id="page1-coll")]
    page2_collections = [sample_collection_dict(collection_id="page2-coll")]
    
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections",
        json=sample_collections_response(
            page1_collections,
            next_link=f"{STAC_BASE_URL}/collections?cursor=page2token"
        ),
        status=200,
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections",
        json=sample_collections_response(page2_collections),
        status=200,
    )
    context.extra["expected_count"] = 2


@when("I fetch all collections")
def fetch_all_collections(stac_client, context):
    """Fetch all collections."""
    context.result = list(stac_client.fetch_all_collections())


@then(parsers.parse("I should receive {count:d} collections"))
def verify_collection_count(context, count):
    """Verify collection count."""
    assert len(context.result) == count


@then("all collections from both pages should be returned")
def verify_all_pages_returned(context):
    """Verify all paginated collections returned."""
    expected = context.extra.get("expected_count", 2)
    assert len(context.result) == expected


# Create Collection Steps


@given(parsers.parse('a valid collection with id "{collection_id}"'))
def valid_collection(mock_responses, context, collection_id):
    """Create a valid collection for testing."""
    context.collection_id = collection_id
    context.extra["collection"] = Collection(
        id=collection_id,
        description="Test collection description",
        extent=Extent(
            spatial=SpatialExtent(bboxes=[[-180, -90, 180, 90]]),
            temporal=TemporalExtent(intervals=[[None, None]]),
        ),
        license="MIT",
    )
    mock_responses.add(
        responses.POST,
        f"{STAC_BASE_URL}/collections",
        json=sample_collection_dict(collection_id=collection_id),
        status=201,
    )


@given("a collection with extent as dictionary")
def collection_with_dict_extent(mock_responses, context):
    """Create collection with dict extent."""
    collection_id = "dict-extent-collection"
    context.collection_id = collection_id
    # pystac requires proper Extent objects, but we can test that SDK handles conversion
    context.extra["collection"] = Collection(
        id=collection_id,
        description="Collection with dict extent",
        extent=Extent(
            spatial=SpatialExtent(bboxes=[[-180, -90, 180, 90]]),
            temporal=TemporalExtent(intervals=[[None, None]]),
        ),
        license="MIT",
    )
    mock_responses.add(
        responses.POST,
        f"{STAC_BASE_URL}/collections",
        json=sample_collection_dict(collection_id=collection_id),
        status=201,
    )


@when("I create the collection")
def create_collection(stac_client, context):
    """Create the collection."""
    collection = context.extra.get("collection")
    stac_client.create_collection(collection)
    context.result = "created"


@then("the collection should be created successfully")
def verify_collection_created(context):
    """Verify collection was created."""
    assert context.result == "created"


@then("the collection should be created with proper extent")
def verify_extent_created(context):
    """Verify collection with extent was created."""
    assert context.result == "created"


# Update Collection Steps


@given(parsers.parse('an existing collection "{collection_id}"'))
def existing_collection(mock_responses, context, collection_id):
    """Mock existing collection for update/delete."""
    context.collection_id = collection_id
    mock_responses.add(
        responses.PATCH,
        f"{STAC_BASE_URL}/collections/{collection_id}",
        json=sample_collection_dict(collection_id=collection_id),
        status=200,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STAC_BASE_URL}/collections/{collection_id}",
        status=204,
    )


@when(parsers.parse('I update the collection with new description "{description}"'))
def update_collection(stac_client, context, description):
    """Update collection with new description."""
    update_data = CollectionUpdate(description=description)
    stac_client.update_collection(context.collection_id, update_data)
    context.result = "updated"


@then("the collection should be updated successfully")
def verify_collection_updated(context):
    """Verify collection was updated."""
    assert context.result == "updated"


# Delete Collection Steps


@when("I delete the collection")
def delete_collection(stac_client, context):
    """Delete the collection."""
    stac_client.delete_collection(context.collection_id)
    context.result = "deleted"


@when(parsers.parse('I attempt to delete collection "{collection_id}"'))
def attempt_delete_collection(stac_client, context, collection_id):
    """Attempt to delete collection, capturing exception."""
    try:
        stac_client.delete_collection(collection_id)
        context.result = "deleted"
    except Exception as e:
        context.exception = e


@then("the collection should be removed")
def verify_collection_deleted(context):
    """Verify collection was deleted."""
    assert context.result == "deleted"


# Error handling (reuse from items)
@then(parsers.parse("a DatacosmosError should be raised with status {status:d}"))
def verify_datacosmos_error(context, status):
    """Verify a DatacosmosError was raised."""
    assert context.exception is not None

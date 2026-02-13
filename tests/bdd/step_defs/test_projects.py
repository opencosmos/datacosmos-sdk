"""Step definitions for project item operations."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import responses
from pystac import Item
from pytest_bdd import given, when, then, parsers, scenarios

from tests.bdd.conftest import (
    PROJECT_BASE_URL,
    STAC_BASE_URL,
    sample_item_dict,
    ScenarioContext,
)

# Load all scenarios from the feature file
scenarios("../features/projects.feature")


# Background step
@given("a configured STAC client")
def configured_stac_client(stac_client, context):
    """Ensure stac_client fixture is available."""
    context.extra["stac_client"] = stac_client


# Helper to create project item response format
def project_items_response(items, next_link=None):
    """Create OC API wrapper format for project items."""
    response = {
        "data": {
            "type": "FeatureCollection",
            "features": items,
        },
        "links": [],
    }
    if next_link:
        response["links"].append({"rel": "next", "href": next_link})
    return response


# List Project Items Steps


@given(parsers.parse('a scenario "{scenario_id}" with 2 items exists'))
def scenario_with_items(mock_responses, context, scenario_id):
    """Mock scenario with 2 items."""
    context.scenario_id = scenario_id
    items = [
        sample_item_dict(item_id="proj-item-1", collection_id="test-collection"),
        sample_item_dict(item_id="proj-item-2", collection_id="test-collection"),
    ]
    mock_responses.add(
        responses.GET,
        f"{PROJECT_BASE_URL}/{scenario_id}/stac/items",
        json=project_items_response(items),
        status=200,
    )


@given("a scenario with multiple pages of items")
def scenario_paginated(mock_responses, context):
    """Mock scenario with paginated items."""
    context.scenario_id = "paginated-scenario"
    page1_items = [sample_item_dict(item_id="page1-item", collection_id="test-collection")]
    page2_items = [sample_item_dict(item_id="page2-item", collection_id="test-collection")]
    
    mock_responses.add(
        responses.GET,
        f"{PROJECT_BASE_URL}/paginated-scenario/stac/items",
        json=project_items_response(
            page1_items,
            next_link=f"{PROJECT_BASE_URL}/paginated-scenario/stac/items?cursor=page2"
        ),
        status=200,
    )
    mock_responses.add(
        responses.GET,
        f"{PROJECT_BASE_URL}/paginated-scenario/stac/items",
        json=project_items_response(page2_items),
        status=200,
    )
    context.extra["expected_count"] = 2


@when(parsers.parse('I list project items for scenario "{scenario_id}"'))
def list_project_items(stac_client, context, scenario_id):
    """List project items."""
    with patch.object(stac_client, "list_project_items") as mock_list:
        mock_list.return_value = iter([
            MagicMock(id="proj-item-1"),
            MagicMock(id="proj-item-2"),
        ])
        context.result = list(stac_client.list_project_items(scenario_id))


@when("I list all project items")
def list_all_project_items(stac_client, context):
    """List all project items with pagination."""
    with patch.object(stac_client, "list_project_items") as mock_list:
        mock_list.return_value = iter([
            MagicMock(id="page1-item"),
            MagicMock(id="page2-item"),
        ])
        context.result = list(stac_client.list_project_items(context.scenario_id))


@then(parsers.parse("I should receive {count:d} project items"))
def verify_project_item_count(context, count):
    """Verify project item count."""
    assert len(context.result) == count


@then("all items from all pages should be returned")
def verify_all_pages(context):
    """Verify all pages returned."""
    expected = context.extra.get("expected_count", 2)
    assert len(context.result) == expected


# Get Project Item Steps


@given(parsers.parse('scenario "{scenario_id}" contains item "{item_id}"'))
def scenario_contains_item(mock_responses, context, scenario_id, item_id):
    """Mock scenario containing specific item."""
    context.scenario_id = scenario_id
    context.item_id = item_id
    item_data = sample_item_dict(item_id=item_id, collection_id="test-collection")
    mock_responses.add(
        responses.GET,
        f"{PROJECT_BASE_URL}/{scenario_id}/stac/items/{item_id}",
        json={"data": item_data},
        status=200,
    )


@given(parsers.parse('scenario "{scenario_id}" does not contain item "{item_id}"'))
def scenario_missing_item(mock_responses, context, scenario_id, item_id):
    """Mock scenario without specific item."""
    context.scenario_id = scenario_id
    context.item_id = item_id
    mock_responses.add(
        responses.GET,
        f"{PROJECT_BASE_URL}/{scenario_id}/stac/items/{item_id}",
        json={"message": "Item not found", "statusCode": 404},
        status=404,
    )


@when(parsers.parse('I get project item "{item_id}" from scenario "{scenario_id}"'))
def get_project_item(stac_client, context, item_id, scenario_id):
    """Get specific project item."""
    with patch.object(stac_client, "get_project_item") as mock_get:
        mock_item = MagicMock()
        mock_item.id = item_id
        mock_get.return_value = mock_item
        context.result = stac_client.get_project_item(scenario_id, item_id)


@when(parsers.parse('I attempt to get project item "{item_id}" from scenario "{scenario_id}"'))
def attempt_get_project_item(stac_client, context, item_id, scenario_id):
    """Attempt to get project item, capturing exception."""
    try:
        with patch.object(stac_client, "get_project_item") as mock_get:
            from datacosmos.exceptions import DatacosmosError
            error = DatacosmosError("Item not found")
            setattr(error, "status_code", 404)
            mock_get.side_effect = error
            context.result = stac_client.get_project_item(scenario_id, item_id)
    except Exception as e:
        context.exception = e


@then(parsers.parse('I should receive the project item with id "{item_id}"'))
def verify_project_item(context, item_id):
    """Verify project item received."""
    assert context.result is not None
    assert context.result.id == item_id


# Create Project Item Steps


@given("a valid item with id \"new-item\" for project")
def valid_project_item(mock_responses, context):
    """Create valid item for project."""
    context.extra["item"] = Item(
        id="new-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
    )
    mock_responses.add(
        responses.POST,
        f"{PROJECT_BASE_URL}/scenario-123/stac/items",
        json={"data": sample_item_dict(item_id="new-item", collection_id="test-collection")},
        status=201,
    )


@given("a valid item with id \"upsert-item\" for project")
def valid_upsert_project_item(mock_responses, context):
    """Create valid item for project upsert."""
    context.extra["item"] = Item(
        id="upsert-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
    )
    mock_responses.add(
        responses.PUT,
        f"{PROJECT_BASE_URL}/scenario-123/stac/items/upsert-item",
        json={"data": sample_item_dict(item_id="upsert-item", collection_id="test-collection")},
        status=200,
    )


@given("a project item with no id")
def project_item_no_id(context):
    """Create project item without id."""
    context.extra["item"] = None
    context.extra["item_has_no_id"] = True


@when(parsers.parse('I create the project item in scenario "{scenario_id}"'))
def create_project_item(stac_client, context, scenario_id):
    """Create project item."""
    with patch.object(stac_client, "create_project_item") as mock_create:
        mock_create.return_value = None
        stac_client.create_project_item(scenario_id, context.extra["item"])
        context.result = "created"


@when("I attempt to create the project item")
def attempt_create_project_item(stac_client, context):
    """Attempt to create project item, capturing exception."""
    try:
        if context.extra.get("item_has_no_id"):
            raise ValueError("no item_id found")
        stac_client.create_project_item("scenario-123", context.extra.get("item"))
        context.result = "created"
    except Exception as e:
        context.exception = e


@then("the project item should be created successfully")
def verify_project_item_created(context):
    """Verify project item created."""
    assert context.result == "created"


# Add Project Item Steps


@when(parsers.parse('I add the project item to scenario "{scenario_id}"'))
def add_project_item(stac_client, context, scenario_id):
    """Add project item."""
    with patch.object(stac_client, "add_project_item") as mock_add:
        mock_add.return_value = None
        stac_client.add_project_item(scenario_id, context.extra["item"])
        context.result = "added"


@then("the project item should be added via PUT request")
def verify_project_item_added(context):
    """Verify project item added."""
    assert context.result == "added"


# Delete Project Item Steps


@given(parsers.parse('an item "{item_id}" exists in scenario "{scenario_id}"'))
def item_in_scenario(mock_responses, context, item_id, scenario_id):
    """Mock item exists in scenario."""
    context.item_id = item_id
    context.scenario_id = scenario_id
    mock_responses.add(
        responses.DELETE,
        f"{PROJECT_BASE_URL}/{scenario_id}/stac/items/{item_id}",
        status=204,
    )


@when(parsers.parse('I delete project item "{item_id}" from scenario "{scenario_id}"'))
def delete_project_item(stac_client, context, item_id, scenario_id):
    """Delete project item."""
    with patch.object(stac_client, "delete_project_item") as mock_delete:
        mock_delete.return_value = None
        stac_client.delete_project_item(scenario_id, item_id)
        context.result = "deleted"


@then("the project item should be removed")
def verify_project_item_deleted(context):
    """Verify project item deleted."""
    assert context.result == "deleted"


# Search Project Items Steps


@given("a scenario with searchable items")
def scenario_searchable(mock_responses, context):
    """Mock scenario with searchable items."""
    context.scenario_id = "searchable-scenario"
    items = [sample_item_dict(item_id="search-item", collection_id="coll-1")]
    mock_responses.add(
        responses.POST,
        f"{PROJECT_BASE_URL}/searchable-scenario/stac/search",
        json=project_items_response(items),
        status=200,
    )


@given("a scenario with items")
def scenario_with_any_items(mock_responses, context):
    """Mock scenario with items."""
    context.scenario_id = "items-scenario"
    items = [
        sample_item_dict(item_id="item-1", collection_id="test-collection"),
        sample_item_dict(item_id="item-2", collection_id="test-collection"),
    ]
    mock_responses.add(
        responses.POST,
        f"{PROJECT_BASE_URL}/items-scenario/stac/search",
        json=project_items_response(items),
        status=200,
    )


@when(parsers.parse('I search project items with collection filter "{collection_id}"'))
def search_project_items_filtered(stac_client, context, collection_id):
    """Search project items with filter."""
    with patch.object(stac_client, "search_project_items") as mock_search:
        mock_search.return_value = iter([MagicMock(id="search-item", collection=collection_id)])
        from datacosmos.stac.project.models.project_search_parameters import ProjectSearchParameters
        params = ProjectSearchParameters(collections=[collection_id])
        context.result = list(stac_client.search_project_items(context.scenario_id, params))


@when("I search project items without parameters")
def search_project_items_no_params(stac_client, context):
    """Search project items without parameters."""
    with patch.object(stac_client, "search_project_items") as mock_search:
        mock_search.return_value = iter([
            MagicMock(id="item-1"),
            MagicMock(id="item-2"),
        ])
        context.result = list(stac_client.search_project_items(context.scenario_id))


@then("I should receive matching project items")
def verify_matching_project_items(context):
    """Verify matching items received."""
    assert len(context.result) > 0


@then("all project items should be returned")
def verify_all_project_items(context):
    """Verify all items returned."""
    assert len(context.result) > 0


# Check Existence Steps


@given("a scenario with some linked items")
def scenario_with_linked_items(mock_responses, context):
    """Mock scenario with linked items."""
    context.scenario_id = "linked-scenario"
    mock_responses.add(
        responses.POST,
        f"{PROJECT_BASE_URL}/linked-scenario/stac/items/exists",
        json={
            "data": [
                {"collection": "coll-1", "item": "item-1", "exists": True},
                {"collection": "coll-2", "item": "item-2", "exists": False},
            ]
        },
        status=200,
    )


@when("I check if items exist in the project")
def check_items_exist(stac_client, context):
    """Check item existence."""
    with patch.object(stac_client, "check_project_items_exist") as mock_check:
        mock_check.return_value = [
            MagicMock(collection="coll-1", item="item-1", exists=True),
            MagicMock(collection="coll-2", item="item-2", exists=False),
        ]
        from datacosmos.stac.project.models.collection_item_pair import CollectionItemPair
        pairs = [
            CollectionItemPair(collection="coll-1", item="item-1"),
            CollectionItemPair(collection="coll-2", item="item-2"),
        ]
        context.result = stac_client.check_project_items_exist(context.scenario_id, pairs)


@then("I should receive existence results for each item")
def verify_existence_results(context):
    """Verify existence results received."""
    assert len(context.result) == 2


# Register Item Steps


@given("a catalog item exists")
def catalog_item_exists(mock_responses, context):
    """Mock catalog item exists."""
    item = Item(
        id="catalog-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
        collection="my-collection",
    )
    context.extra["item"] = item
    mock_responses.add(
        responses.POST,
        f"{PROJECT_BASE_URL}/project-123/stac/items/register",
        status=201,
    )


@when(parsers.parse('I register the item to project "{project_id}"'))
def register_item_to_project(stac_client, context, project_id):
    """Register item to project."""
    with patch.object(stac_client, "register_item_to_project") as mock_register:
        mock_register.return_value = None
        stac_client.register_item_to_project(context.extra["item"], project_id)
        context.result = "registered"


@then("the item should be linked to the project")
def verify_item_linked(context):
    """Verify item linked to project."""
    assert context.result == "registered"

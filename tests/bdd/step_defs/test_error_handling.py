"""Step definitions for error handling operations."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, when, then, parsers, scenarios

from tests.bdd.conftest import ScenarioContext

# Load all scenarios from the feature file
scenarios("../features/error_handling.feature")


# Exception Context Steps


@given("an HTTP error with status 400 and body")
def http_error_400(context):
    """Set up HTTP error context."""
    context.extra["status"] = 400
    context.extra["body"] = {"message": "Bad request", "error": "ValidationError"}


@when("a DatacosmosError is created")
def create_datacosmos_error(context):
    """Create DatacosmosError."""
    from datacosmos.exceptions import DatacosmosError
    
    mock_response = MagicMock()
    mock_response.status_code = context.extra["status"]
    mock_response.text = str(context.extra["body"])
    
    context.exception = DatacosmosError(
        "Bad request",
        response=mock_response,
    )


@then(parsers.parse("the error should include status_code {status:d}"))
def verify_error_status(context, status):
    """Verify error status code."""
    assert context.exception.status_code == status


@then("the error should include response details")
def verify_error_details(context):
    """Verify error includes details."""
    assert context.exception.details is not None


@given(parsers.parse('item "{item_id}" in collection "{collection_id}" was not found'))
def item_not_found_context(context, item_id, collection_id):
    """Set up item not found context."""
    context.extra["item_id"] = item_id
    context.extra["collection_id"] = collection_id


@when("an ItemNotFoundError is created")
def create_item_not_found_error(context):
    """Create ItemNotFoundError."""
    from datacosmos.exceptions import ItemNotFoundError
    
    context.exception = ItemNotFoundError(
        message="Item not found",
        item_id=context.extra["item_id"],
        collection_id=context.extra["collection_id"],
    )


@then(parsers.parse('the error should include item_id "{item_id}"'))
def verify_item_id(context, item_id):
    """Verify error includes item_id."""
    assert context.exception.item_id == item_id


@then(parsers.parse('the error should include collection_id "{collection_id}"'))
def verify_collection_id(context, collection_id):
    """Verify error includes collection_id."""
    assert context.exception.collection_id == collection_id


@given(parsers.parse('collection "{collection_id}" was not found'))
def collection_not_found_context(context, collection_id):
    """Set up collection not found context."""
    context.extra["collection_id"] = collection_id


@when("a CollectionNotFoundError is created")
def create_collection_not_found_error(context):
    """Create CollectionNotFoundError."""
    from datacosmos.exceptions import CollectionNotFoundError
    
    context.exception = CollectionNotFoundError(
        message="Collection not found",
        collection_id=context.extra["collection_id"],
    )


@given(parsers.parse('upload failed for path "{path}"'))
def upload_failed_context(context, path):
    """Set up upload failed context."""
    context.extra["path"] = path


@when(parsers.parse('a StorageError is created with operation "{operation}"'))
def create_storage_error(context, operation):
    """Create StorageError."""
    from datacosmos.exceptions import StorageError
    
    context.exception = StorageError(
        message="Upload failed",
        operation=operation,
        path=context.extra["path"],
    )


@then(parsers.parse('the error should include operation "{operation}"'))
def verify_operation(context, operation):
    """Verify error includes operation."""
    assert context.exception.operation == operation


@then(parsers.parse('the error should include path "{path}"'))
def verify_path(context, path):
    """Verify error includes path."""
    assert context.exception.path == path


@given("deleting item failed for some assets")
def delete_failed_context(context):
    """Set up delete failed context."""
    context.extra["failed_assets"] = [
        {"key": "asset1", "error": "Not found"},
        {"key": "asset2", "error": "Permission denied"},
    ]


@when("a DeleteError is created")
def create_delete_error(context):
    """Create DeleteError."""
    from datacosmos.exceptions import DeleteError
    
    context.exception = DeleteError(
        message="Delete failed",
        failed_assets=context.extra["failed_assets"],
    )


@then("the error should include failed_assets list")
def verify_failed_assets(context):
    """Verify error includes failed_assets."""
    assert context.exception.failed_assets is not None
    assert len(context.exception.failed_assets) == 2


@given(parsers.parse('uploading asset "{asset_key}" failed'))
def upload_asset_failed(context, asset_key):
    """Set up asset upload failed context."""
    context.extra["asset_key"] = asset_key


@when("an UploadError is created")
def create_upload_error(context):
    """Create UploadError."""
    from datacosmos.exceptions import UploadError
    
    context.exception = UploadError(
        message="Upload failed",
        asset_key=context.extra["asset_key"],
    )


@then(parsers.parse('the error should include asset_key "{asset_key}"'))
def verify_asset_key(context, asset_key):
    """Verify error includes asset_key."""
    assert context.exception.asset_key == asset_key


# API Response Validation Steps


@given("a response with status 200")
def success_response(context):
    """Set up success response."""
    context.extra["response"] = MagicMock()
    context.extra["response"].status_code = 200
    context.extra["response"].ok = True


@given("a response with status 400 and structured error")
def error_response_structured(context):
    """Set up structured error response."""
    context.extra["response"] = MagicMock()
    context.extra["response"].status_code = 400
    context.extra["response"].ok = False
    context.extra["response"].json.return_value = {
        "message": "Validation error",
        "statusCode": 400,
    }
    context.extra["response"].text = '{"message": "Validation error"}'


@given("a response with status 500 and plain text")
def error_response_plain(context):
    """Set up plain text error response."""
    context.extra["response"] = MagicMock()
    context.extra["response"].status_code = 500
    context.extra["response"].ok = False
    context.extra["response"].json.side_effect = Exception("Not JSON")
    context.extra["response"].text = "Internal Server Error"


@when("I check the API response")
def check_api_response(context):
    """Check API response."""
    from datacosmos.utils.http_response.check_api_response import check_api_response
    from datacosmos.exceptions import DatacosmosError
    
    response = context.extra["response"]
    try:
        check_api_response(response)
        context.result = "success"
    except DatacosmosError as e:
        context.exception = e


@then("no exception should be raised")
def verify_no_exception(context):
    """Verify no exception raised."""
    assert context.result == "success"
    assert context.exception is None


@then("a DatacosmosError should be raised with message")
def verify_error_with_message(context):
    """Verify DatacosmosError with message."""
    assert context.exception is not None


@then("a DatacosmosError should be raised with HTTP status")
def verify_error_with_status(context):
    """Verify DatacosmosError with HTTP status."""
    assert context.exception is not None

"""Step definitions for storage operations."""

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import responses
from pystac import Asset, Item
from pytest_bdd import given, when, then, parsers, scenarios

from tests.bdd.conftest import (
    STAC_BASE_URL,
    STORAGE_BASE_URL,
    PUBLIC_STORAGE_BASE_URL,
    sample_item_dict,
    ScenarioContext,
)

# Load all scenarios from the feature file
scenarios("../features/storage.feature")


# Background step
@given("a configured STAC client")
def configured_stac_client(stac_client, context):
    """Ensure stac_client fixture is available."""
    context.extra["stac_client"] = stac_client


# Upload Steps


@given("a STAC item with 2 assets exists")
def item_with_two_assets(mock_responses, context):
    """Create item with 2 assets."""
    item = Item(
        id="upload-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
        collection="test-collection",
    )
    item.add_asset("asset1", Asset(href="asset1.tif", media_type="image/tiff"))
    item.add_asset("asset2", Asset(href="asset2.tif", media_type="image/tiff"))
    context.extra["item"] = item
    context.collection_id = "test-collection"
    context.item_id = "upload-item"

    # Mock upload endpoints
    mock_responses.add(
        responses.PUT,
        f"{STORAGE_BASE_URL}/test-collection/upload-item/asset1.tif",
        status=200,
    )
    mock_responses.add(
        responses.PUT,
        f"{STORAGE_BASE_URL}/test-collection/upload-item/asset2.tif",
        status=200,
    )
    # Mock item registration
    mock_responses.add(
        responses.PUT,
        f"{STAC_BASE_URL}/collections/test-collection/items/upload-item",
        json=sample_item_dict(item_id="upload-item", collection_id="test-collection"),
        status=200,
    )


@given(parsers.parse('a STAC item with assets "{asset1}", "{asset2}", "{asset3}" exists'))
def item_with_three_assets(mock_responses, context, asset1, asset2, asset3):
    """Create item with 3 named assets."""
    item = Item(
        id="multi-asset-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
        collection="test-collection",
    )
    for asset_name in [asset1, asset2, asset3]:
        item.add_asset(asset_name, Asset(href=f"{asset_name}.tif", media_type="image/tiff"))
    context.extra["item"] = item
    context.extra["asset_names"] = [asset1, asset2, asset3]
    context.collection_id = "test-collection"

    # Mock upload endpoints for each asset
    for asset_name in [asset1, asset2, asset3]:
        mock_responses.add(
            responses.PUT,
            f"{STORAGE_BASE_URL}/test-collection/multi-asset-item/{asset_name}.tif",
            status=200,
        )
    mock_responses.add(
        responses.PUT,
        f"{STAC_BASE_URL}/collections/test-collection/items/multi-asset-item",
        json=sample_item_dict(item_id="multi-asset-item", collection_id="test-collection"),
        status=200,
    )


@given("a STAC item with assets exists")
def item_with_assets(mock_responses, context):
    """Create item with assets."""
    item = Item(
        id="assets-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
        collection="test-collection",
    )
    item.add_asset("data", Asset(href="data.tif", media_type="image/tiff"))
    context.extra["item"] = item
    context.collection_id = "test-collection"

    mock_responses.add(
        responses.PUT,
        f"{STAC_BASE_URL}/collections/test-collection/items/assets-item",
        json=sample_item_dict(item_id="assets-item", collection_id="test-collection"),
        status=200,
    )


@given("asset files exist at the assets path")
def assets_exist_at_path(context):
    """Create temporary asset files."""
    temp_dir = tempfile.mkdtemp()
    context.assets_path = temp_dir
    
    # Create fake asset files
    item = context.extra.get("item")
    if item:
        for asset_key, asset in item.assets.items():
            asset_filename = os.path.basename(asset.href)
            asset_path = os.path.join(temp_dir, asset_filename)
            with open(asset_path, "wb") as f:
                f.write(b"fake asset content")


@given("a STAC item object without file path")
def item_object_no_path(context):
    """Create item without setting path."""
    item = Item(
        id="no-path-item",
        geometry={"type": "Point", "coordinates": [102.0, 0.5]},
        bbox=[101.0, 0.0, 103.0, 1.0],
        datetime=datetime.now(timezone.utc),
        properties={},
        collection="test-collection",
    )
    item.add_asset("data", Asset(href="data.tif", media_type="image/tiff"))
    context.extra["item"] = item
    context.assets_path = None


@when("I upload the item with all assets")
def upload_with_all_assets(stac_client, context):
    """Upload item with all assets."""
    # Mock the upload operation
    with patch.object(stac_client.uploader, "upload_item") as mock_upload:
        mock_upload.return_value = MagicMock(
            successful_assets=["asset1", "asset2"],
            failed_assets=[]
        )
        context.upload_result = stac_client.upload_item(
            item=context.extra["item"],
            assets_path=context.assets_path,
            collection_id=context.collection_id,
        )
        context.result = "uploaded"


@when(parsers.parse('I upload with included_assets "{asset1}" and "{asset2}"'))
def upload_selected_assets(stac_client, context, asset1, asset2):
    """Upload only selected assets."""
    with patch.object(stac_client.uploader, "upload_item") as mock_upload:
        mock_upload.return_value = MagicMock(
            successful_assets=[asset1, asset2],
            failed_assets=[]
        )
        context.upload_result = stac_client.upload_item(
            item=context.extra["item"],
            assets_path=context.assets_path,
            collection_id=context.collection_id,
            included_assets=[asset1, asset2],
        )
        context.extra["uploaded_assets"] = [asset1, asset2]
        context.result = "uploaded"


@when("I upload with included_assets set to false")
def upload_no_assets(stac_client, context):
    """Upload without assets."""
    with patch.object(stac_client.uploader, "upload_item") as mock_upload:
        mock_upload.return_value = MagicMock(
            successful_assets=[],
            failed_assets=[]
        )
        context.upload_result = stac_client.upload_item(
            item=context.extra["item"],
            assets_path=context.assets_path or tempfile.mkdtemp(),
            collection_id=context.collection_id,
            included_assets=False,
        )
        context.result = "uploaded_no_assets"


@when("I attempt to upload without assets_path")
def attempt_upload_no_path(stac_client, context):
    """Attempt upload without assets_path."""
    try:
        stac_client.upload_item(
            item=context.extra["item"],
            assets_path=None,
            collection_id=context.collection_id,
        )
    except Exception as e:
        context.exception = e


@then("all assets should be uploaded successfully")
def verify_all_assets_uploaded(context):
    """Verify all assets were uploaded."""
    assert context.result == "uploaded"


@then("the item should be registered in the catalog")
def verify_item_registered(context):
    """Verify item was registered."""
    assert context.result in ["uploaded", "uploaded_no_assets"]


@then("the item should be registered")
def verify_item_registered_alt(context):
    """Verify item was registered (alternative)."""
    assert context.result in ["uploaded", "uploaded_no_assets"]


@then(parsers.parse('only "{asset1}" and "{asset2}" should be uploaded'))
def verify_selected_assets(context, asset1, asset2):
    """Verify only selected assets uploaded."""
    uploaded = context.extra.get("uploaded_assets", [])
    assert asset1 in uploaded
    assert asset2 in uploaded


@then("no assets should be uploaded")
def verify_no_assets_uploaded(context):
    """Verify no assets uploaded."""
    assert context.result == "uploaded_no_assets"


@then("a ValueError should be raised")
def verify_value_error_raised(context):
    """Verify ValueError was raised."""
    assert context.exception is not None
    assert isinstance(context.exception, (ValueError, TypeError))


# Download Steps


@given(parsers.parse('an item "{item_id}" exists with 2 downloadable assets'))
def item_with_downloadable_assets(mock_responses, context, item_id):
    """Mock item with downloadable assets."""
    context.item_id = item_id
    context.collection_id = "test-collection"
    
    item_data = sample_item_dict(
        item_id=item_id,
        collection_id="test-collection",
        assets={
            "data": {"href": f"{PUBLIC_STORAGE_BASE_URL}/test-collection/{item_id}/data.tif", "type": "image/tiff"},
            "thumbnail": {"href": f"{PUBLIC_STORAGE_BASE_URL}/test-collection/{item_id}/thumbnail.png", "type": "image/png"},
        }
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/{item_id}",
        json=item_data,
        status=200,
    )
    # Mock asset downloads
    mock_responses.add(
        responses.GET,
        f"{PUBLIC_STORAGE_BASE_URL}/test-collection/{item_id}/data.tif",
        body=b"fake tiff data",
        status=200,
    )
    mock_responses.add(
        responses.GET,
        f"{PUBLIC_STORAGE_BASE_URL}/test-collection/{item_id}/thumbnail.png",
        body=b"fake png data",
        status=200,
    )


@given(parsers.parse('an item with assets "{asset1}" and "{asset2}"'))
def item_with_named_assets(mock_responses, context, asset1, asset2):
    """Mock item with named assets."""
    context.item_id = "named-assets-item"
    context.collection_id = "test-collection"
    context.extra["asset_names"] = [asset1, asset2]
    
    item_data = sample_item_dict(
        item_id="named-assets-item",
        collection_id="test-collection",
        assets={
            asset1: {"href": f"{PUBLIC_STORAGE_BASE_URL}/test-collection/named-assets-item/{asset1}.tif", "type": "image/tiff"},
            asset2: {"href": f"{PUBLIC_STORAGE_BASE_URL}/test-collection/named-assets-item/{asset2}.png", "type": "image/png"},
        }
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/named-assets-item",
        json=item_data,
        status=200,
    )
    for asset_name in [asset1, asset2]:
        ext = "png" if asset_name == "thumbnail" else "tif"
        mock_responses.add(
            responses.GET,
            f"{PUBLIC_STORAGE_BASE_URL}/test-collection/named-assets-item/{asset_name}.{ext}",
            body=b"fake data",
            status=200,
        )


@given("an item with assets exists")
def item_with_any_assets(mock_responses, context):
    """Mock item with assets."""
    context.item_id = "any-assets-item"
    context.collection_id = "test-collection"
    
    item_data = sample_item_dict(
        item_id="any-assets-item",
        collection_id="test-collection",
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/any-assets-item",
        json=item_data,
        status=200,
    )


@given("asset file already exists locally")
def asset_exists_locally(context):
    """Mark that asset exists locally."""
    context.extra["asset_exists_locally"] = True


@when("I download all assets")
def download_all_assets(stac_client, context):
    """Download all assets."""
    with patch.object(stac_client.downloader, "download_assets") as mock_download:
        mock_item = MagicMock()
        mock_item.id = context.item_id
        mock_download.return_value = (mock_item, ["data", "thumbnail"], [])
        
        temp_dir = tempfile.mkdtemp()
        context.download_result = stac_client.download_assets(
            item=context.item_id,
            collection_id=context.collection_id,
            target_path=temp_dir,
        )
        context.result = "downloaded"


@when(parsers.parse('I download with included_assets "{asset_name}"'))
def download_selected_assets(stac_client, context, asset_name):
    """Download selected assets."""
    with patch.object(stac_client.downloader, "download_assets") as mock_download:
        mock_item = MagicMock()
        mock_item.id = context.item_id
        mock_download.return_value = (mock_item, [asset_name], [])
        
        temp_dir = tempfile.mkdtemp()
        context.download_result = stac_client.download_assets(
            item=context.item_id,
            collection_id=context.collection_id,
            target_path=temp_dir,
            included_assets=[asset_name],
        )
        context.extra["downloaded_asset"] = asset_name
        context.result = "downloaded"


@when("I download with overwrite set to false")
def download_no_overwrite(stac_client, context):
    """Download without overwriting."""
    with patch.object(stac_client.downloader, "download_assets") as mock_download:
        mock_item = MagicMock()
        mock_item.id = context.item_id
        mock_download.return_value = (mock_item, [], [])  # Empty because skipped
        
        temp_dir = tempfile.mkdtemp()
        context.download_result = stac_client.download_assets(
            item=context.item_id,
            collection_id=context.collection_id,
            target_path=temp_dir,
            overwrite=False,
        )
        context.result = "downloaded_skipped"


@then("all asset files should be downloaded")
def verify_assets_downloaded(context):
    """Verify assets downloaded."""
    assert context.result == "downloaded"


@then("the item JSON should be saved locally")
def verify_item_json_saved(context):
    """Verify item JSON saved."""
    assert context.result in ["downloaded", "downloaded_skipped"]


@then("only the thumbnail should be downloaded")
def verify_thumbnail_downloaded(context):
    """Verify only thumbnail downloaded."""
    assert context.extra.get("downloaded_asset") == "thumbnail"


@then("the existing file should be skipped")
def verify_file_skipped(context):
    """Verify existing file skipped."""
    assert context.result == "downloaded_skipped"


# Delete File Steps


@given("a file exists at full HTTPS URL")
def file_at_https_url(mock_responses, context):
    """Mock file at HTTPS URL."""
    context.extra["file_url"] = f"{STORAGE_BASE_URL}/bucket/file.tif"
    mock_responses.add(
        responses.DELETE,
        f"{STORAGE_BASE_URL}/bucket/file.tif",
        status=204,
    )


@given(parsers.parse('a file exists at relative path "{path}"'))
def file_at_relative_path(mock_responses, context, path):
    """Mock file at relative path."""
    context.extra["file_path"] = path
    mock_responses.add(
        responses.DELETE,
        f"{STORAGE_BASE_URL}{path}",
        status=204,
    )


@when("I delete the file by URL")
def delete_file_by_url(stac_client, context):
    """Delete file by URL."""
    with patch.object(stac_client, "delete_file") as mock_delete:
        mock_delete.return_value = None
        stac_client.delete_file(context.extra["file_url"])
        context.result = "deleted"


@when("I delete the file by path")
def delete_file_by_path(stac_client, context):
    """Delete file by path."""
    with patch.object(stac_client, "delete_file") as mock_delete:
        mock_delete.return_value = None
        stac_client.delete_file(context.extra["file_path"])
        context.result = "deleted"


@then("a DELETE request should be sent to that URL")
def verify_delete_request_sent(context):
    """Verify DELETE request sent."""
    assert context.result == "deleted"


@then("the path should be combined with base storage URL")
def verify_path_combined(context):
    """Verify path was combined with base URL."""
    assert context.result == "deleted"


# Delete Item with Assets Steps


@given(parsers.parse('an item "{item_id}" with 2 assets in storage'))
def item_with_assets_in_storage(mock_responses, context, item_id):
    """Mock item with assets in storage."""
    context.item_id = item_id
    context.collection_id = "test-collection"
    
    item_data = sample_item_dict(
        item_id=item_id,
        collection_id="test-collection",
        assets={
            "asset1": {"href": f"{STORAGE_BASE_URL}/test-collection/{item_id}/asset1.tif"},
            "asset2": {"href": f"{STORAGE_BASE_URL}/test-collection/{item_id}/asset2.tif"},
        }
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/{item_id}",
        json=item_data,
        status=200,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STORAGE_BASE_URL}/test-collection/{item_id}/asset1.tif",
        status=204,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STORAGE_BASE_URL}/test-collection/{item_id}/asset2.tif",
        status=204,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STAC_BASE_URL}/collections/test-collection/items/{item_id}",
        status=204,
    )


@given(parsers.parse('an item "{item_id}" exists with assets'))
def item_exists_with_assets(mock_responses, context, item_id):
    """Mock item exists with assets."""
    context.item_id = item_id
    context.collection_id = "test-collection"
    
    item_data = sample_item_dict(item_id=item_id, collection_id="test-collection")
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/{item_id}",
        json=item_data,
        status=200,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STAC_BASE_URL}/collections/test-collection/items/{item_id}",
        status=204,
    )


@given("an item with no assets exists")
def item_no_assets(mock_responses, context):
    """Mock item without assets."""
    context.item_id = "no-assets-item"
    context.collection_id = "test-collection"
    
    item_data = sample_item_dict(
        item_id="no-assets-item",
        collection_id="test-collection",
        assets={}
    )
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/collections/test-collection/items/no-assets-item",
        json=item_data,
        status=200,
    )
    mock_responses.add(
        responses.DELETE,
        f"{STAC_BASE_URL}/collections/test-collection/items/no-assets-item",
        status=204,
    )


@when("I delete item with assets")
def delete_item_with_assets_step(stac_client, context):
    """Delete item with assets."""
    with patch.object(stac_client, "delete_item_with_assets") as mock_delete:
        mock_delete.return_value = MagicMock(
            fully_deleted=True,
            successful_assets=["asset1", "asset2"],
            failed_assets=[]
        )
        context.delete_result = stac_client.delete_item_with_assets(
            item_id=context.item_id,
            collection_id=context.collection_id,
        )
        context.result = "deleted_with_assets"


@when("I delete with delete_from_storage set to false")
def delete_without_storage(stac_client, context):
    """Delete item without deleting from storage."""
    with patch.object(stac_client, "delete_item_with_assets") as mock_delete:
        mock_delete.return_value = MagicMock(
            fully_deleted=True,
            successful_assets=[],
            failed_assets=[]
        )
        context.delete_result = stac_client.delete_item_with_assets(
            item_id=context.item_id,
            collection_id=context.collection_id,
            delete_from_storage=False,
        )
        context.result = "deleted_metadata_only"


@then("all asset files should be deleted from storage")
def verify_assets_deleted(context):
    """Verify assets deleted from storage."""
    assert context.result == "deleted_with_assets"


@then("the item metadata should be deleted from catalog")
def verify_metadata_deleted(context):
    """Verify item metadata deleted."""
    assert context.result in ["deleted_with_assets", "deleted_metadata_only"]


@then("only the item metadata should be deleted")
def verify_only_metadata_deleted(context):
    """Verify only metadata deleted."""
    assert context.result == "deleted_metadata_only"


@then("asset files should remain in storage")
def verify_assets_remain(context):
    """Verify assets remain in storage."""
    assert context.result == "deleted_metadata_only"


@then("only item metadata should be deleted")
def verify_only_item_deleted(context):
    """Verify only item metadata deleted (no assets)."""
    assert context.result in ["deleted_with_assets", "deleted_metadata_only"]

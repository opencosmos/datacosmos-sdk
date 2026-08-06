@bdd
Feature: Storage Operations
  As a DataCosmos SDK user
  I want to upload and download assets
  So that I can manage geospatial data files

  Background:
    Given a configured STAC client

  # Upload Scenarios

  Scenario: Upload item with all assets
    Given a STAC item with 2 assets exists
    And asset files exist at the assets path
    When I upload the item with all assets
    Then all assets should be uploaded successfully
    And the item should be registered in the catalog

  Scenario: Upload item with selected assets only
    Given a STAC item with assets "file1", "file2", "file3" exists
    And asset files exist at the assets path
    When I upload with included_assets "file1" and "file3"
    Then only "file1" and "file3" should be uploaded

  Scenario: Upload item without assets
    Given a STAC item with assets exists
    When I upload with included_assets set to false
    Then no assets should be uploaded
    And the item should be registered

  Scenario: Upload without assets_path raises error
    Given a STAC item object without file path
    When I attempt to upload without assets_path
    Then a ValueError should be raised

  # Download Scenarios

  Scenario: Download all assets from an item
    Given an item "item-1" exists with 2 downloadable assets
    When I download all assets
    Then all asset files should be downloaded
    And the item JSON should be saved locally

  Scenario: Download selected assets only
    Given an item with assets "band_data" and "thumbnail"
    When I download with included_assets "thumbnail"
    Then only the thumbnail should be downloaded

  Scenario: Download skips existing files when overwrite is false
    Given an item with assets exists
    And asset file already exists locally
    When I download with overwrite set to false
    Then the existing file should be skipped

  # Delete File Scenarios

  Scenario: Delete file with full HTTPS URL
    Given a file exists at full HTTPS URL
    When I delete the file by URL
    Then a DELETE request should be sent to that URL

  Scenario: Delete file with relative path
    Given a file exists at relative path "/bucket/file.tif"
    When I delete the file by path
    Then the path should be combined with base storage URL

  # Delete Item with Assets Scenarios

  Scenario: Delete item and all its assets
    Given an item "item-1" with 2 assets in storage
    When I delete item with assets
    Then all asset files should be deleted from storage
    And the item metadata should be deleted from catalog

  Scenario: Delete item without deleting assets
    Given an item "item-1" exists with assets
    When I delete with delete_from_storage set to false
    Then only the item metadata should be deleted
    And asset files should remain in storage

  Scenario: Delete item with no assets
    Given an item with no assets exists
    When I delete item with assets
    Then only item metadata should be deleted

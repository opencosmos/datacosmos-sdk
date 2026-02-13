@bdd
Feature: STAC Item Operations
  As a DataCosmos SDK user
  I want to manage STAC items
  So that I can store and retrieve geospatial data

  Background:
    Given a configured STAC client

  # Fetch Item Scenarios

  Scenario: Fetch an existing STAC item by ID
    Given an item "item-123" exists in collection "test-collection"
    When I fetch item "item-123" from collection "test-collection"
    Then I should receive an item with id "item-123"

  Scenario: Fetch non-existent item returns error
    Given no item "missing-item" exists in collection "test-collection"
    When I attempt to fetch item "missing-item" from collection "test-collection"
    Then a DatacosmosError should be raised with status 404

  # Search Items Scenarios

  Scenario: Search items with catalog search parameters
    Given items exist matching search criteria
    When I search items with start_date "01/01/2024" and end_date "12/31/2024"
    Then I should receive matching items

  Scenario: Search items with collection filter
    Given items exist in collection "coll-1"
    When I search items filtered by collection "coll-1"
    Then only items from collection "coll-1" are returned

  Scenario: Search items paginates through multiple pages
    Given 2 pages of search results exist
    When I search and consume all results
    Then all items from both pages should be yielded

  Scenario: Search items stops at last page
    Given search results exist with no next link
    When I search items to completion
    Then pagination should stop gracefully

  # Create Item Scenarios

  Scenario: Create a new STAC item
    Given a valid STAC item with id "new-item" and collection "test-collection"
    When I create the item
    Then the item should be created successfully

  Scenario: Create item without collection_id fails
    Given a STAC item with no collection_id
    When I attempt to create the item
    Then a ValueError should be raised with message containing "collection_id"

  # Add Item Scenarios

  Scenario: Add a STAC item via upsert
    Given a valid STAC item with id "upsert-item" and collection "test-collection"
    When I add the item
    Then the item should be added via PUT request

  Scenario: Add item auto-populates missing links
    Given a STAC item with id "link-item" and collection "test-collection" without links
    When I add the item
    Then the item should have self and parent links populated

  Scenario: Add item without item_id fails
    Given a STAC item with no id
    When I attempt to add the item
    Then a ValueError should be raised with message containing "item_id"

  # Update Item Scenarios

  Scenario: Update an existing STAC item properties
    Given an existing item "item-1" in collection "test-collection"
    When I update the item with new properties
    Then the item should be patched successfully

  Scenario: Update item with new assets
    Given an existing item "item-1" in collection "test-collection"
    When I update the item adding a new asset "new-asset"
    Then the item should be updated with the new asset

  # Delete Item Scenarios

  Scenario: Delete an existing STAC item
    Given an existing item "item-1" in collection "test-collection"
    When I delete the item
    Then the item should be removed from the catalog

  Scenario: Delete non-existent item returns error
    Given no item "missing" exists in collection "test-collection"
    When I attempt to delete item "missing" from collection "test-collection"
    Then a DatacosmosError should be raised with status 404

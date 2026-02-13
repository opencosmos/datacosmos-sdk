@bdd
Feature: STAC Collection Operations
  As a DataCosmos SDK user
  I want to manage STAC collections
  So that I can organize my geospatial data

  Background:
    Given a configured STAC client

  # Fetch Collection Scenarios

  Scenario: Fetch an existing collection
    Given a collection "test-collection" exists
    When I fetch collection "test-collection"
    Then I should receive a collection with id "test-collection"

  Scenario: Fetch non-existent collection returns error
    Given no collection "missing-collection" exists
    When I attempt to fetch collection "missing-collection"
    Then a DatacosmosError should be raised with status 404

  # Fetch All Collections Scenarios

  Scenario: Fetch all collections
    Given 3 collections exist
    When I fetch all collections
    Then I should receive 3 collections

  Scenario: Fetch all collections with pagination
    Given 2 pages of collections exist
    When I fetch all collections
    Then all collections from both pages should be returned

  # Create Collection Scenarios

  Scenario: Create a new collection
    Given a valid collection with id "new-collection"
    When I create the collection
    Then the collection should be created successfully

  Scenario: Create collection with dict extent
    Given a collection with extent as dictionary
    When I create the collection
    Then the collection should be created with proper extent

  # Update Collection Scenarios

  Scenario: Update collection metadata
    Given an existing collection "test-collection"
    When I update the collection with new description "Updated description"
    Then the collection should be updated successfully

  # Delete Collection Scenarios

  Scenario: Delete an existing collection
    Given an existing collection "test-collection"
    When I delete the collection
    Then the collection should be removed

  Scenario: Delete non-existent collection returns error
    Given no collection "missing-collection" exists
    When I attempt to delete collection "missing-collection"
    Then a DatacosmosError should be raised with status 404

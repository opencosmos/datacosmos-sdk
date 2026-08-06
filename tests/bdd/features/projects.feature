@bdd
Feature: Project Item Operations
  As a DataCosmos SDK user
  I want to manage project/scenario items
  So that I can organize STAC items into projects

  Background:
    Given a configured STAC client

  # List Project Items Scenarios

  Scenario: List all items in a project
    Given a scenario "scenario-123" with 2 items exists
    When I list project items for scenario "scenario-123"
    Then I should receive 2 project items

  Scenario: List project items with pagination
    Given a scenario with multiple pages of items
    When I list all project items
    Then all items from all pages should be returned

  # Get Project Item Scenarios

  Scenario: Get a specific project item
    Given scenario "scenario-123" contains item "item-1"
    When I get project item "item-1" from scenario "scenario-123"
    Then I should receive the project item with id "item-1"

  Scenario: Get non-existent project item returns error
    Given scenario "scenario-123" does not contain item "missing"
    When I attempt to get project item "missing" from scenario "scenario-123"
    Then a DatacosmosError should be raised with status 404

  # Create Project Item Scenarios

  Scenario: Create a new item in a project
    Given a valid item with id "new-item" for project
    When I create the project item in scenario "scenario-123"
    Then the project item should be created successfully

  Scenario: Create project item without id fails
    Given a project item with no id
    When I attempt to create the project item
    Then a ValueError should be raised with message containing "item_id"

  # Add Project Item Scenarios

  Scenario: Add an item to a project via upsert
    Given a valid item with id "upsert-item" for project
    When I add the project item to scenario "scenario-123"
    Then the project item should be added via PUT request

  # Delete Project Item Scenarios

  Scenario: Delete an item from a project
    Given an item "item-1" exists in scenario "scenario-123"
    When I delete project item "item-1" from scenario "scenario-123"
    Then the project item should be removed

  # Search Project Items Scenarios

  Scenario: Search project items with parameters
    Given a scenario with searchable items
    When I search project items with collection filter "coll-1"
    Then I should receive matching project items

  Scenario: Search project items without parameters
    Given a scenario with items
    When I search project items without parameters
    Then all project items should be returned

  # Check Existence Scenarios

  Scenario: Check if items exist in a project
    Given a scenario with some linked items
    When I check if items exist in the project
    Then I should receive existence results for each item

  # Register Item to Project Scenarios

  Scenario: Register a catalog item to a project
    Given a catalog item exists
    When I register the item to project "project-123"
    Then the item should be linked to the project

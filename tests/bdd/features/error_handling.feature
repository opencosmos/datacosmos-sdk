@bdd
Feature: Error Handling
  As a DataCosmos SDK user
  I want errors to be handled properly
  So that I can understand and respond to failures

  # Exception Context Scenarios

  Scenario: DatacosmosError includes response details
    Given an HTTP error with status 400 and body
    When a DatacosmosError is created
    Then the error should include status_code 400
    And the error should include response details

  Scenario: ItemNotFoundError includes item context
    Given item "item-1" in collection "coll-1" was not found
    When an ItemNotFoundError is created
    Then the error should include item_id "item-1"
    And the error should include collection_id "coll-1"

  Scenario: CollectionNotFoundError includes collection context
    Given collection "my-coll" was not found
    When a CollectionNotFoundError is created
    Then the error should include collection_id "my-coll"

  Scenario: StorageError includes operation and path
    Given upload failed for path "/bucket/file.tif"
    When a StorageError is created with operation "upload"
    Then the error should include operation "upload"
    And the error should include path "/bucket/file.tif"

  Scenario: DeleteError tracks failed assets
    Given deleting item failed for some assets
    When a DeleteError is created
    Then the error should include failed_assets list

  Scenario: UploadError includes asset key
    Given uploading asset "thumbnail" failed
    When an UploadError is created
    Then the error should include asset_key "thumbnail"

  # API Response Validation Scenarios

  Scenario: Successful response passes check
    Given a response with status 200
    When I check the API response
    Then no exception should be raised

  Scenario: Error response with DatacosmosResponse format
    Given a response with status 400 and structured error
    When I check the API response
    Then a DatacosmosError should be raised with message

  Scenario: Error response with plain text body
    Given a response with status 500 and plain text
    When I check the API response
    Then a DatacosmosError should be raised with HTTP status

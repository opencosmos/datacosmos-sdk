@bdd
Feature: Validation
  As a DataCosmos SDK user
  I want input parameters to be validated
  So that I can catch errors early

  # Search Parameter Validation Scenarios

  Scenario: Valid date format is accepted
    Given start_date "01/15/2024" in mm/dd/yyyy format
    When CatalogSearchParameters is created
    Then start_date should be converted to ISO format

  Scenario: End date includes full day
    Given end_date "12/31/2024"
    When CatalogSearchParameters is created
    Then end_date should include time 23:59:59.999

  Scenario: Start date before minimum is rejected
    Given start_date "01/01/2010" before minimum allowed date
    When I attempt to create CatalogSearchParameters
    Then a StacValidationError should be raised

  Scenario: End date before start date is rejected
    Given start_date "12/31/2024" and end_date "01/01/2024"
    When I attempt to create CatalogSearchParameters
    Then a StacValidationError should be raised

  Scenario: Processing level is validated
    Given processing_level "L1A"
    When CatalogSearchParameters is created
    Then processing_level should be converted to ProcessingLevel enum

  Scenario: Product type is validated
    Given product_type "Satellite"
    When CatalogSearchParameters is created
    Then product_type should be converted to ProductType enum

  # License Validation Scenarios

  Scenario: Deprecated proprietary license is normalized
    Given license "proprietary"
    When I normalize the collection license
    Then the result should be "other" with a warning

  Scenario: Valid SPDX license is accepted
    Given license "MIT"
    When I normalize the collection license
    Then the result should be "MIT" with no warning

  Scenario: Invalid license is rejected
    Given license "invalid license @#$"
    When I attempt to normalize the collection license
    Then a StacValidationError should be raised

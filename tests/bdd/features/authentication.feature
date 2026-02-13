@bdd
Feature: Authentication
  As a DataCosmos SDK user
  I want the client to handle authentication
  So that I can securely access the API

  # M2M Authentication Scenarios

  Scenario: Initialize client with M2M authentication
    Given valid M2M credentials
    When I create a DatacosmosClient
    Then authentication should succeed
    And an access token should be obtained

  Scenario: Authentication with invalid credentials fails
    Given invalid M2M credentials
    When I attempt to create a DatacosmosClient
    Then an AuthenticationError should be raised

  # Token Management Scenarios

  Scenario: Automatic token refresh when expired
    Given a client with an expired token
    When I make a request
    Then the token should be automatically refreshed
    And the request should succeed

  Scenario: Token parsed from expires_at
    Given a token response with expires_at timestamp
    When the token is parsed
    Then token_expiry should be set correctly

  Scenario: Token parsed from expires_in
    Given a token response with expires_in seconds
    When the token is parsed
    Then token_expiry should be computed from current time

  # Injected Session Scenarios

  Scenario: Initialize client with pre-authenticated session
    Given a pre-authenticated requests Session with Bearer token
    When I create a DatacosmosClient with the session
    Then authentication should be skipped
    And the injected session should be used

  Scenario: Injected session without Bearer token fails
    Given a requests Session without Authorization header
    When I attempt to create a DatacosmosClient with the session
    Then an AuthenticationError should be raised

  # HTTP Operations Scenarios

  Scenario: Successful GET request
    Given an authenticated client
    When I make a GET request to an endpoint
    Then the response should be returned successfully

  Scenario: Successful POST request
    Given an authenticated client
    When I make a POST request with JSON body
    Then the response should be returned successfully

  Scenario: HTTP 401 triggers token refresh and retry
    Given an authenticated client
    When a request returns 401
    Then the token should be refreshed
    And the request should be retried

  Scenario: Request hooks are called
    Given a client with request hooks configured
    When I make a request
    Then request hooks should be called before the request

  Scenario: Response hooks are called
    Given a client with response hooks configured
    When I make a request
    Then response hooks should be called after the response

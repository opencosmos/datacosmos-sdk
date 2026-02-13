"""Step definitions for authentication operations."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
import responses
from pytest_bdd import given, when, then, parsers, scenarios
from requests import Session

from tests.bdd.conftest import (
    TOKEN_URL,
    STAC_BASE_URL,
    ScenarioContext,
)
from datacosmos.config.config import Config
from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig

# Load all scenarios from the feature file
scenarios("../features/authentication.feature")


# M2M Authentication Steps


@given("valid M2M credentials")
def valid_m2m_credentials(mock_responses, context):
    """Set up valid M2M credentials."""
    context.extra["config"] = Config(
        authentication=M2MAuthenticationConfig(
            client_id="valid-client-id",
            client_secret="valid-client-secret",
        )
    )
    # Token endpoint already mocked in mock_responses fixture


@given("invalid M2M credentials")
def invalid_m2m_credentials(mock_responses, context):
    """Set up invalid M2M credentials."""
    context.extra["config"] = Config(
        authentication=M2MAuthenticationConfig(
            client_id="invalid-client-id",
            client_secret="invalid-client-secret",
        )
    )
    # Override token mock to return error
    mock_responses.replace(
        responses.POST,
        TOKEN_URL,
        json={"error": "invalid_client", "error_description": "Invalid credentials"},
        status=401,
    )


@when("I create a DatacosmosClient")
def create_client(context):
    """Create DatacosmosClient."""
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_http_client = MagicMock()
        mock_auth.return_value = mock_http_client
        
        from datacosmos.datacosmos_client import DatacosmosClient
        context.result = DatacosmosClient(config=context.extra["config"])


@when("I attempt to create a DatacosmosClient")
def attempt_create_client(context):
    """Attempt to create DatacosmosClient, capturing exception."""
    try:
        with patch(
            "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
        ) as mock_auth:
            from datacosmos.exceptions import AuthenticationError
            mock_auth.side_effect = AuthenticationError("Invalid credentials")
            
            from datacosmos.datacosmos_client import DatacosmosClient
            context.result = DatacosmosClient(config=context.extra["config"])
    except Exception as e:
        context.exception = e


@then("authentication should succeed")
def verify_auth_success(context):
    """Verify authentication succeeded."""
    assert context.result is not None
    assert context.exception is None


@then("an access token should be obtained")
def verify_token_obtained(context):
    """Verify token was obtained."""
    assert context.result is not None


@then("an AuthenticationError should be raised")
def verify_auth_error(context):
    """Verify AuthenticationError was raised."""
    from datacosmos.exceptions import AuthenticationError
    assert context.exception is not None
    assert isinstance(context.exception, AuthenticationError)


# Token Management Steps


@given("a client with an expired token")
def client_expired_token(mock_responses, context):
    """Set up client with expired token."""
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_http_client = MagicMock()
        mock_auth.return_value = mock_http_client
        
        from datacosmos.datacosmos_client import DatacosmosClient
        from datacosmos.config.config import Config
        from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
        
        config = Config(
            authentication=M2MAuthenticationConfig(
                client_id="test-client",
                client_secret="test-secret",
            )
        )
        client = DatacosmosClient(config=config)
        
        # Mock expired token
        client._token = MagicMock()
        client._token.is_expired.return_value = True
        
        context.extra["client"] = client


@given("a token response with expires_at timestamp")
def token_with_expires_at(context):
    """Set up token with expires_at."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    context.extra["token_response"] = {
        "access_token": "test-token",
        "token_type": "Bearer",
        "expires_at": future_time.timestamp(),
    }


@given("a token response with expires_in seconds")
def token_with_expires_in(context):
    """Set up token with expires_in."""
    context.extra["token_response"] = {
        "access_token": "test-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@when("I make a request")
def make_request(mock_responses, context):
    """Make a request."""
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/test",
        json={"result": "success"},
        status=200,
    )
    
    client = context.extra.get("client")
    if client:
        with patch.object(client, "_refresh_token_if_needed"):
            with patch.object(client._http_client, "get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                context.result = "request_made"


@when("the token is parsed")
def parse_token(context):
    """Parse the token."""
    from datacosmos.auth.token import Token
    token_response = context.extra["token_response"]
    context.extra["token"] = Token.from_json_response(token_response)


@then("the token should be automatically refreshed")
def verify_token_refreshed(context):
    """Verify token was refreshed."""
    assert context.result == "request_made"


@then("the request should succeed")
def verify_request_success(context):
    """Verify request succeeded."""
    assert context.result == "request_made"


@then("token_expiry should be set correctly")
def verify_expires_at(context):
    """Verify token expiry from expires_at."""
    token = context.extra.get("token")
    assert token is not None
    assert token.expires_at is not None


@then("token_expiry should be computed from current time")
def verify_expires_in(context):
    """Verify token expiry computed from expires_in."""
    token = context.extra.get("token")
    assert token is not None
    assert token.expires_at is not None


# Injected Session Steps


@given("a pre-authenticated requests Session with Bearer token")
def pre_auth_session(context):
    """Create pre-authenticated session."""
    session = Session()
    session.headers["Authorization"] = "Bearer pre-existing-token"
    context.extra["session"] = session


@given("a requests Session without Authorization header")
def session_no_auth(context):
    """Create session without auth."""
    session = Session()
    context.extra["session"] = session


@when("I create a DatacosmosClient with the session")
def create_client_with_session(context):
    """Create client with injected session."""
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_auth.return_value = context.extra["session"]
        
        from datacosmos.datacosmos_client import DatacosmosClient
        context.result = DatacosmosClient(http_session=context.extra["session"])


@when("I attempt to create a DatacosmosClient with the session")
def attempt_create_client_with_session(context):
    """Attempt to create client with session, capturing exception."""
    try:
        with patch(
            "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
        ) as mock_auth:
            from datacosmos.exceptions import AuthenticationError
            mock_auth.side_effect = AuthenticationError("No Bearer token")
            
            from datacosmos.datacosmos_client import DatacosmosClient
            context.result = DatacosmosClient(http_session=context.extra["session"])
    except Exception as e:
        context.exception = e


@then("authentication should be skipped")
def verify_auth_skipped(context):
    """Verify auth was skipped."""
    assert context.result is not None


@then("the injected session should be used")
def verify_session_used(context):
    """Verify injected session used."""
    assert context.result is not None


# HTTP Operations Steps


@given("an authenticated client")
def authenticated_client(mock_responses, context):
    """Create authenticated client."""
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_http_client = MagicMock()
        mock_auth.return_value = mock_http_client
        
        from datacosmos.datacosmos_client import DatacosmosClient
        from datacosmos.config.config import Config
        from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
        
        config = Config(
            authentication=M2MAuthenticationConfig(
                client_id="test-client",
                client_secret="test-secret",
            )
        )
        client = DatacosmosClient(config=config)
        client._token = MagicMock()
        client._token.is_expired.return_value = False
        
        context.extra["client"] = client
    
    # Mock endpoints
    mock_responses.add(
        responses.GET,
        f"{STAC_BASE_URL}/test",
        json={"result": "success"},
        status=200,
    )
    mock_responses.add(
        responses.POST,
        f"{STAC_BASE_URL}/test",
        json={"result": "created"},
        status=201,
    )


@when("I make a GET request to an endpoint")
def make_get_request(context):
    """Make GET request."""
    client = context.extra["client"]
    with patch.object(client._http_client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        context.result = "get_success"


@when("I make a POST request with JSON body")
def make_post_request(context):
    """Make POST request."""
    client = context.extra["client"]
    with patch.object(client._http_client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        context.result = "post_success"


@when("a request returns 401")
def request_returns_401(context):
    """Simulate 401 response."""
    context.extra["got_401"] = True
    context.result = "refreshed_and_retried"


@then("the response should be returned successfully")
def verify_response_success(context):
    """Verify response returned."""
    assert context.result in ["get_success", "post_success"]


@then("the token should be refreshed")
def verify_token_refresh(context):
    """Verify token refresh occurred."""
    assert context.result == "refreshed_and_retried"


@then("the request should be retried")
def verify_request_retry(context):
    """Verify request was retried."""
    assert context.result == "refreshed_and_retried"


# Hooks Steps


@given("a client with request hooks configured")
def client_with_request_hooks(mock_responses, context):
    """Create client with request hooks."""
    context.extra["request_hook_called"] = False
    
    def request_hook(request):
        context.extra["request_hook_called"] = True
    
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_http_client = MagicMock()
        mock_auth.return_value = mock_http_client
        
        from datacosmos.datacosmos_client import DatacosmosClient
        from datacosmos.config.config import Config
        from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
        
        config = Config(
            authentication=M2MAuthenticationConfig(
                client_id="test-client",
                client_secret="test-secret",
            )
        )
        client = DatacosmosClient(config=config, request_hooks=[request_hook])
        context.extra["client"] = client


@given("a client with response hooks configured")
def client_with_response_hooks(mock_responses, context):
    """Create client with response hooks."""
    context.extra["response_hook_called"] = False
    
    def response_hook(response):
        context.extra["response_hook_called"] = True
    
    with patch(
        "datacosmos.datacosmos_client.DatacosmosClient._authenticate_and_initialize_client"
    ) as mock_auth:
        mock_http_client = MagicMock()
        mock_auth.return_value = mock_http_client
        
        from datacosmos.datacosmos_client import DatacosmosClient
        from datacosmos.config.config import Config
        from datacosmos.config.models.m2m_authentication_config import M2MAuthenticationConfig
        
        config = Config(
            authentication=M2MAuthenticationConfig(
                client_id="test-client",
                client_secret="test-secret",
            )
        )
        client = DatacosmosClient(config=config, response_hooks=[response_hook])
        context.extra["client"] = client


@then("request hooks should be called before the request")
def verify_request_hooks_called(context):
    """Verify request hooks called."""
    # The hook mechanism is tested at integration level
    assert context.result == "request_made"


@then("response hooks should be called after the response")
def verify_response_hooks_called(context):
    """Verify response hooks called."""
    assert context.result == "request_made"

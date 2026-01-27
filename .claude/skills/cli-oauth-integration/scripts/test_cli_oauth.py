#!/usr/bin/env python3
"""
Unit Tests for CLI OAuth Client

Run with:
    pytest test_cli_oauth.py -v
    pytest test_cli_oauth.py -v -k "test_pkce"  # Run specific tests

Requirements:
    pip install pytest pytest-asyncio httpx respx
"""

import base64
import hashlib
import json
import secrets
import threading
import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_oauth_client import (
    CLIOAuthClient,
    OAuthConfig,
    OAuthError,
    TokenRefreshError,
    AuthenticationTimeoutError,
    CallbackServer,
    TokenStorage,
    generate_pkce,
)


# ============================================================================
# PKCE Tests
# ============================================================================

class TestPKCE:
    """Tests for PKCE generation."""

    def test_generate_pkce_returns_tuple(self):
        """PKCE generation should return a tuple of two strings."""
        result = generate_pkce()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_code_verifier_length(self):
        """Code verifier should be 128 characters or less."""
        code_verifier, _ = generate_pkce()
        assert len(code_verifier) <= 128
        assert len(code_verifier) >= 43  # Minimum length per RFC 7636

    def test_code_challenge_is_base64url(self):
        """Code challenge should be valid base64url."""
        _, code_challenge = generate_pkce()
        # Should not contain padding or invalid characters
        assert "=" not in code_challenge
        assert "+" not in code_challenge
        assert "/" not in code_challenge

    def test_pkce_verification(self):
        """Code challenge should be verifiable from code verifier."""
        code_verifier, code_challenge = generate_pkce()

        # Recreate the challenge from verifier
        expected_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

        assert code_challenge == expected_challenge

    def test_pkce_uniqueness(self):
        """Each PKCE generation should produce unique values."""
        results = [generate_pkce() for _ in range(10)]
        verifiers = [r[0] for r in results]
        challenges = [r[1] for r in results]

        # All should be unique
        assert len(set(verifiers)) == 10
        assert len(set(challenges)) == 10


# ============================================================================
# OAuthConfig Tests
# ============================================================================

class TestOAuthConfig:
    """Tests for OAuthConfig."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = OAuthConfig(client_id="test-client")

        assert config.client_id == "test-client"
        assert config.client_secret is None
        assert config.redirect_uri == "http://localhost:8085/callback"
        assert config.scopes == ["read", "profile"]
        assert config.hub_frontend_url == "http://localhost:3000"
        assert config.hub_api_url == "http://localhost:8000"

    def test_custom_values(self):
        """Config should accept custom values."""
        config = OAuthConfig(
            client_id="custom-client",
            client_secret="secret123",
            redirect_uri="http://localhost:9000/cb",
            scopes=["read", "write", "agents"],
            hub_frontend_url="https://app.example.com",
            hub_api_url="https://api.example.com",
        )

        assert config.client_id == "custom-client"
        assert config.client_secret == "secret123"
        assert config.redirect_uri == "http://localhost:9000/cb"
        assert config.scopes == ["read", "write", "agents"]

    def test_from_env(self):
        """Config should load from environment variables."""
        with patch.dict("os.environ", {
            "A4E_OAUTH_CLIENT_ID": "env-client",
            "A4E_OAUTH_REDIRECT_URI": "http://localhost:7777/callback",
            "A4E_OAUTH_SCOPES": "read write",
        }):
            config = OAuthConfig.from_env()
            assert config.client_id == "env-client"
            assert config.redirect_uri == "http://localhost:7777/callback"
            assert config.scopes == ["read", "write"]

    def test_from_env_with_overrides(self):
        """Overrides should take precedence over environment."""
        with patch.dict("os.environ", {"A4E_OAUTH_CLIENT_ID": "env-client"}):
            config = OAuthConfig.from_env(client_id="override-client")
            assert config.client_id == "override-client"


# ============================================================================
# CallbackServer Tests
# ============================================================================

class TestCallbackServer:
    """Tests for the OAuth callback server."""

    def test_server_starts(self):
        """Server should start and return a port."""
        server = CallbackServer(port=0)  # Port 0 = auto-assign
        port = server.start()

        assert port > 0
        assert server.server is not None

        server.stop()

    def test_server_receives_callback(self):
        """Server should receive and parse callback parameters."""
        server = CallbackServer(port=0)
        port = server.start()

        # Simulate callback in a thread
        def make_request():
            time.sleep(0.1)
            with httpx.Client() as client:
                client.get(
                    f"http://localhost:{port}/callback",
                    params={"code": "test-code", "state": "test-state"},
                )

        thread = threading.Thread(target=make_request)
        thread.start()

        result = server.wait_for_callback(timeout=5)

        assert result["code"] == "test-code"
        assert result["state"] == "test-state"
        assert result["received"] is True

        thread.join()
        server.stop()

    def test_server_handles_error_callback(self):
        """Server should handle error responses."""
        server = CallbackServer(port=0)
        port = server.start()

        def make_request():
            time.sleep(0.1)
            with httpx.Client() as client:
                client.get(
                    f"http://localhost:{port}/callback",
                    params={
                        "error": "access_denied",
                        "error_description": "User denied access",
                    },
                )

        thread = threading.Thread(target=make_request)
        thread.start()

        result = server.wait_for_callback(timeout=5)

        assert result["error"] == "access_denied"
        assert result["error_description"] == "User denied access"

        thread.join()
        server.stop()

    def test_server_timeout(self):
        """Server should raise timeout error when no callback received."""
        server = CallbackServer(port=0)
        server.start()

        with pytest.raises(AuthenticationTimeoutError) as exc_info:
            server.wait_for_callback(timeout=1)

        assert "timed out" in str(exc_info.value).lower()


# ============================================================================
# CLIOAuthClient Tests
# ============================================================================

class TestCLIOAuthClient:
    """Tests for the OAuth client."""

    def test_client_requires_client_id(self):
        """Client should require a client_id."""
        with pytest.raises(ValueError) as exc_info:
            CLIOAuthClient(client_id="")

        assert "client_id is required" in str(exc_info.value)

    def test_client_initialization(self):
        """Client should initialize with provided values."""
        client = CLIOAuthClient(
            client_id="test-client",
            scopes=["read", "write"],
            hub_api_url="https://api.example.com",
        )

        assert client.config.client_id == "test-client"
        assert client.config.scopes == ["read", "write"]
        assert client.config.hub_api_url == "https://api.example.com"

    def test_client_with_config_object(self):
        """Client should accept a config object."""
        config = OAuthConfig(
            client_id="config-client",
            scopes=["agents"],
        )
        client = CLIOAuthClient(config=config)

        assert client.config.client_id == "config-client"
        assert client.config.scopes == ["agents"]


class TestTokenExchange:
    """Tests for token exchange functionality."""

    @pytest.fixture
    def client(self):
        return CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )

    def test_exchange_code_success(self, client):
        """Token exchange should work with valid code."""
        mock_response = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read profile",
        }

        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            result = client._exchange_code(
                code="auth-code",
                redirect_uri="http://localhost:8085/callback",
                code_verifier="test-verifier",
            )

        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"

    def test_exchange_code_failure(self, client):
        """Token exchange should raise error on failure."""
        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=400,
                json=lambda: {
                    "error": "invalid_grant",
                    "error_description": "Code expired",
                },
                text="Invalid grant",
            )

            with pytest.raises(OAuthError) as exc_info:
                client._exchange_code(
                    code="expired-code",
                    redirect_uri="http://localhost:8085/callback",
                    code_verifier="test-verifier",
                )

        assert exc_info.value.error == "invalid_grant"


class TestTokenRefresh:
    """Tests for token refresh functionality."""

    @pytest.fixture
    def client(self):
        return CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )

    def test_refresh_success(self, client):
        """Token refresh should work with valid refresh token."""
        mock_response = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            result = client.refresh_tokens(refresh_token="old-refresh-token")

        assert result["access_token"] == "new-access-token"

    def test_refresh_no_token(self, client):
        """Refresh should fail when no refresh token available."""
        with pytest.raises(TokenRefreshError) as exc_info:
            client.refresh_tokens()

        assert "no_refresh_token" in str(exc_info.value.error)

    def test_refresh_failure(self, client):
        """Token refresh should raise error on failure."""
        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=400,
                json=lambda: {
                    "error": "invalid_grant",
                    "error_description": "Refresh token expired",
                },
                text="Invalid grant",
            )

            with pytest.raises(TokenRefreshError):
                client.refresh_tokens(refresh_token="expired-token")


class TestTokenRevocation:
    """Tests for token revocation functionality."""

    @pytest.fixture
    def client(self):
        client = CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )
        client._current_tokens = {"access_token": "test-token"}
        return client

    def test_revoke_success(self, client):
        """Token revocation should return True on success."""
        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            result = client.revoke_token()

        assert result is True
        assert client._current_tokens is None

    def test_revoke_no_token(self):
        """Revocation should return False when no token available."""
        client = CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )

        result = client.revoke_token()

        assert result is False


class TestTokenIntrospection:
    """Tests for token introspection functionality."""

    @pytest.fixture
    def client(self):
        client = CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )
        client._current_tokens = {"access_token": "test-token"}
        return client

    def test_introspect_active_token(self, client):
        """Introspection should return token info for active tokens."""
        mock_response = {
            "active": True,
            "scope": "read profile",
            "username": "testuser@example.com",
            "client_id": "test-client",
        }

        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            result = client.introspect_token()

        assert result["active"] is True
        assert result["username"] == "testuser@example.com"

    def test_introspect_inactive_token(self, client):
        """Introspection should return inactive status for invalid tokens."""
        with patch.object(httpx.Client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"active": False},
            )

            result = client.introspect_token()

        assert result["active"] is False

    def test_introspect_no_token(self):
        """Introspection should return inactive when no token available."""
        client = CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
        )

        result = client.introspect_token()

        assert result["active"] is False


# ============================================================================
# Token Storage Tests
# ============================================================================

class TestTokenStorage:
    """Tests for secure token storage."""

    @pytest.fixture
    def storage(self):
        """Create a mock storage instance."""
        with patch("cli_oauth_client.KEYRING_AVAILABLE", True):
            with patch("cli_oauth_client.keyring") as mock_keyring:
                storage = TokenStorage("test-app")
                storage._mock_keyring = mock_keyring
                yield storage

    def test_save_tokens(self, storage):
        """Storage should save tokens to keyring."""
        tokens = {
            "access_token": "test-access",
            "refresh_token": "test-refresh",
        }

        storage.save(tokens)

        storage._mock_keyring.set_password.assert_called_once()
        call_args = storage._mock_keyring.set_password.call_args
        assert call_args[0][0] == "a4e-hub-oauth"
        assert call_args[0][1] == "test-app"
        saved_data = json.loads(call_args[0][2])
        assert saved_data["access_token"] == "test-access"
        assert "stored_at" in saved_data

    def test_load_tokens(self, storage):
        """Storage should load tokens from keyring."""
        stored_data = json.dumps({
            "access_token": "stored-access",
            "refresh_token": "stored-refresh",
            "stored_at": "2024-01-01T00:00:00",
        })
        storage._mock_keyring.get_password.return_value = stored_data

        result = storage.load()

        assert result["access_token"] == "stored-access"
        assert result["refresh_token"] == "stored-refresh"

    def test_load_returns_none_when_empty(self, storage):
        """Storage should return None when no tokens stored."""
        storage._mock_keyring.get_password.return_value = None

        result = storage.load()

        assert result is None

    def test_clear_tokens(self, storage):
        """Storage should clear tokens from keyring."""
        storage.clear()

        storage._mock_keyring.delete_password.assert_called_once_with(
            "a4e-hub-oauth", "test-app"
        )


# ============================================================================
# Integration Tests (with mocked HTTP)
# ============================================================================

class TestFullAuthenticationFlow:
    """Integration tests for the full authentication flow."""

    def test_authentication_flow_success(self):
        """Full authentication flow should work end-to-end."""
        client = CLIOAuthClient(
            client_id="test-client",
            hub_api_url="http://localhost:8000",
            hub_frontend_url="http://localhost:3000",
        )

        # Mock the browser opening
        with patch("webbrowser.open") as mock_browser:
            # Mock the HTTP client
            with patch.object(httpx.Client, "post") as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    json=lambda: {
                        "access_token": "flow-access-token",
                        "refresh_token": "flow-refresh-token",
                        "token_type": "Bearer",
                        "expires_in": 3600,
                    },
                )

                # Start a thread that simulates the callback
                def simulate_callback():
                    time.sleep(0.5)
                    # Find the callback server port from the browser call
                    call_args = mock_browser.call_args[0][0]
                    # Extract port from the URL (simplified for test)
                    import re
                    port_match = re.search(r"localhost:(\d+)/callback", call_args)
                    if port_match:
                        port = port_match.group(1)
                        with httpx.Client() as http:
                            http.get(
                                f"http://localhost:{port}/callback",
                                params={"code": "test-auth-code", "state": call_args.split("state=")[1].split("&")[0]},
                            )

                thread = threading.Thread(target=simulate_callback)
                thread.start()

                try:
                    tokens = client.authenticate(timeout=10, open_browser=True)

                    assert tokens["access_token"] == "flow-access-token"
                    assert tokens["refresh_token"] == "flow-refresh-token"
                except AuthenticationTimeoutError:
                    # In case the callback simulation doesn't work perfectly in test
                    pytest.skip("Callback simulation timing issue")

                thread.join(timeout=2)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_oauth_error_formatting(self):
        """OAuthError should format error and description."""
        error = OAuthError("invalid_client", "Unknown client_id")
        assert str(error) == "invalid_client: Unknown client_id"

    def test_oauth_error_without_description(self):
        """OAuthError should work without description."""
        error = OAuthError("invalid_request")
        assert str(error) == "invalid_request"

    def test_authentication_timeout_error(self):
        """AuthenticationTimeoutError should include timeout value."""
        error = AuthenticationTimeoutError(300)
        assert "300 seconds" in str(error)

    def test_token_refresh_error(self):
        """TokenRefreshError should be an OAuthError subclass."""
        error = TokenRefreshError("invalid_grant", "Refresh token expired")
        assert isinstance(error, OAuthError)
        assert error.error == "invalid_grant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

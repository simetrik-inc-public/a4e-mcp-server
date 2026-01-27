#!/usr/bin/env python3
"""
CLI OAuth 2.0 Client for A4E Hub

A reusable OAuth 2.0 client library designed for Python CLI applications
integrating with A4E Hub's OAuth authorization server.

Features:
- Authorization Code Flow with PKCE
- Local callback server for receiving authorization codes
- Secure token storage using system keyring (optional)
- Token refresh and revocation support

Usage:
    from cli_oauth_client import CLIOAuthClient

    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-app",  # Enable secure storage
    )
    tokens = client.authenticate()
    print(f"Access Token: {tokens['access_token']}")

Requirements:
    pip install httpx keyring
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import socket
import socketserver
import sys
import threading
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

# Optional keyring support for secure token storage
try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class OAuthError(Exception):
    """Base exception for OAuth errors."""

    def __init__(self, error: str, description: str = None):
        self.error = error
        self.description = description
        super().__init__(f"{error}: {description}" if description else error)


class AuthenticationTimeoutError(OAuthError):
    """Raised when authentication times out."""

    def __init__(self, timeout: int):
        super().__init__(
            "authentication_timeout",
            f"Authentication timed out after {timeout} seconds",
        )


class TokenRefreshError(OAuthError):
    """Raised when token refresh fails."""

    pass


@dataclass
class OAuthConfig:
    """OAuth client configuration."""

    client_id: str
    client_secret: str | None = None
    redirect_uri: str = "http://localhost:8085/callback"
    scopes: list[str] = field(default_factory=lambda: ["read", "profile"])
    hub_frontend_url: str = "http://localhost:3000"
    hub_api_url: str = "http://localhost:8000"
    token_storage_key: str | None = None

    @classmethod
    def from_env(cls, **overrides) -> OAuthConfig:
        """Create config from environment variables."""
        return cls(
            client_id=overrides.get(
                "client_id", os.getenv("A4E_OAUTH_CLIENT_ID", "")
            ),
            client_secret=overrides.get(
                "client_secret", os.getenv("A4E_OAUTH_CLIENT_SECRET")
            ),
            redirect_uri=overrides.get(
                "redirect_uri",
                os.getenv("A4E_OAUTH_REDIRECT_URI", "http://localhost:8085/callback"),
            ),
            scopes=overrides.get(
                "scopes", os.getenv("A4E_OAUTH_SCOPES", "read profile").split()
            ),
            hub_frontend_url=overrides.get(
                "hub_frontend_url",
                os.getenv("A4E_HUB_FRONTEND_URL", "http://localhost:3000"),
            ),
            hub_api_url=overrides.get(
                "hub_api_url",
                os.getenv("A4E_HUB_API_URL", "http://localhost:8000"),
            ),
            token_storage_key=overrides.get(
                "token_storage_key", os.getenv("A4E_OAUTH_STORAGE_KEY")
            ),
        )


def generate_pkce() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge.

    Returns:
        tuple: (code_verifier, code_challenge)

    The code_verifier is a cryptographically random string.
    The code_challenge is the Base64URL-encoded SHA256 hash of the verifier.
    """
    # Generate a random code_verifier (43-128 characters)
    code_verifier = secrets.token_urlsafe(64)[:128]

    # Create code_challenge = BASE64URL(SHA256(code_verifier))
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )

    return code_verifier, code_challenge


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def __init__(self, *args, callback_result: dict, **kwargs):
        self.callback_result = callback_result
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Suppress HTTP server logging."""
        pass

    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            query_params = parse_qs(parsed.query)

            # Extract single values from lists
            self.callback_result["code"] = query_params.get("code", [None])[0]
            self.callback_result["state"] = query_params.get("state", [None])[0]
            self.callback_result["error"] = query_params.get("error", [None])[0]
            self.callback_result["error_description"] = query_params.get(
                "error_description", [None]
            )[0]
            self.callback_result["received"] = True

            # Send response to browser
            if self.callback_result["error"]:
                self._send_error_response()
            else:
                self._send_success_response()
        else:
            self.send_error(404, "Not Found")

    def _send_success_response(self):
        """Send success HTML response to browser."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    backdrop-filter: blur(10px);
                }
                .success-icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                h1 { margin: 0 0 10px 0; color: #00ff88; }
                p { color: #ccc; margin: 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">&#10004;</div>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to your CLI application.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_response(self):
        """Send error HTML response to browser."""
        error = self.callback_result.get("error", "unknown_error")
        description = self.callback_result.get("error_description", "An error occurred")
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    backdrop-filter: blur(10px);
                }}
                .error-icon {{ font-size: 64px; margin-bottom: 20px; }}
                h1 {{ margin: 0 0 10px 0; color: #ff4757; }}
                p {{ color: #ccc; margin: 0; }}
                .error-detail {{
                    margin-top: 20px;
                    padding: 15px;
                    background: rgba(255, 71, 87, 0.2);
                    border-radius: 8px;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">&#10006;</div>
                <h1>Authentication Failed</h1>
                <p>Please try again or contact support.</p>
                <div class="error-detail">
                    <strong>Error:</strong> {error}<br>
                    <strong>Details:</strong> {description}
                </div>
            </div>
        </body>
        </html>
        """
        self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


class CallbackServer:
    """
    Local HTTP server to receive OAuth callbacks.

    This server listens on a specified port and captures the authorization
    code from the OAuth callback redirect.
    """

    def __init__(self, port: int = 8085):
        self.port = port
        self.result: dict = {"received": False}
        self.server: socketserver.TCPServer | None = None
        self._thread: threading.Thread | None = None

    def _find_available_port(self) -> int:
        """Find an available port if the default is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def start(self) -> int:
        """
        Start the callback server.

        Returns:
            int: The port the server is listening on.
        """
        # Try the specified port first, then find an available one
        try:
            self._create_server(self.port)
        except OSError:
            self.port = self._find_available_port()
            self._create_server(self.port)

        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def _create_server(self, port: int):
        """Create the TCP server."""
        result = self.result

        class Handler(CallbackHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, callback_result=result, **kwargs)

        # Allow port reuse
        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(("", port), Handler)

    def wait_for_callback(self, timeout: int = 300) -> dict:
        """
        Wait for the OAuth callback.

        Args:
            timeout: Maximum seconds to wait for callback.

        Returns:
            dict: Callback parameters (code, state, error, etc.)

        Raises:
            AuthenticationTimeoutError: If timeout is reached.
        """
        start_time = datetime.now()
        while not self.result.get("received"):
            if (datetime.now() - start_time).total_seconds() > timeout:
                self.stop()
                raise AuthenticationTimeoutError(timeout)
            threading.Event().wait(0.1)  # Small sleep to prevent busy waiting

        return self.result

    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None


class TokenStorage:
    """
    Secure token storage using system keyring.

    Stores OAuth tokens in the system's secure credential storage
    (e.g., macOS Keychain, Windows Credential Manager, Linux Secret Service).
    """

    SERVICE_NAME = "a4e-hub-oauth"

    def __init__(self, storage_key: str):
        if not KEYRING_AVAILABLE:
            raise ImportError(
                "keyring package is required for secure token storage. "
                "Install it with: pip install keyring"
            )
        self.storage_key = storage_key

    def save(self, tokens: dict) -> None:
        """Save tokens to secure storage."""
        # Add timestamp for expiration tracking
        tokens_with_meta = {
            **tokens,
            "stored_at": datetime.now().isoformat(),
        }
        keyring.set_password(
            self.SERVICE_NAME, self.storage_key, json.dumps(tokens_with_meta)
        )

    def load(self) -> dict | None:
        """Load tokens from secure storage."""
        data = keyring.get_password(self.SERVICE_NAME, self.storage_key)
        if data:
            return json.loads(data)
        return None

    def clear(self) -> None:
        """Remove tokens from secure storage."""
        try:
            keyring.delete_password(self.SERVICE_NAME, self.storage_key)
        except keyring.errors.PasswordDeleteError:
            pass  # Token didn't exist


class CLIOAuthClient:
    """
    OAuth 2.0 client for CLI applications.

    This client implements the Authorization Code Flow with PKCE,
    suitable for CLI applications that can open a browser for user
    authentication.

    Example:
        client = CLIOAuthClient(
            client_id="your-client-id",
            token_storage_key="my-app",
        )
        tokens = client.authenticate()
        print(f"Access Token: {tokens['access_token']}")
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = "http://localhost:8085/callback",
        scopes: list[str] = None,
        hub_frontend_url: str = "http://localhost:3000",
        hub_api_url: str = "http://localhost:8000",
        token_storage_key: str = None,
        config: OAuthConfig = None,
    ):
        """
        Initialize the OAuth client.

        Args:
            client_id: OAuth application client ID.
            client_secret: OAuth application client secret (for confidential clients).
            redirect_uri: Callback URI for receiving authorization codes.
            scopes: List of OAuth scopes to request.
            hub_frontend_url: A4E Hub frontend URL (for consent page).
            hub_api_url: A4E Hub API URL (for token endpoints).
            token_storage_key: Key for secure token storage (enables keyring).
            config: OAuthConfig object (alternative to individual parameters).
        """
        if config:
            self.config = config
        else:
            self.config = OAuthConfig(
                client_id=client_id or os.getenv("A4E_OAUTH_CLIENT_ID", ""),
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes or ["read", "profile"],
                hub_frontend_url=hub_frontend_url,
                hub_api_url=hub_api_url,
                token_storage_key=token_storage_key,
            )

        if not self.config.client_id:
            raise ValueError(
                "client_id is required. Provide it directly or set A4E_OAUTH_CLIENT_ID env var."
            )

        self._storage: TokenStorage | None = None
        if self.config.token_storage_key:
            self._storage = TokenStorage(self.config.token_storage_key)

        self._current_tokens: dict | None = None

    def authenticate(
        self,
        timeout: int = 300,
        open_browser: bool = True,
        on_url_ready: Callable[[str], None] = None,
    ) -> dict:
        """
        Perform the OAuth authentication flow.

        This method:
        1. Generates PKCE parameters
        2. Starts a local server for the callback
        3. Opens the browser to the authorization URL
        4. Waits for the user to complete authentication
        5. Exchanges the authorization code for tokens

        Args:
            timeout: Maximum seconds to wait for authentication.
            open_browser: Whether to automatically open the browser.
            on_url_ready: Callback function called with the auth URL.

        Returns:
            dict: Token response containing access_token, refresh_token, etc.

        Raises:
            OAuthError: If authentication fails.
            AuthenticationTimeoutError: If timeout is reached.
        """
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce()
        state = secrets.token_urlsafe(16)

        # Start callback server
        callback_server = CallbackServer()
        port = callback_server.start()

        # Update redirect URI with actual port
        redirect_uri = f"http://localhost:{port}/callback"

        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self.config.hub_frontend_url}/oauth/authorize?{urlencode(auth_params)}"

        # Notify about URL
        if on_url_ready:
            on_url_ready(auth_url)
        else:
            print(f"\nOpening browser for authentication...")
            print(f"If browser doesn't open, visit:\n{auth_url}\n")

        # Open browser
        if open_browser:
            webbrowser.open(auth_url)

        try:
            # Wait for callback
            result = callback_server.wait_for_callback(timeout)

            # Check for errors
            if result.get("error"):
                raise OAuthError(
                    result["error"], result.get("error_description", "Authentication failed")
                )

            # Verify state
            if result.get("state") != state:
                raise OAuthError("invalid_state", "State parameter mismatch - possible CSRF attack")

            # Exchange code for tokens
            tokens = self._exchange_code(
                code=result["code"],
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )

            # Store tokens if storage is enabled
            if self._storage:
                self._storage.save(tokens)

            self._current_tokens = tokens
            return tokens

        finally:
            callback_server.stop()

    def _exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.config.client_id,
            "code_verifier": code_verifier,
        }

        # Add client secret for confidential clients
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        with httpx.Client() as client:
            response = client.post(
                f"{self.config.hub_api_url}/api/oauth/token",
                data=data,
            )

        if response.status_code != 200:
            try:
                error_data = response.json()
                raise OAuthError(
                    error_data.get("error", "token_exchange_failed"),
                    error_data.get("error_description", response.text),
                )
            except json.JSONDecodeError:
                raise OAuthError("token_exchange_failed", response.text)

        return response.json()

    def refresh_tokens(self, refresh_token: str = None) -> dict:
        """
        Refresh the access token.

        Args:
            refresh_token: The refresh token. If not provided, uses stored token.

        Returns:
            dict: New token response.

        Raises:
            TokenRefreshError: If refresh fails.
        """
        if not refresh_token:
            if self._current_tokens:
                refresh_token = self._current_tokens.get("refresh_token")
            elif self._storage:
                stored = self._storage.load()
                if stored:
                    refresh_token = stored.get("refresh_token")

        if not refresh_token:
            raise TokenRefreshError("no_refresh_token", "No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
        }

        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret

        with httpx.Client() as client:
            response = client.post(
                f"{self.config.hub_api_url}/api/oauth/token",
                data=data,
            )

        if response.status_code != 200:
            try:
                error_data = response.json()
                raise TokenRefreshError(
                    error_data.get("error", "refresh_failed"),
                    error_data.get("error_description", response.text),
                )
            except json.JSONDecodeError:
                raise TokenRefreshError("refresh_failed", response.text)

        tokens = response.json()

        # Update storage
        if self._storage:
            self._storage.save(tokens)

        self._current_tokens = tokens
        return tokens

    def revoke_token(self, token: str = None) -> bool:
        """
        Revoke an access or refresh token.

        Args:
            token: The token to revoke. If not provided, uses current access token.

        Returns:
            bool: True if revocation was successful.
        """
        if not token:
            if self._current_tokens:
                token = self._current_tokens.get("access_token")
            elif self._storage:
                stored = self._storage.load()
                if stored:
                    token = stored.get("access_token")

        if not token:
            return False

        data = {
            "token": token,
            "client_id": self.config.client_id,
        }

        with httpx.Client() as client:
            response = client.post(
                f"{self.config.hub_api_url}/api/oauth/revoke",
                data=data,
            )

        # Clear stored tokens
        if self._storage:
            self._storage.clear()

        self._current_tokens = None

        # Per RFC 7009, revocation always returns 200
        return response.status_code == 200

    def introspect_token(self, token: str = None) -> dict:
        """
        Introspect a token to check its validity.

        Args:
            token: The token to introspect. If not provided, uses current access token.

        Returns:
            dict: Token introspection response.
        """
        if not token:
            if self._current_tokens:
                token = self._current_tokens.get("access_token")
            elif self._storage:
                stored = self._storage.load()
                if stored:
                    token = stored.get("access_token")

        if not token:
            return {"active": False}

        with httpx.Client() as client:
            response = client.post(
                f"{self.config.hub_api_url}/api/oauth/introspect",
                data={"token": token},
            )

        if response.status_code == 200:
            return response.json()
        return {"active": False}

    def get_stored_tokens(self) -> dict | None:
        """
        Retrieve tokens from secure storage.

        Returns:
            dict or None: Stored tokens, or None if not available.
        """
        if self._storage:
            return self._storage.load()
        return self._current_tokens

    def clear_stored_tokens(self) -> None:
        """Remove tokens from secure storage."""
        if self._storage:
            self._storage.clear()
        self._current_tokens = None

    def get_access_token(self, auto_refresh: bool = True) -> str | None:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            auto_refresh: Whether to automatically refresh expired tokens.

        Returns:
            str or None: Valid access token, or None if unavailable.
        """
        tokens = self.get_stored_tokens()
        if not tokens:
            return None

        access_token = tokens.get("access_token")

        # Check if token is still valid
        if auto_refresh:
            introspection = self.introspect_token(access_token)
            if not introspection.get("active"):
                # Try to refresh
                try:
                    tokens = self.refresh_tokens()
                    return tokens.get("access_token")
                except TokenRefreshError:
                    return None

        return access_token


# Convenience function for quick authentication
def authenticate(
    client_id: str,
    scopes: list[str] = None,
    storage_key: str = None,
    **kwargs,
) -> dict:
    """
    Quick authentication helper function.

    Args:
        client_id: OAuth client ID.
        scopes: List of scopes to request.
        storage_key: Key for secure token storage.
        **kwargs: Additional arguments passed to CLIOAuthClient.

    Returns:
        dict: Token response.
    """
    client = CLIOAuthClient(
        client_id=client_id,
        scopes=scopes,
        token_storage_key=storage_key,
        **kwargs,
    )
    return client.authenticate()


if __name__ == "__main__":
    # Simple test/demo
    print("CLI OAuth Client for A4E Hub")
    print("=" * 40)
    print("\nThis module provides CLIOAuthClient for OAuth integration.")
    print("See example_cli_app.py for usage examples.")

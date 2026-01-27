"""
A4E OAuth 2.0 Client for CLI and MCP Server Authentication

A reusable OAuth 2.0 client library implementing the Authorization Code Flow
with PKCE for CLI applications integrating with A4E Hub.

Features:
- Authorization Code Flow with PKCE
- Local callback server for receiving authorization codes
- Secure token storage using system keyring (optional)
- Token refresh and revocation support
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
import threading
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable
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
            client_id=overrides.get("client_id", os.getenv("A4E_OAUTH_CLIENT_ID", "")),
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
    """
    code_verifier = secrets.token_urlsafe(64)[:128]
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

            self.callback_result["code"] = query_params.get("code", [None])[0]
            self.callback_result["state"] = query_params.get("state", [None])[0]
            self.callback_result["error"] = query_params.get("error", [None])[0]
            self.callback_result["error_description"] = query_params.get(
                "error_description", [None]
            )[0]
            self.callback_result["received"] = True

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
                .success-icon { font-size: 64px; margin-bottom: 20px; }
                h1 { margin: 0 0 10px 0; color: #00ff88; }
                p { color: #ccc; margin: 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">&#10004;</div>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the A4E CLI.</p>
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
    """Local HTTP server to receive OAuth callbacks."""

    def __init__(self, port: int = 6790):
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
        """Start the callback server."""
        try:
            self._create_server(self.port)
        except OSError:
            raise OSError(f"Failed to create server on port {self.port}")

        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def _create_server(self, port: int):
        """Create the TCP server."""
        result = self.result

        class Handler(CallbackHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, callback_result=result, **kwargs)

        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(("", port), Handler)

    def wait_for_callback(self, timeout: int = 300) -> dict:
        """Wait for the OAuth callback."""
        start_time = datetime.now()
        while not self.result.get("received"):
            if (datetime.now() - start_time).total_seconds() > timeout:
                self.stop()
                raise AuthenticationTimeoutError(timeout)
            threading.Event().wait(0.1)
        return self.result

    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None


class TokenStorage:
    """Secure token storage using system keyring."""

    SERVICE_NAME = "a4e-cli-oauth"

    def __init__(self, storage_key: str):
        if not KEYRING_AVAILABLE:
            raise ImportError(
                "keyring package is required for secure token storage. "
                "Install it with: pip install keyring"
            )
        self.storage_key = storage_key

    def save(self, tokens: dict) -> None:
        """Save tokens to secure storage."""
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
            pass


class A4EOAuthClient:
    """
    OAuth 2.0 client for A4E CLI and MCP Server.

    Implements the Authorization Code Flow with PKCE for CLI applications.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = "http://localhost:8085/callback",
        scopes: list[str] = None,
        hub_frontend_url: str = None,
        hub_api_url: str = None,
        token_storage_key: str = "a4e-cli",
        config: OAuthConfig = None,
    ):
        if config:
            self.config = config
        else:
            self.config = OAuthConfig(
                client_id=client_id or os.getenv("A4E_OAUTH_CLIENT_ID", ""),
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes or ["read", "profile"],
                hub_frontend_url=hub_frontend_url
                or os.getenv("A4E_HUB_FRONTEND_URL", "http://localhost:3000"),
                hub_api_url=hub_api_url
                or os.getenv("A4E_HUB_API_URL", "http://localhost:8000"),
                token_storage_key=token_storage_key,
            )

        if not self.config.client_id:
            raise ValueError(
                "client_id is required. Provide it directly or set A4E_OAUTH_CLIENT_ID env var."
            )

        self._storage: TokenStorage | None = None
        if self.config.token_storage_key and KEYRING_AVAILABLE:
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

        Args:
            timeout: Maximum seconds to wait for authentication.
            open_browser: Whether to automatically open the browser.
            on_url_ready: Callback function called with the auth URL.

        Returns:
            dict: Token response containing access_token, refresh_token, etc.
        """
        code_verifier, code_challenge = generate_pkce()
        state = secrets.token_urlsafe(16)

        callback_server = CallbackServer()
        port = callback_server.start()

        redirect_uri = f"http://localhost:{port}/callback"

        auth_params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = (
            f"{self.config.hub_frontend_url}/oauth/authorize?{urlencode(auth_params)}"
        )

        if on_url_ready:
            on_url_ready(auth_url)

        if open_browser:
            webbrowser.open(auth_url)

        try:
            result = callback_server.wait_for_callback(timeout)

            if result.get("error"):
                raise OAuthError(
                    result["error"],
                    result.get("error_description", "Authentication failed"),
                )

            if result.get("state") != state:
                raise OAuthError(
                    "invalid_state", "State parameter mismatch - possible CSRF attack"
                )

            tokens = self._exchange_code(
                code=result["code"],
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )

            if self._storage:
                self._storage.save(tokens)

            self._current_tokens = tokens
            return tokens

        finally:
            callback_server.stop()

    def _exchange_code(self, code: str, redirect_uri: str, code_verifier: str) -> dict:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.config.client_id,
            "code_verifier": code_verifier,
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
                raise OAuthError(
                    error_data.get("error", "token_exchange_failed"),
                    error_data.get("error_description", response.text),
                )
            except json.JSONDecodeError:
                raise OAuthError("token_exchange_failed", response.text)

        return response.json()

    def refresh_tokens(self, refresh_token: str = None) -> dict:
        """Refresh the access token."""
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

        if self._storage:
            self._storage.save(tokens)

        self._current_tokens = tokens
        return tokens

    def revoke_token(self, token: str = None) -> bool:
        """Revoke an access or refresh token."""
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

        if self._storage:
            self._storage.clear()

        self._current_tokens = None
        return response.status_code == 200

    def introspect_token(self, token: str = None) -> dict:
        """Introspect a token to check its validity."""
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
        """Retrieve tokens from secure storage."""
        if self._storage:
            return self._storage.load()
        return self._current_tokens

    def clear_stored_tokens(self) -> None:
        """Remove tokens from secure storage."""
        if self._storage:
            self._storage.clear()
        self._current_tokens = None

    def get_access_token(self, auto_refresh: bool = True) -> str | None:
        """Get a valid access token, refreshing if necessary."""
        tokens = self.get_stored_tokens()
        if not tokens:
            return None

        access_token = tokens.get("access_token")

        if auto_refresh:
            introspection = self.introspect_token(access_token)
            if not introspection.get("active"):
                try:
                    tokens = self.refresh_tokens()
                    return tokens.get("access_token")
                except TokenRefreshError:
                    return None

        return access_token

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated with valid tokens."""
        tokens = self.get_stored_tokens()
        if not tokens:
            return False
        introspection = self.introspect_token(tokens.get("access_token"))
        return introspection.get("active", False)

    def get_user_info(self) -> dict | None:
        """Get user info from the stored token introspection."""
        tokens = self.get_stored_tokens()
        if not tokens:
            return None
        introspection = self.introspect_token(tokens.get("access_token"))
        if introspection.get("active"):
            return {
                "sub": introspection.get("sub"),
                "username": introspection.get("username"),
                "email": introspection.get("email"),
                "scope": introspection.get("scope"),
            }
        return None


def verify_token(token: str, hub_api_url: str = None) -> dict:
    """
    Verify an access token with the A4E Hub.

    Args:
        token: The access token to verify.
        hub_api_url: The A4E Hub API URL.

    Returns:
        dict: Token introspection response with 'active' boolean.
    """
    api_url = hub_api_url or os.getenv("A4E_HUB_API_URL", "http://localhost:8000")

    with httpx.Client() as client:
        response = client.post(
            f"{api_url}/api/oauth/introspect",
            data={"token": token},
        )

    if response.status_code == 200:
        return response.json()
    return {"active": False}

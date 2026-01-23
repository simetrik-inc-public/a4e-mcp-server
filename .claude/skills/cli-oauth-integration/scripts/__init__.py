"""
CLI OAuth Integration for A4E Hub

This package provides a reusable OAuth 2.0 client for Python CLI applications
integrating with A4E Hub's authorization server.

Example:
    from cli_oauth_integration.scripts import CLIOAuthClient

    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-app",
    )
    tokens = client.authenticate()
"""

from .cli_oauth_client import (
    CLIOAuthClient,
    OAuthConfig,
    OAuthError,
    AuthenticationTimeoutError,
    TokenRefreshError,
    CallbackServer,
    TokenStorage,
    generate_pkce,
    authenticate,
)

__all__ = [
    "CLIOAuthClient",
    "OAuthConfig",
    "OAuthError",
    "AuthenticationTimeoutError",
    "TokenRefreshError",
    "CallbackServer",
    "TokenStorage",
    "generate_pkce",
    "authenticate",
]

__version__ = "1.0.0"

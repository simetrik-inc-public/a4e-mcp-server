---
name: cli-oauth-integration
version: 1.0.0
description: Integrate Python CLI applications with A4E Hub OAuth 2.0 authentication
author: A4E Hub Team
tags:
  - oauth
  - cli
  - python
  - authentication
  - pkce
globs:
  - "**/*.py"
---

# CLI OAuth 2.0 Integration for A4E Hub

This skill helps you integrate Python CLI applications with A4E Hub's OAuth 2.0 authorization server using the Authorization Code Flow with PKCE.

## Overview

CLI applications have unique requirements for OAuth authentication:
- Cannot receive redirects like web applications
- Need to open a browser for user authentication
- Must run a temporary local server to receive the callback
- Should securely store tokens for subsequent use

This skill provides a complete solution for these challenges.

## Quick Start

### 1. Install Dependencies

```bash
pip install httpx keyring click
```

### 2. Use the OAuth Client

```python
from cli_oauth_client import CLIOAuthClient

# Initialize client
client = CLIOAuthClient(
    client_id="your-client-id",
    redirect_uri="http://localhost:8085/callback",
    scopes=["read", "profile"],
)

# Authenticate (opens browser)
tokens = client.authenticate()

# Use the access token
print(f"Access Token: {tokens['access_token']}")
```

## How It Works

1. **PKCE Generation**: Creates secure `code_verifier` and `code_challenge`
2. **Local Server**: Starts a temporary HTTP server to receive the OAuth callback
3. **Browser Auth**: Opens the user's browser to A4E Hub's consent page
4. **Token Exchange**: Exchanges the authorization code for access/refresh tokens
5. **Token Storage**: Optionally stores tokens securely using the system keyring

## Files Included

### Scripts

| File | Description |
|------|-------------|
| `scripts/cli_oauth_client.py` | Reusable OAuth 2.0 client library for CLI apps |
| `scripts/example_cli_app.py` | Complete example CLI application using the client |
| `scripts/test_cli_oauth.py` | Unit tests for the OAuth client |

### References

| File | Description |
|------|-------------|
| `references/README.md` | Detailed integration documentation |
| `references/TROUBLESHOOTING.md` | Common issues and solutions |

## API Reference

### CLIOAuthClient

```python
class CLIOAuthClient:
    def __init__(
        self,
        client_id: str,
        redirect_uri: str = "http://localhost:8085/callback",
        scopes: list[str] = None,
        hub_frontend_url: str = "http://localhost:3000",
        hub_api_url: str = "http://localhost:8000",
        token_storage_key: str = None,  # Enable keyring storage
    ):
        ...

    def authenticate(self, timeout: int = 300) -> dict:
        """
        Perform OAuth authentication flow.
        Opens browser, waits for callback, exchanges code for tokens.
        Returns: {"access_token": "...", "refresh_token": "...", ...}
        """

    def refresh_tokens(self, refresh_token: str = None) -> dict:
        """
        Refresh the access token using a refresh token.
        Returns new token set.
        """

    def revoke_token(self, token: str = None) -> bool:
        """
        Revoke an access or refresh token.
        Returns True if successful.
        """

    def get_stored_tokens(self) -> dict | None:
        """
        Retrieve tokens from secure storage (keyring).
        Returns None if no tokens stored.
        """

    def clear_stored_tokens(self) -> None:
        """
        Remove tokens from secure storage.
        """
```

## Security Features

- **PKCE (RFC 7636)**: Prevents authorization code interception
- **State Parameter**: CSRF protection
- **Secure Token Storage**: Uses system keyring (optional)
- **Token Refresh**: Automatic token refresh support
- **Token Revocation**: Clean logout functionality

## Integration Steps

### Step 1: Register OAuth Application

1. Go to A4E Hub Settings > OAuth Applications
2. Click "Create Application"
3. Set redirect URI to `http://localhost:8085/callback`
4. Copy the `client_id`

### Step 2: Copy the Client Library

Copy `scripts/cli_oauth_client.py` to your project.

### Step 3: Implement Authentication

```python
from cli_oauth_client import CLIOAuthClient

def main():
    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-cli-app",  # Enable secure storage
    )

    # Try to use stored tokens first
    tokens = client.get_stored_tokens()
    if not tokens:
        print("Please authenticate...")
        tokens = client.authenticate()

    # Make API calls with the token
    import httpx
    response = httpx.get(
        "http://localhost:8000/api/some-endpoint",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    print(response.json())

if __name__ == "__main__":
    main()
```

## Environment Variables

The client supports configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `A4E_HUB_FRONTEND_URL` | Frontend URL for consent page | `http://localhost:3000` |
| `A4E_HUB_API_URL` | Backend API URL | `http://localhost:8000` |
| `A4E_OAUTH_CLIENT_ID` | OAuth client ID | (required) |
| `A4E_OAUTH_REDIRECT_URI` | Callback URI | `http://localhost:8085/callback` |

## Testing

Run the included tests:

```bash
cd skills_external/cli-oauth-integration/scripts
pytest test_cli_oauth.py -v
```

## Troubleshooting

See `references/TROUBLESHOOTING.md` for common issues and solutions.

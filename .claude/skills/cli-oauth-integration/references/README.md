# CLI OAuth 2.0 Integration Guide

This guide explains how to integrate Python CLI applications with A4E Hub's OAuth 2.0 authorization server.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Step-by-Step Integration](#step-by-step-integration)
6. [API Reference](#api-reference)
7. [Security Best Practices](#security-best-practices)
8. [Advanced Usage](#advanced-usage)

## Overview

### Why OAuth for CLI Apps?

CLI applications face unique authentication challenges:

- **No browser context**: CLI apps run in terminals, not browsers
- **Credential security**: Apps shouldn't store user passwords
- **Token management**: Need to handle token expiration and refresh

OAuth 2.0 with PKCE solves these challenges by:

1. Opening the user's default browser for authentication
2. Running a temporary local server to receive the callback
3. Securely exchanging authorization codes for tokens
4. Optionally storing tokens in the system's secure credential store

### How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI App   │     │   Browser   │     │  A4E Hub    │     │  Local      │
│             │     │             │     │  (OAuth)    │     │  Server     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  1. Generate PKCE │                   │                   │
       │────────────────────────────────────────────────────────────
       │                   │                   │                   │
       │  2. Start local server               │                   │
       │───────────────────────────────────────────────────────────►
       │                   │                   │                   │
       │  3. Open browser  │                   │                   │
       │──────────────────►│                   │                   │
       │                   │  4. Load consent  │                   │
       │                   │──────────────────►│                   │
       │                   │                   │                   │
       │                   │  5. User approves │                   │
       │                   │──────────────────►│                   │
       │                   │                   │                   │
       │                   │  6. Redirect      │                   │
       │                   │◄──────────────────│                   │
       │                   │                   │                   │
       │                   │  7. Callback      │                   │
       │                   │───────────────────────────────────────►
       │                   │                   │                   │
       │  8. Receive code  │                   │                   │
       │◄──────────────────────────────────────────────────────────
       │                   │                   │                   │
       │  9. Exchange code for tokens         │                   │
       │──────────────────────────────────────►│                   │
       │                   │                   │                   │
       │  10. Receive tokens                  │                   │
       │◄──────────────────────────────────────│                   │
       │                   │                   │                   │
       │  11. Make API calls with token       │                   │
       │──────────────────────────────────────►│                   │
       │                   │                   │                   │
```

## Prerequisites

### Requirements

- Python 3.9+
- A4E Hub running locally or accessible via network
- Registered OAuth application in A4E Hub

### Install Dependencies

```bash
pip install httpx keyring
```

Optional for enhanced CLI experience:
```bash
pip install click rich
```

### Register OAuth Application

1. Log in to A4E Hub
2. Go to **Settings** > **OAuth Applications**
3. Click **Create Application**
4. Fill in the details:
   - **Name**: Your CLI app name
   - **Redirect URI**: `http://localhost:8085/callback`
   - **Scopes**: Select required scopes (read, profile, etc.)
5. Save the `client_id` - you'll need it

## Quick Start

### Minimal Example

```python
from cli_oauth_client import CLIOAuthClient

# Initialize client
client = CLIOAuthClient(
    client_id="your-client-id-here",
    scopes=["read", "profile"],
)

# Authenticate (opens browser)
tokens = client.authenticate()

# Use the access token for API calls
import httpx

response = httpx.get(
    "http://localhost:8000/api/users/me",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)

print(response.json())
```

### With Token Storage

```python
from cli_oauth_client import CLIOAuthClient

client = CLIOAuthClient(
    client_id="your-client-id",
    token_storage_key="my-cli-app",  # Enables secure storage
)

# Check for existing tokens first
tokens = client.get_stored_tokens()
if not tokens:
    tokens = client.authenticate()

# Get access token (auto-refreshes if expired)
access_token = client.get_access_token(auto_refresh=True)
```

## Architecture

### Components

```
cli_oauth_client.py
├── CLIOAuthClient        # Main client class
├── OAuthConfig           # Configuration dataclass
├── CallbackServer        # Local HTTP server for OAuth callback
├── CallbackHandler       # HTTP request handler
├── TokenStorage          # Secure token storage (keyring)
├── generate_pkce()       # PKCE code generation
└── Exceptions
    ├── OAuthError
    ├── AuthenticationTimeoutError
    └── TokenRefreshError
```

### Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIOAuthClient                           │
├─────────────────────────────────────────────────────────────────┤
│ - config: OAuthConfig                                           │
│ - _storage: TokenStorage | None                                 │
│ - _current_tokens: dict | None                                  │
├─────────────────────────────────────────────────────────────────┤
│ + authenticate(timeout, open_browser, on_url_ready) -> dict     │
│ + refresh_tokens(refresh_token) -> dict                         │
│ + revoke_token(token) -> bool                                   │
│ + introspect_token(token) -> dict                               │
│ + get_stored_tokens() -> dict | None                            │
│ + clear_stored_tokens() -> None                                 │
│ + get_access_token(auto_refresh) -> str | None                  │
│ - _exchange_code(code, redirect_uri, code_verifier) -> dict     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌───────────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│     OAuthConfig       │  │  CallbackServer  │  │  TokenStorage   │
├───────────────────────┤  ├──────────────────┤  ├─────────────────┤
│ client_id             │  │ port: int        │  │ storage_key     │
│ client_secret         │  │ result: dict     │  ├─────────────────┤
│ redirect_uri          │  ├──────────────────┤  │ + save(tokens)  │
│ scopes                │  │ + start() -> int │  │ + load() -> dict│
│ hub_frontend_url      │  │ + wait_for_...() │  │ + clear()       │
│ hub_api_url           │  │ + stop()         │  └─────────────────┘
│ token_storage_key     │  └──────────────────┘
└───────────────────────┘
```

## Step-by-Step Integration

### Step 1: Copy the Client Library

Copy `cli_oauth_client.py` to your project:

```
your-project/
├── your_app.py
├── cli_oauth_client.py  # <-- Copy here
└── requirements.txt
```

### Step 2: Configure the Client

```python
from cli_oauth_client import CLIOAuthClient, OAuthConfig

# Option 1: Direct parameters
client = CLIOAuthClient(
    client_id="your-client-id",
    scopes=["read", "profile"],
    hub_api_url="http://localhost:8000",
    hub_frontend_url="http://localhost:3000",
)

# Option 2: Config object
config = OAuthConfig(
    client_id="your-client-id",
    scopes=["read", "profile", "agents"],
    hub_api_url="https://api.a4ehub.example.com",
    hub_frontend_url="https://a4ehub.example.com",
    token_storage_key="my-app",
)
client = CLIOAuthClient(config=config)

# Option 3: Environment variables
# Set: A4E_OAUTH_CLIENT_ID, A4E_HUB_API_URL, etc.
config = OAuthConfig.from_env()
client = CLIOAuthClient(config=config)
```

### Step 3: Implement Login Flow

```python
def login():
    """Authenticate user with A4E Hub."""
    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-app",
    )

    # Check existing tokens
    tokens = client.get_stored_tokens()
    if tokens:
        # Verify token is still valid
        introspection = client.introspect_token()
        if introspection.get("active"):
            print(f"Already logged in as {introspection.get('username')}")
            return tokens

    # Perform OAuth flow
    print("Opening browser for authentication...")
    tokens = client.authenticate(timeout=300)
    print("Login successful!")

    return tokens
```

### Step 4: Make Authenticated API Calls

```python
import httpx
from cli_oauth_client import CLIOAuthClient, TokenRefreshError

def make_api_request(endpoint: str, method: str = "GET", data: dict = None):
    """Make an authenticated API request."""
    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-app",
    )

    # Get valid access token (auto-refreshes if needed)
    access_token = client.get_access_token(auto_refresh=True)
    if not access_token:
        raise Exception("Not authenticated. Please login first.")

    # Make the request
    with httpx.Client() as http:
        response = http.request(
            method=method,
            url=f"http://localhost:8000{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=data,
        )

    response.raise_for_status()
    return response.json()
```

### Step 5: Implement Logout

```python
def logout():
    """Log out and revoke tokens."""
    client = CLIOAuthClient(
        client_id="your-client-id",
        token_storage_key="my-app",
    )

    # Revoke token on server
    client.revoke_token()

    # Clear local storage
    client.clear_stored_tokens()

    print("Logged out successfully.")
```

## API Reference

### CLIOAuthClient

#### Constructor

```python
CLIOAuthClient(
    client_id: str = None,
    client_secret: str = None,
    redirect_uri: str = "http://localhost:8085/callback",
    scopes: list[str] = None,
    hub_frontend_url: str = "http://localhost:3000",
    hub_api_url: str = "http://localhost:8000",
    token_storage_key: str = None,
    config: OAuthConfig = None,
)
```

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `authenticate(timeout=300, open_browser=True, on_url_ready=None)` | Perform OAuth flow | `dict` with tokens |
| `refresh_tokens(refresh_token=None)` | Refresh access token | `dict` with new tokens |
| `revoke_token(token=None)` | Revoke a token | `bool` |
| `introspect_token(token=None)` | Check token validity | `dict` with token info |
| `get_stored_tokens()` | Get tokens from storage | `dict` or `None` |
| `clear_stored_tokens()` | Remove stored tokens | `None` |
| `get_access_token(auto_refresh=True)` | Get valid access token | `str` or `None` |

### OAuthConfig

```python
@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str | None = None
    redirect_uri: str = "http://localhost:8085/callback"
    scopes: list[str] = field(default_factory=lambda: ["read", "profile"])
    hub_frontend_url: str = "http://localhost:3000"
    hub_api_url: str = "http://localhost:8000"
    token_storage_key: str | None = None
```

### Exceptions

| Exception | When Raised |
|-----------|-------------|
| `OAuthError` | General OAuth errors |
| `AuthenticationTimeoutError` | User didn't complete auth in time |
| `TokenRefreshError` | Token refresh failed |

## Security Best Practices

### 1. Always Use PKCE

PKCE (Proof Key for Code Exchange) is always enabled and protects against authorization code interception attacks.

### 2. Store Tokens Securely

Use the `token_storage_key` option to store tokens in the system keyring:

```python
client = CLIOAuthClient(
    client_id="...",
    token_storage_key="my-app",  # Uses system keyring
)
```

This stores tokens in:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring, KWallet)

### 3. Handle Token Expiration

Always use `get_access_token(auto_refresh=True)` to automatically refresh expired tokens:

```python
access_token = client.get_access_token(auto_refresh=True)
if not access_token:
    # Token couldn't be refreshed, need re-authentication
    tokens = client.authenticate()
```

### 4. Revoke Tokens on Logout

Always revoke tokens when the user logs out:

```python
client.revoke_token()
client.clear_stored_tokens()
```

### 5. Minimize Requested Scopes

Only request the scopes your application actually needs:

```python
# Bad: requesting all scopes
client = CLIOAuthClient(client_id="...", scopes=["read", "write", "profile", "agents"])

# Good: only what's needed
client = CLIOAuthClient(client_id="...", scopes=["read"])
```

### 6. Use Environment Variables for Sensitive Config

```bash
export A4E_OAUTH_CLIENT_ID="your-client-id"
export A4E_OAUTH_CLIENT_SECRET="your-secret"  # Only for confidential clients
```

```python
config = OAuthConfig.from_env()
client = CLIOAuthClient(config=config)
```

## Advanced Usage

### Custom Callback Handler

Override the URL callback behavior:

```python
def my_url_handler(auth_url: str):
    """Custom handler for the authorization URL."""
    print(f"Please visit this URL to authenticate:")
    print(f"\n  {auth_url}\n")
    # Maybe copy to clipboard, send via notification, etc.

tokens = client.authenticate(
    open_browser=False,
    on_url_ready=my_url_handler,
)
```

### Headless/Server Environment

For environments without a browser:

```python
def authenticate_headless():
    client = CLIOAuthClient(client_id="...")

    auth_url = None

    def capture_url(url: str):
        nonlocal auth_url
        auth_url = url

    # Start authentication without opening browser
    import threading

    def auth_flow():
        return client.authenticate(open_browser=False, on_url_ready=capture_url)

    thread = threading.Thread(target=auth_flow)
    thread.start()

    # Wait for URL to be generated
    import time
    while auth_url is None:
        time.sleep(0.1)

    # Display URL for user to visit manually
    print(f"Visit this URL on any device: {auth_url}")

    thread.join()
```

### Multiple Environments

Support different environments:

```python
import os

ENVIRONMENTS = {
    "local": {
        "hub_api_url": "http://localhost:8000",
        "hub_frontend_url": "http://localhost:3000",
    },
    "staging": {
        "hub_api_url": "https://api.staging.a4ehub.com",
        "hub_frontend_url": "https://staging.a4ehub.com",
    },
    "production": {
        "hub_api_url": "https://api.a4ehub.com",
        "hub_frontend_url": "https://a4ehub.com",
    },
}

env = os.getenv("A4E_ENV", "local")
config = ENVIRONMENTS.get(env, ENVIRONMENTS["local"])

client = CLIOAuthClient(
    client_id="...",
    **config,
)
```

### Async Support

Wrap the synchronous client for async applications:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)

async def authenticate_async():
    client = CLIOAuthClient(client_id="...")
    loop = asyncio.get_event_loop()
    tokens = await loop.run_in_executor(executor, client.authenticate)
    return tokens
```

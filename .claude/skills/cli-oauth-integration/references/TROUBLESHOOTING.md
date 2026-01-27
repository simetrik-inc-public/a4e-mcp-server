# Troubleshooting Guide

This guide covers common issues and solutions when integrating CLI applications with A4E Hub OAuth 2.0.

## Table of Contents

1. [Authentication Errors](#authentication-errors)
2. [Token Issues](#token-issues)
3. [Network and Connection Errors](#network-and-connection-errors)
4. [Browser Issues](#browser-issues)
5. [Token Storage Issues](#token-storage-issues)
6. [PKCE Errors](#pkce-errors)
7. [Debugging Tips](#debugging-tips)

---

## Authentication Errors

### `invalid_client` - Unknown client_id

**Symptoms:**
```
OAuthError: invalid_client: Unknown client_id
```

**Causes:**
- Client ID is incorrect or mistyped
- OAuth application was deleted
- Using wrong environment (local vs production)

**Solutions:**

1. Verify your client_id:
   ```python
   print(f"Using client_id: {client.config.client_id}")
   ```

2. Check the OAuth application exists in A4E Hub:
   - Go to Settings > OAuth Applications
   - Verify your app is listed

3. Ensure you're connecting to the right environment:
   ```python
   client = CLIOAuthClient(
       client_id="your-client-id",
       hub_api_url="http://localhost:8000",  # Check this URL
   )
   ```

---

### `invalid_redirect_uri` - Redirect URI mismatch

**Symptoms:**
```
OAuthError: invalid_redirect_uri: Redirect URI doesn't match registered URIs
```

**Causes:**
- Redirect URI doesn't exactly match what's registered
- Port mismatch
- HTTP vs HTTPS mismatch
- Missing or extra trailing slash

**Solutions:**

1. Check registered redirect URIs in A4E Hub settings

2. Ensure exact match (including port):
   ```python
   # Registered: http://localhost:8085/callback
   client = CLIOAuthClient(
       redirect_uri="http://localhost:8085/callback",  # Must match exactly
   )
   ```

3. Add multiple URIs if needed (in A4E Hub settings):
   - `http://localhost:8085/callback`
   - `http://127.0.0.1:8085/callback`

---

### `invalid_scope` - Scope not allowed

**Symptoms:**
```
OAuthError: invalid_scope: Scope 'write' is not allowed for this application
```

**Causes:**
- Requesting scopes not granted to the OAuth application
- Typo in scope name

**Solutions:**

1. Check allowed scopes in A4E Hub OAuth application settings

2. Only request allowed scopes:
   ```python
   # If app only has 'read' and 'profile' permissions:
   client = CLIOAuthClient(
       client_id="...",
       scopes=["read", "profile"],  # Don't include 'write' if not allowed
   )
   ```

3. Update OAuth application permissions if needed

---

### `access_denied` - User denied consent

**Symptoms:**
```
OAuthError: access_denied: User denied the authorization request
```

**Causes:**
- User clicked "Deny" on the consent page
- User closed the browser window

**Solutions:**

1. This is expected user behavior - handle gracefully:
   ```python
   try:
       tokens = client.authenticate()
   except OAuthError as e:
       if e.error == "access_denied":
           print("Authorization was denied. Please try again.")
           return
       raise
   ```

---

### `authentication_timeout` - Timeout waiting for callback

**Symptoms:**
```
AuthenticationTimeoutError: Authentication timed out after 300 seconds
```

**Causes:**
- User didn't complete authentication in time
- Browser didn't redirect back
- Callback server issues

**Solutions:**

1. Increase timeout if needed:
   ```python
   tokens = client.authenticate(timeout=600)  # 10 minutes
   ```

2. Ensure the callback URL is reachable:
   ```bash
   curl http://localhost:8085/callback?code=test
   ```

3. Check firewall/antivirus isn't blocking the local server

---

## Token Issues

### `invalid_grant` - Authorization code expired or already used

**Symptoms:**
```
OAuthError: invalid_grant: Authorization code has expired
OAuthError: invalid_grant: Authorization code has already been used
```

**Causes:**
- Authorization codes are single-use and expire after 10 minutes
- Code was already exchanged for tokens

**Solutions:**

1. Ensure code is exchanged immediately after callback
2. Don't retry token exchange with the same code - start a new auth flow

---

### `invalid_grant` - Refresh token expired or revoked

**Symptoms:**
```
TokenRefreshError: invalid_grant: Refresh token has expired
```

**Causes:**
- Refresh token expired (30-day lifetime)
- Token was revoked

**Solutions:**

1. Re-authenticate the user:
   ```python
   try:
       tokens = client.refresh_tokens()
   except TokenRefreshError:
       # Token can't be refreshed, need full re-auth
       client.clear_stored_tokens()
       tokens = client.authenticate()
   ```

---

### Token introspection returns `active: false`

**Symptoms:**
```python
introspection = client.introspect_token()
print(introspection)  # {'active': False}
```

**Causes:**
- Token has expired
- Token was revoked
- Token is malformed

**Solutions:**

1. Try refreshing the token:
   ```python
   if not client.introspect_token().get("active"):
       try:
           client.refresh_tokens()
       except TokenRefreshError:
           client.authenticate()
   ```

---

## Network and Connection Errors

### Connection refused

**Symptoms:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**Causes:**
- A4E Hub backend is not running
- Wrong API URL configured
- Firewall blocking connection

**Solutions:**

1. Verify A4E Hub is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check configuration:
   ```python
   print(f"API URL: {client.config.hub_api_url}")
   ```

3. Check firewall settings

---

### SSL/TLS errors

**Symptoms:**
```
ssl.SSLCertVerificationError: certificate verify failed
```

**Causes:**
- Self-signed certificate
- Invalid certificate
- Missing CA certificates

**Solutions:**

1. For development with self-signed certs (NOT for production):
   ```python
   import httpx

   # In cli_oauth_client.py, modify HTTP client creation:
   with httpx.Client(verify=False) as client:
       ...
   ```

2. For production, ensure valid SSL certificate is installed

---

## Browser Issues

### Browser doesn't open automatically

**Symptoms:**
- Authentication starts but no browser window appears
- Message says "Opening browser..." but nothing happens

**Causes:**
- No default browser configured
- Running in headless environment
- Browser blocked by system settings

**Solutions:**

1. Open URL manually:
   ```python
   def handle_url(url: str):
       print(f"Please open this URL manually:\n{url}")

   tokens = client.authenticate(
       open_browser=False,
       on_url_ready=handle_url,
   )
   ```

2. Set default browser in system settings

---

### Browser opens but shows error page

**Symptoms:**
- Browser opens but A4E Hub shows an error
- "Invalid request" or similar error message

**Causes:**
- Invalid OAuth parameters
- A4E Hub frontend not running

**Solutions:**

1. Verify frontend is accessible:
   ```bash
   curl http://localhost:3000
   ```

2. Check browser console for errors (F12 > Console)

3. Verify OAuth parameters by printing the auth URL:
   ```python
   def debug_url(url: str):
       print(f"Auth URL: {url}")
       # Check URL has all required parameters

   client.authenticate(on_url_ready=debug_url)
   ```

---

## Token Storage Issues

### `ImportError: keyring package not found`

**Symptoms:**
```
ImportError: keyring package is required for secure token storage
```

**Causes:**
- keyring package not installed

**Solutions:**

```bash
pip install keyring
```

---

### Keyring backend not available

**Symptoms:**
```
keyring.errors.NoKeyringError: No recommended backend was available
```

**Causes:**
- No keyring backend installed (common on headless Linux)

**Solutions:**

1. Install a backend:
   ```bash
   # On Linux
   pip install secretstorage  # For GNOME
   pip install keyrings.alt   # Alternative backends
   ```

2. Or disable token storage:
   ```python
   client = CLIOAuthClient(
       client_id="...",
       token_storage_key=None,  # Disable storage
   )
   ```

---

### Stored tokens not found

**Symptoms:**
```python
tokens = client.get_stored_tokens()
print(tokens)  # None
```

**Causes:**
- Tokens were never stored
- Different storage key used
- Keyring was cleared

**Solutions:**

1. Verify storage key is consistent:
   ```python
   # Always use the same storage key
   STORAGE_KEY = "my-app-tokens"

   client = CLIOAuthClient(
       client_id="...",
       token_storage_key=STORAGE_KEY,
   )
   ```

2. Check keyring directly:
   ```python
   import keyring
   data = keyring.get_password("a4e-hub-oauth", "my-app-tokens")
   print(data)
   ```

---

## PKCE Errors

### `invalid_pkce` - Code verifier doesn't match

**Symptoms:**
```
OAuthError: invalid_pkce: Code verifier doesn't match the code challenge
```

**Causes:**
- Different code_verifier used for auth request and token exchange
- Code verifier was corrupted or truncated

**Solutions:**

1. This is handled automatically by the client, but if you see this:
   - Ensure you're not modifying the code_verifier between requests
   - Check for encoding issues

2. Verify PKCE manually:
   ```python
   import base64
   import hashlib

   code_verifier = "your-code-verifier"
   expected_challenge = (
       base64.urlsafe_b64encode(
           hashlib.sha256(code_verifier.encode()).digest()
       )
       .rstrip(b"=")
       .decode()
   )
   print(f"Expected challenge: {expected_challenge}")
   ```

---

## Debugging Tips

### Enable verbose logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

### Print configuration

```python
client = CLIOAuthClient(client_id="...", ...)

print("Configuration:")
print(f"  Client ID: {client.config.client_id}")
print(f"  API URL: {client.config.hub_api_url}")
print(f"  Frontend URL: {client.config.hub_frontend_url}")
print(f"  Redirect URI: {client.config.redirect_uri}")
print(f"  Scopes: {client.config.scopes}")
```

### Test API connectivity

```python
import httpx

# Test backend health
try:
    response = httpx.get("http://localhost:8000/health")
    print(f"Backend health: {response.status_code}")
except Exception as e:
    print(f"Backend error: {e}")

# Test frontend
try:
    response = httpx.get("http://localhost:3000")
    print(f"Frontend status: {response.status_code}")
except Exception as e:
    print(f"Frontend error: {e}")
```

### Inspect token contents

```python
# Get token info
introspection = client.introspect_token()
print(f"Token active: {introspection.get('active')}")
print(f"Scopes: {introspection.get('scope')}")
print(f"Username: {introspection.get('username')}")
print(f"Client ID: {introspection.get('client_id')}")

# Check expiration
import datetime
if 'exp' in introspection:
    exp_time = datetime.datetime.fromtimestamp(introspection['exp'])
    print(f"Expires at: {exp_time}")
```

### Check callback server

```python
from cli_oauth_client import CallbackServer

# Test callback server independently
server = CallbackServer(port=8085)
port = server.start()
print(f"Server started on port {port}")

# Test it
import httpx
response = httpx.get(f"http://localhost:{port}/callback?code=test&state=test")
print(f"Callback response: {response.status_code}")

server.stop()
```

---

## Getting Help

If you're still having issues:

1. Check the A4E Hub logs for server-side errors
2. Review the OAuth 2.0 implementation documentation
3. Open an issue with:
   - Error message (full stack trace)
   - Configuration (without secrets)
   - Steps to reproduce
   - Environment details (OS, Python version)

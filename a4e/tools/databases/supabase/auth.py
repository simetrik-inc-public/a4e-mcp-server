"""
Supabase authentication helpers.
"""

from typing import Optional, Dict, Any
import json

from ....core import mcp

# Try to import dependencies
try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@mcp.tool()
def supabase_get_user(
    url: str,
    key: str,
    access_token: str,
) -> dict:
    """
    Get user information from an access token.
    
    This verifies the JWT and returns the user's profile.
    
    Args:
        url: Supabase project URL
        key: Supabase API key (anon or service_role)
        access_token: User's JWT access token
    
    Returns:
        User profile information
    
    Example:
        supabase_get_user(
            url="https://xxx.supabase.co",
            key="...",
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            # Get user from token
            user = client.auth.get_user(access_token)
            
            if user and user.user:
                return {
                    "success": True,
                    "user": {
                        "id": user.user.id,
                        "email": user.user.email,
                        "phone": user.user.phone,
                        "created_at": user.user.created_at,
                        "updated_at": user.user.updated_at,
                        "email_confirmed_at": user.user.email_confirmed_at,
                        "role": user.user.role,
                        "app_metadata": user.user.app_metadata,
                        "user_metadata": user.user.user_metadata,
                    },
                }
            return {"success": False, "error": "User not found"}
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "invalid" in error_msg.lower():
                return {"success": False, "error": "Invalid or expired token"}
            return {"success": False, "error": error_msg}
    
    # Fallback to REST API
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed. Run: pip install httpx"}
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {access_token}",
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{url.rstrip('/')}/auth/v1/user",
                headers=headers,
            )
            
            if response.status_code == 401:
                return {"success": False, "error": "Invalid or expired token"}
            elif response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            user_data = response.json()
            return {
                "success": True,
                "user": user_data,
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def supabase_list_users(
    url: str,
    service_role_key: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """
    List all users in the Supabase project.
    
    IMPORTANT: This requires the service_role key, not the anon key.
    
    Args:
        url: Supabase project URL
        service_role_key: Supabase service_role key (has admin access)
        page: Page number (default 1)
        per_page: Users per page (default 50, max 1000)
    
    Returns:
        List of users with pagination info
    
    Example:
        supabase_list_users(
            url="https://xxx.supabase.co",
            service_role_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            page=1,
            per_page=100
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, service_role_key)
            # Admin API requires service_role key
            result = client.auth.admin.list_users(
                page=page,
                per_page=min(per_page, 1000),
            )
            
            users = []
            for user in result:
                users.append({
                    "id": user.id,
                    "email": user.email,
                    "phone": user.phone,
                    "created_at": user.created_at,
                    "email_confirmed_at": user.email_confirmed_at,
                    "last_sign_in_at": user.last_sign_in_at,
                    "role": user.role,
                })
            
            return {
                "success": True,
                "users": users,
                "count": len(users),
                "page": page,
                "per_page": per_page,
            }
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                return {
                    "success": False,
                    "error": "Access denied. Make sure you're using the service_role key, not the anon key.",
                }
            return {"success": False, "error": error_msg}
    
    # Fallback to REST API
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed. Run: pip install httpx"}
    
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{url.rstrip('/')}/auth/v1/admin/users",
                headers=headers,
                params={"page": page, "per_page": min(per_page, 1000)},
            )
            
            if response.status_code == 401 or response.status_code == 403:
                return {
                    "success": False,
                    "error": "Access denied. Make sure you're using the service_role key.",
                }
            elif response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            data = response.json()
            users = data.get("users", data) if isinstance(data, dict) else data
            
            return {
                "success": True,
                "users": users,
                "count": len(users),
                "page": page,
                "per_page": per_page,
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def supabase_create_user(
    url: str,
    service_role_key: str,
    email: str,
    password: str,
    user_metadata: Optional[Dict[str, Any]] = None,
    email_confirm: bool = True,
) -> dict:
    """
    Create a new user in Supabase.
    
    IMPORTANT: This requires the service_role key.
    
    Args:
        url: Supabase project URL
        service_role_key: Supabase service_role key
        email: User's email address
        password: User's password
        user_metadata: Optional metadata to store with the user
        email_confirm: Whether to auto-confirm the email (default True)
    
    Returns:
        Created user information
    
    Example:
        supabase_create_user(
            url="https://xxx.supabase.co",
            service_role_key="...",
            email="newuser@example.com",
            password="securepassword123",
            user_metadata={"name": "John Doe"}
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, service_role_key)
            
            result = client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": email_confirm,
                "user_metadata": user_metadata or {},
            })
            
            if result.user:
                return {
                    "success": True,
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "created_at": result.user.created_at,
                    },
                    "message": f"User created: {email}",
                }
            return {"success": False, "error": "Failed to create user"}
            
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return {"success": False, "error": f"User with email {email} already exists"}
            return {"success": False, "error": error_msg}
    
    # Fallback to REST API
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed"}
    
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "email": email,
        "password": password,
        "email_confirm": email_confirm,
    }
    if user_metadata:
        payload["user_metadata"] = user_metadata
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{url.rstrip('/')}/auth/v1/admin/users",
                headers=headers,
                json=payload,
            )
            
            if response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            user_data = response.json()
            return {
                "success": True,
                "user": user_data,
                "message": f"User created: {email}",
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def supabase_delete_user(
    url: str,
    service_role_key: str,
    user_id: str,
) -> dict:
    """
    Delete a user from Supabase.
    
    IMPORTANT: This requires the service_role key.
    
    Args:
        url: Supabase project URL
        service_role_key: Supabase service_role key
        user_id: UUID of the user to delete
    
    Returns:
        Deletion confirmation
    
    Example:
        supabase_delete_user(
            url="https://xxx.supabase.co",
            service_role_key="...",
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, service_role_key)
            client.auth.admin.delete_user(user_id)
            
            return {
                "success": True,
                "message": f"User {user_id} deleted successfully",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed"}
    
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.delete(
                f"{url.rstrip('/')}/auth/v1/admin/users/{user_id}",
                headers=headers,
            )
            
            if response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            return {
                "success": True,
                "message": f"User {user_id} deleted successfully",
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

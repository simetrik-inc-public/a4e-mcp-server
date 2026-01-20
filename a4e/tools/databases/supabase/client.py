"""
Supabase client connection and validation tools.
"""

from typing import Optional, Dict, Any
import json
import os

from ....core import mcp, get_project_dir

# Try to import supabase, fall back to httpx
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# Global connection cache
_connections: Dict[str, Any] = {}


def _get_connection(url: str, key: str) -> Any:
    """Get or create a Supabase connection."""
    cache_key = f"{url}:{key[:10]}"
    
    if cache_key in _connections:
        return _connections[cache_key]
    
    if HAS_SUPABASE:
        client = create_client(url, key)
        _connections[cache_key] = client
        return client
    
    return None


def _make_request(url: str, key: str, endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make a direct REST API request to Supabase."""
    if not HAS_HTTPX:
        return {"error": "httpx not installed. Run: pip install httpx"}
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    
    full_url = f"{url.rstrip('/')}/rest/v1/{endpoint}"
    
    with httpx.Client(timeout=30.0) as client:
        if method == "GET":
            response = client.get(full_url, headers=headers)
        elif method == "POST":
            response = client.post(full_url, headers=headers, json=data)
        elif method == "PATCH":
            response = client.patch(full_url, headers=headers, json=data)
        elif method == "DELETE":
            response = client.delete(full_url, headers=headers)
        else:
            return {"error": f"Unknown method: {method}"}
        
        if response.status_code >= 400:
            return {
                "error": f"HTTP {response.status_code}: {response.text}",
                "status_code": response.status_code,
            }
        
        try:
            return response.json() if response.text else {}
        except json.JSONDecodeError:
            return {"raw": response.text}


@mcp.tool()
def supabase_connect(
    url: str,
    key: str,
    save_config: bool = True,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Initialize and validate a Supabase connection.
    
    This tool connects to your Supabase project and optionally saves
    the configuration for future use.
    
    Args:
        url: Supabase project URL (https://xxx.supabase.co)
        key: Supabase API key (anon or service_role)
        save_config: Whether to save connection config to agent's db_config.json
        agent_name: Agent to configure (uses current project if not specified)
    
    Returns:
        Connection status and project info
    
    Example:
        supabase_connect(
            url="https://myproject.supabase.co",
            key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
    """
    # Validate URL format
    if not url.startswith("https://") or "supabase.co" not in url:
        return {
            "success": False,
            "error": "Invalid Supabase URL. Expected format: https://xxx.supabase.co",
        }
    
    # Extract project ref
    project_ref = url.replace("https://", "").split(".")[0]
    
    # Test connection by listing tables
    validation = supabase_validate(url, key)
    
    if not validation.get("valid"):
        return {
            "success": False,
            "error": validation.get("error", "Connection failed"),
        }
    
    # Save config if requested
    if save_config:
        project_dir = get_project_dir(agent_name)
        config_path = project_dir / "db_config.json"
        
        existing_config = {}
        if config_path.exists():
            try:
                existing_config = json.loads(config_path.read_text())
            except json.JSONDecodeError:
                pass
        
        existing_config["db_type"] = "supabase"
        existing_config["supabase_url"] = url
        existing_config["required_secrets"] = ["SUPABASE_URL", "SUPABASE_KEY"]
        
        config_path.write_text(json.dumps(existing_config, indent=2))
    
    return {
        "success": True,
        "message": f"Connected to Supabase project: {project_ref}",
        "project_ref": project_ref,
        "tables": validation.get("tables", []),
        "table_count": len(validation.get("tables", [])),
        "using_sdk": HAS_SUPABASE,
    }


@mcp.tool()
def supabase_validate(
    url: str,
    key: str,
) -> dict:
    """
    Validate Supabase connection and return project info.
    
    Tests the connection without saving any configuration.
    Returns project name and available tables.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
    
    Returns:
        Validation result with project info and tables
    """
    # Validate URL format
    if not url.startswith("https://") or "supabase.co" not in url:
        return {
            "valid": False,
            "error": "Invalid Supabase URL. Expected format: https://xxx.supabase.co",
        }
    
    project_ref = url.replace("https://", "").split(".")[0]
    
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            # Try to get tables from information_schema
            result = client.from_("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
            tables = [row["table_name"] for row in result.data] if result.data else []
            
            return {
                "valid": True,
                "project_name": project_ref,
                "tables": tables,
            }
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Invalid API key" in error_msg.lower():
                return {"valid": False, "error": "Invalid API key"}
            elif "404" in error_msg:
                return {"valid": False, "error": "Project not found"}
            return {"valid": False, "error": error_msg}
    
    elif HAS_HTTPX:
        try:
            # Use REST API to test connection
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
            }
            
            with httpx.Client(timeout=30.0) as client:
                # Try the REST API root to get available tables
                response = client.get(f"{url.rstrip('/')}/rest/v1/", headers=headers)
                
                if response.status_code == 401:
                    return {"valid": False, "error": "Invalid API key"}
                elif response.status_code == 404:
                    return {"valid": False, "error": "Project not found"}
                elif response.status_code >= 400:
                    return {"valid": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
                # Parse OpenAPI spec to get table names
                try:
                    spec = response.json()
                    tables = []
                    if "paths" in spec:
                        for path in spec["paths"]:
                            if path.startswith("/") and not path.startswith("/rpc"):
                                table_name = path.strip("/")
                                if table_name:
                                    tables.append(table_name)
                    elif "definitions" in spec:
                        tables = list(spec["definitions"].keys())
                    
                    return {
                        "valid": True,
                        "project_name": project_ref,
                        "tables": tables,
                    }
                except json.JSONDecodeError:
                    # Connection works but can't parse response
                    return {
                        "valid": True,
                        "project_name": project_ref,
                        "tables": [],
                        "note": "Connected but could not list tables",
                    }
                    
        except httpx.ConnectError:
            return {"valid": False, "error": "Could not connect to Supabase"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    else:
        return {
            "valid": False,
            "error": "No HTTP client available. Install supabase or httpx: pip install supabase",
        }


@mcp.tool()
def supabase_list_tables(
    url: str,
    key: str,
) -> dict:
    """
    List all tables in the Supabase database.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
    
    Returns:
        List of table names with optional schema info
    """
    validation = supabase_validate(url, key)
    
    if not validation.get("valid"):
        return {
            "success": False,
            "error": validation.get("error"),
        }
    
    return {
        "success": True,
        "tables": validation.get("tables", []),
        "count": len(validation.get("tables", [])),
    }

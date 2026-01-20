"""
Supabase query operations (CRUD).
"""

from typing import Optional, Dict, Any, List
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


def _build_filter_query(base_url: str, filters: Dict[str, Any]) -> str:
    """Build PostgREST filter query string."""
    if not filters:
        return base_url
    
    parts = []
    for key, value in filters.items():
        if isinstance(value, dict):
            # Handle operators: {"column": {"eq": "value"}}
            for op, val in value.items():
                parts.append(f"{key}={op}.{val}")
        else:
            # Default to equals
            parts.append(f"{key}=eq.{value}")
    
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{'&'.join(parts)}"


def _make_supabase_request(
    url: str, 
    key: str, 
    table: str, 
    method: str = "GET", 
    data: Any = None,
    filters: Dict[str, Any] = None,
    select: str = "*",
    limit: int = None,
    order: str = None,
) -> dict:
    """Make a REST API request to Supabase."""
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed. Run: pip install httpx"}
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    
    # Build URL with query params
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    params = []
    
    if select:
        params.append(f"select={select}")
    if limit:
        params.append(f"limit={limit}")
    if order:
        params.append(f"order={order}")
    
    if params:
        endpoint = f"{endpoint}?{'&'.join(params)}"
    
    # Add filters
    if filters:
        endpoint = _build_filter_query(endpoint, filters)
    
    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            elif method == "POST":
                response = client.post(endpoint, headers=headers, json=data)
            elif method == "PATCH":
                response = client.patch(endpoint, headers=headers, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=headers)
            else:
                return {"success": False, "error": f"Unknown method: {method}"}
            
            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code,
                }
            
            try:
                result = response.json() if response.text else []
                return {"success": True, "data": result}
            except json.JSONDecodeError:
                return {"success": True, "data": response.text}
                
    except httpx.ConnectError:
        return {"success": False, "error": "Could not connect to Supabase"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def supabase_select(
    url: str,
    key: str,
    table: str,
    columns: Optional[str] = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = 100,
    order: Optional[str] = None,
) -> dict:
    """
    Select data from a Supabase table.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        table: Table name to query
        columns: Columns to select (default "*" for all). Can use Supabase syntax like "id,name,profile(email)"
        filters: Filter conditions as dict. Examples:
            - {"status": "active"} - equals
            - {"age": {"gt": 18}} - greater than
            - {"name": {"ilike": "%john%"}} - case-insensitive like
        limit: Maximum rows to return (default 100)
        order: Order by column, e.g., "created_at.desc"
    
    Returns:
        Query results with data array
    
    Example:
        supabase_select(
            url="https://xxx.supabase.co",
            key="...",
            table="users",
            columns="id,email,name",
            filters={"status": "active"},
            limit=10,
            order="created_at.desc"
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            query = client.from_(table).select(columns or "*")
            
            # Apply filters
            if filters:
                for col, condition in filters.items():
                    if isinstance(condition, dict):
                        for op, val in condition.items():
                            if op == "eq":
                                query = query.eq(col, val)
                            elif op == "neq":
                                query = query.neq(col, val)
                            elif op == "gt":
                                query = query.gt(col, val)
                            elif op == "gte":
                                query = query.gte(col, val)
                            elif op == "lt":
                                query = query.lt(col, val)
                            elif op == "lte":
                                query = query.lte(col, val)
                            elif op == "like":
                                query = query.like(col, val)
                            elif op == "ilike":
                                query = query.ilike(col, val)
                            elif op == "in":
                                query = query.in_(col, val)
                    else:
                        query = query.eq(col, condition)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Apply order
            if order:
                parts = order.split(".")
                col = parts[0]
                desc = len(parts) > 1 and parts[1].lower() == "desc"
                query = query.order(col, desc=desc)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    return _make_supabase_request(
        url, key, table,
        method="GET",
        select=columns,
        filters=filters,
        limit=limit,
        order=order,
    )


@mcp.tool()
def supabase_insert(
    url: str,
    key: str,
    table: str,
    data: Dict[str, Any],
) -> dict:
    """
    Insert a row into a Supabase table.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        table: Table name
        data: Row data as dictionary
    
    Returns:
        Inserted row(s) with generated IDs
    
    Example:
        supabase_insert(
            url="https://xxx.supabase.co",
            key="...",
            table="users",
            data={"email": "user@example.com", "name": "John Doe"}
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            result = client.from_(table).insert(data).execute()
            
            return {
                "success": True,
                "data": result.data,
                "message": f"Inserted {len(result.data)} row(s)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    result = _make_supabase_request(url, key, table, method="POST", data=data)
    if result.get("success"):
        result["message"] = "Row inserted successfully"
    return result


@mcp.tool()
def supabase_update(
    url: str,
    key: str,
    table: str,
    data: Dict[str, Any],
    filters: Dict[str, Any],
) -> dict:
    """
    Update rows in a Supabase table.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        table: Table name
        data: Fields to update
        filters: Filter conditions to identify rows to update
    
    Returns:
        Updated row(s)
    
    Example:
        supabase_update(
            url="https://xxx.supabase.co",
            key="...",
            table="users",
            data={"status": "inactive"},
            filters={"id": 123}
        )
    """
    if not filters:
        return {
            "success": False,
            "error": "Filters required for update operation to prevent accidental bulk updates",
        }
    
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            query = client.from_(table).update(data)
            
            # Apply filters
            for col, condition in filters.items():
                if isinstance(condition, dict):
                    for op, val in condition.items():
                        if op == "eq":
                            query = query.eq(col, val)
                        # Add more operators as needed
                else:
                    query = query.eq(col, condition)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data,
                "message": f"Updated {len(result.data)} row(s)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    result = _make_supabase_request(url, key, table, method="PATCH", data=data, filters=filters)
    if result.get("success"):
        result["message"] = "Rows updated successfully"
    return result


@mcp.tool()
def supabase_delete(
    url: str,
    key: str,
    table: str,
    filters: Dict[str, Any],
) -> dict:
    """
    Delete rows from a Supabase table.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        table: Table name
        filters: Filter conditions to identify rows to delete
    
    Returns:
        Deleted row(s)
    
    Example:
        supabase_delete(
            url="https://xxx.supabase.co",
            key="...",
            table="users",
            filters={"id": 123}
        )
    """
    if not filters:
        return {
            "success": False,
            "error": "Filters required for delete operation to prevent accidental bulk deletes",
        }
    
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            query = client.from_(table).delete()
            
            # Apply filters
            for col, condition in filters.items():
                if isinstance(condition, dict):
                    for op, val in condition.items():
                        if op == "eq":
                            query = query.eq(col, val)
                else:
                    query = query.eq(col, condition)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data,
                "message": f"Deleted {len(result.data)} row(s)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    result = _make_supabase_request(url, key, table, method="DELETE", filters=filters)
    if result.get("success"):
        result["message"] = "Rows deleted successfully"
    return result


@mcp.tool()
def supabase_upsert(
    url: str,
    key: str,
    table: str,
    data: Dict[str, Any],
    on_conflict: str = "id",
) -> dict:
    """
    Upsert (insert or update) a row in a Supabase table.
    
    If a row with the same value for the conflict column exists, it will be updated.
    Otherwise, a new row will be inserted.
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        table: Table name
        data: Row data
        on_conflict: Column to check for conflicts (default "id")
    
    Returns:
        Upserted row(s)
    
    Example:
        supabase_upsert(
            url="https://xxx.supabase.co",
            key="...",
            table="users",
            data={"id": 123, "email": "new@example.com"},
            on_conflict="id"
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            result = client.from_(table).upsert(data, on_conflict=on_conflict).execute()
            
            return {
                "success": True,
                "data": result.data,
                "message": f"Upserted {len(result.data)} row(s)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # REST API upsert requires Prefer header
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed"}
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": f"resolution=merge-duplicates,return=representation",
    }
    
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}?on_conflict={on_conflict}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, headers=headers, json=data)
            
            if response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            return {
                "success": True,
                "data": response.json() if response.text else [],
                "message": "Upsert successful",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def supabase_rpc(
    url: str,
    key: str,
    function_name: str,
    params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Call a Supabase RPC (stored procedure/function).
    
    Args:
        url: Supabase project URL
        key: Supabase API key
        function_name: Name of the database function to call
        params: Parameters to pass to the function
    
    Returns:
        Function result
    
    Example:
        supabase_rpc(
            url="https://xxx.supabase.co",
            key="...",
            function_name="get_user_stats",
            params={"user_id": 123}
        )
    """
    if HAS_SUPABASE:
        try:
            client = create_client(url, key)
            result = client.rpc(function_name, params or {}).execute()
            
            return {
                "success": True,
                "data": result.data,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Fallback to REST API
    if not HAS_HTTPX:
        return {"success": False, "error": "httpx not installed"}
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    
    endpoint = f"{url.rstrip('/')}/rest/v1/rpc/{function_name}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, headers=headers, json=params or {})
            
            if response.status_code >= 400:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            return {
                "success": True,
                "data": response.json() if response.text else None,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

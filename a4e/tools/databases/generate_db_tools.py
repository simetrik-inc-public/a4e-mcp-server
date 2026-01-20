"""
Generate boilerplate database tool code for an agent.
"""

from typing import Optional
from pathlib import Path

from ...core import mcp, get_project_dir


# Code templates for different database types
DB_TEMPLATES = {
    "supabase": '''"""
Database utilities for Supabase connection.

Credentials are automatically injected by the A4E platform:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_KEY: Your service role key
"""

from typing import Dict, Any, Optional
from supabase import create_client, Client


def get_supabase(params: Dict[str, Any]) -> Client:
    """
    Get Supabase client from injected credentials.
    
    Args:
        params: Tool parameters (db_connections is auto-injected)
    
    Returns:
        Supabase client instance
    
    Raises:
        ValueError: If credentials not configured
    """
    db_connections = params.get("db_connections", {})
    conn = db_connections.get("supabase", {})
    
    url = conn.get("url")
    key = conn.get("key")
    
    if not url or not key:
        raise ValueError(
            "Supabase credentials not configured. "
            "Add SUPABASE_URL and SUPABASE_KEY in the A4E Hub deployment settings."
        )
    
    return create_client(url, key)


# Example usage in your tools:
#
# def get_users(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Get all users from the database."""
#     supabase = get_supabase(params)
#     response = supabase.table("users").select("*").execute()
#     return {"users": response.data}
#
# def create_user(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Create a new user."""
#     supabase = get_supabase(params)
#     user_data = {
#         "name": params.get("name"),
#         "email": params.get("email"),
#     }
#     response = supabase.table("users").insert(user_data).execute()
#     return {"user": response.data[0] if response.data else None}
''',

    "postgres": '''"""
Database utilities for PostgreSQL connection.

Credentials are automatically injected by the A4E platform:
- DATABASE_URL: PostgreSQL connection string
"""

from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


_connection = None


def get_connection(params: Dict[str, Any]):
    """
    Get PostgreSQL connection from injected credentials.
    
    Uses connection pooling for efficiency.
    
    Args:
        params: Tool parameters (db_connections is auto-injected)
    
    Returns:
        psycopg2 connection
    
    Raises:
        ValueError: If credentials not configured
    """
    global _connection
    
    if _connection is not None:
        try:
            # Test if connection is still alive
            _connection.cursor().execute("SELECT 1")
            return _connection
        except:
            _connection = None
    
    db_connections = params.get("db_connections", {})
    conn = db_connections.get("postgres", {})
    
    url = conn.get("url")
    
    if not url:
        raise ValueError(
            "PostgreSQL credentials not configured. "
            "Add DATABASE_URL in the A4E Hub deployment settings."
        )
    
    _connection = psycopg2.connect(url)
    return _connection


def execute_query(params: Dict[str, Any], query: str, values: tuple = None) -> list:
    """
    Execute a query and return results as list of dicts.
    
    Args:
        params: Tool parameters
        query: SQL query string
        values: Query parameter values
    
    Returns:
        List of row dicts
    """
    conn = get_connection(params)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, values)
        if cur.description:
            return cur.fetchall()
        conn.commit()
        return []


# Example usage in your tools:
#
# def get_users(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Get all users from the database."""
#     users = execute_query(params, "SELECT * FROM users")
#     return {"users": users}
#
# def create_user(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Create a new user."""
#     query = "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING *"
#     result = execute_query(params, query, (params["name"], params["email"]))
#     return {"user": result[0] if result else None}
''',

    "mysql": '''"""
Database utilities for MySQL connection.

Credentials are automatically injected by the A4E platform:
- MYSQL_URL: MySQL connection string
"""

from typing import Dict, Any
import mysql.connector
from urllib.parse import urlparse


_connection = None


def get_connection(params: Dict[str, Any]):
    """
    Get MySQL connection from injected credentials.
    
    Args:
        params: Tool parameters (db_connections is auto-injected)
    
    Returns:
        MySQL connection
    
    Raises:
        ValueError: If credentials not configured
    """
    global _connection
    
    if _connection is not None and _connection.is_connected():
        return _connection
    
    db_connections = params.get("db_connections", {})
    conn = db_connections.get("mysql", {})
    
    url = conn.get("url")
    
    if not url:
        raise ValueError(
            "MySQL credentials not configured. "
            "Add MYSQL_URL in the A4E Hub deployment settings."
        )
    
    # Parse connection URL
    parsed = urlparse(url)
    
    _connection = mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
    )
    return _connection


def execute_query(params: Dict[str, Any], query: str, values: tuple = None) -> list:
    """Execute a query and return results."""
    conn = get_connection(params)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, values)
    
    if cursor.description:
        return cursor.fetchall()
    conn.commit()
    return []
''',

    "mongodb": '''"""
Database utilities for MongoDB connection.

Credentials are automatically injected by the A4E platform:
- MONGODB_URL: MongoDB connection string
"""

from typing import Dict, Any
from pymongo import MongoClient
from urllib.parse import urlparse


_client = None
_db = None


def get_database(params: Dict[str, Any]):
    """
    Get MongoDB database from injected credentials.
    
    Args:
        params: Tool parameters (db_connections is auto-injected)
    
    Returns:
        MongoDB database instance
    
    Raises:
        ValueError: If credentials not configured
    """
    global _client, _db
    
    if _db is not None:
        return _db
    
    db_connections = params.get("db_connections", {})
    conn = db_connections.get("mongodb", {})
    
    url = conn.get("url")
    
    if not url:
        raise ValueError(
            "MongoDB credentials not configured. "
            "Add MONGODB_URL in the A4E Hub deployment settings."
        )
    
    _client = MongoClient(url)
    
    # Extract database name from URL
    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/").split("?")[0] or "default"
    
    _db = _client[db_name]
    return _db


# Example usage in your tools:
#
# def get_users(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Get all users from the database."""
#     db = get_database(params)
#     users = list(db.users.find({}, {"_id": 0}))
#     return {"users": users}
#
# def create_user(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Create a new user."""
#     db = get_database(params)
#     result = db.users.insert_one({"name": params["name"], "email": params["email"]})
#     return {"user_id": str(result.inserted_id)}
''',

    "sqlite": '''"""
Database utilities for SQLite (runtime-created database).

This template creates a SQLite database at runtime in /tmp.
The database is created fresh on first access and can be seeded
with initial data.
"""

from typing import Dict, Any, Optional, List
import sqlite3
import os


# Database path - use /tmp for container compatibility
_DB_PATH = "/tmp/{agent_id}_data.db"
_connection = None


def get_connection() -> sqlite3.Connection:
    """Get database connection, creating tables if needed."""
    global _connection
    
    if _connection is not None:
        return _connection
    
    # Ensure database exists
    _init_db()
    
    _connection = sqlite3.connect(_DB_PATH)
    _connection.row_factory = sqlite3.Row
    return _connection


def _init_db():
    """Initialize database with required tables."""
    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()
    
    # TODO: Add your table definitions here
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def execute_query(query: str, params: tuple = None) -> List[dict]:
    """Execute a query and return results as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    if cursor.description:
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.commit()
    return []


# Example usage in your tools:
#
# def get_items(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Get all items."""
#     items = execute_query("SELECT * FROM items ORDER BY created_at DESC")
#     return {"items": items}
#
# def create_item(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Create a new item."""
#     execute_query(
#         "INSERT INTO items (name, description) VALUES (?, ?)",
#         (params["name"], params.get("description", ""))
#     )
#     return {"success": True}
''',
}


@mcp.tool()
def generate_db_tools(
    db_type: str,
    agent_name: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """
    Generate boilerplate database tool code for an agent.
    
    Creates a db.py file in the agent's tools directory with helper
    functions for connecting to the specified database type.
    
    Args:
        db_type: Type of database ("supabase", "postgres", "mysql", "mongodb", "sqlite")
        agent_name: Agent to generate for (uses current project if not specified)
        overwrite: If True, overwrite existing db.py file
    
    Returns:
        Generation status and file path
    """
    # Validate db_type
    if db_type not in DB_TEMPLATES:
        return {
            "success": False,
            "error": f"Unknown database type: {db_type}",
            "supported_types": list(DB_TEMPLATES.keys()),
        }
    
    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name
    
    # Ensure tools directory exists
    tools_dir = project_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if db.py already exists
    db_file = tools_dir / "db.py"
    if db_file.exists() and not overwrite:
        return {
            "success": False,
            "error": f"File already exists: {db_file}",
            "hint": "Use overwrite=True to replace the existing file",
        }
    
    # Generate code from template
    template = DB_TEMPLATES[db_type]
    
    # Replace placeholders
    code = template.replace("{agent_id}", agent_id)
    
    # Write file
    db_file.write_text(code)
    
    return {
        "success": True,
        "message": f"Generated {db_type} database tools for agent '{agent_id}'",
        "file_path": str(db_file),
        "db_type": db_type,
        "next_steps": [
            f"1. Review and customize the generated code at {db_file}",
            f"2. Add your database credentials in the A4E Hub deployment UI",
            f"3. Import and use the helpers in your other tools",
        ] if db_type != "sqlite" else [
            f"1. Review and customize the generated code at {db_file}",
            f"2. Update the table schemas in _init_db()",
            f"3. SQLite databases are created at runtime - no credentials needed",
        ],
    }

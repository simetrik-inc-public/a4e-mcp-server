"""
SQLite database validation tool.
Validates SQLite file structure and returns table info.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sqlite3
import os

from ...core import mcp, get_project_dir


@mcp.tool()
def validate_sqlite(
    file_path: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Validate a SQLite database file and return its structure.
    
    This tool inspects a SQLite database file and returns information about:
    - File validity and size
    - Tables and their schemas
    - Column types and row counts
    
    Args:
        file_path: Path to the SQLite file (.db, .sqlite, .sqlite3)
        agent_name: Agent to associate with (uses current project if not specified)
    
    Returns:
        Validation result with file info, tables, and schema details
    """
    # Resolve file path
    path = Path(file_path)
    if not path.is_absolute():
        project_dir = get_project_dir(agent_name)
        path = project_dir / file_path
    
    # Check file exists
    if not path.exists():
        return {
            "valid": False,
            "error": f"File not found: {path}",
            "filename": path.name,
        }
    
    # Check extension
    valid_extensions = {".db", ".sqlite", ".sqlite3"}
    if path.suffix.lower() not in valid_extensions:
        return {
            "valid": False,
            "error": f"Invalid file extension. Expected: {', '.join(valid_extensions)}",
            "filename": path.name,
        }
    
    # Get file size
    size_bytes = path.stat().st_size
    size_display = _format_size(size_bytes)
    
    # Try to open and validate the database
    tables: List[Dict[str, Any]] = []
    total_rows = 0
    
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        # Get info for each table
        for table_name in table_names:
            # Get columns
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = [
                {"name": col[1], "type": col[2] or "TEXT"}
                for col in cursor.fetchall()
            ]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
            })
        
        conn.close()
        
        return {
            "valid": True,
            "filename": path.name,
            "size_bytes": size_bytes,
            "size_display": size_display,
            "tables": tables,
            "total_tables": len(tables),
            "total_rows": total_rows,
            "path": str(path),
        }
        
    except sqlite3.DatabaseError as e:
        return {
            "valid": False,
            "error": f"Invalid SQLite database: {str(e)}",
            "filename": path.name,
            "size_bytes": size_bytes,
            "size_display": size_display,
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error reading database: {str(e)}",
            "filename": path.name,
        }


@mcp.tool()
def sqlite_query(
    file_path: str,
    query: str,
    params: Optional[List[Any]] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Execute a read-only SQL query on a SQLite database.
    
    Args:
        file_path: Path to the SQLite file
        query: SQL query to execute (SELECT only for safety)
        params: Optional list of query parameters for parameterized queries
        agent_name: Agent context
    
    Returns:
        Query results with columns and rows
    """
    # Resolve file path
    path = Path(file_path)
    if not path.is_absolute():
        project_dir = get_project_dir(agent_name)
        path = project_dir / file_path
    
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {path}",
        }
    
    # Safety check - only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return {
            "success": False,
            "error": "Only SELECT queries are allowed for safety. Use sqlite_execute for write operations.",
        }
    
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Fetch results
        rows = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"SQL error: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing query: {str(e)}",
        }


@mcp.tool()
def sqlite_execute(
    file_path: str,
    query: str,
    params: Optional[List[Any]] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Execute a write SQL query on a SQLite database (INSERT, UPDATE, DELETE).
    
    Args:
        file_path: Path to the SQLite file
        query: SQL query to execute
        params: Optional list of query parameters for parameterized queries
        agent_name: Agent context
    
    Returns:
        Execution result with affected rows
    """
    # Resolve file path
    path = Path(file_path)
    if not path.is_absolute():
        project_dir = get_project_dir(agent_name)
        path = project_dir / file_path
    
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {path}",
        }
    
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        affected_rows = cursor.rowcount
        last_id = cursor.lastrowid
        
        conn.close()
        
        return {
            "success": True,
            "affected_rows": affected_rows,
            "last_insert_id": last_id,
            "message": f"Query executed successfully. {affected_rows} row(s) affected.",
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"SQL error: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing query: {str(e)}",
        }


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

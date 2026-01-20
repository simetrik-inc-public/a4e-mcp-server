"""
Upload SQLite database tool for A4E agents.
"""

from typing import Optional
from pathlib import Path
import os

from ...core import mcp, get_project_dir


@mcp.tool()
def upload_database(
    database_path: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Upload a SQLite database file for an agent.
    
    The database will be stored in S3 and automatically downloaded
    when the agent runs. Changes made during execution are synced back.
    
    Args:
        database_path: Path to the SQLite database file to upload
        agent_name: Agent to upload for (uses current project if not specified)
    
    Returns:
        Upload status and instructions
    """
    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name
    
    # Resolve database path
    db_path = Path(database_path)
    if not db_path.is_absolute():
        db_path = project_dir / database_path
    
    # Validate file exists
    if not db_path.exists():
        return {
            "success": False,
            "error": f"Database file not found: {db_path}",
        }
    
    # Validate it's a SQLite file
    if not db_path.suffix.lower() in [".db", ".sqlite", ".sqlite3"]:
        return {
            "success": False,
            "error": "File must be a SQLite database (.db, .sqlite, .sqlite3)",
        }
    
    # Check SQLite header
    try:
        with open(db_path, "rb") as f:
            header = f.read(16)
            if not header.startswith(b"SQLite format 3"):
                return {
                    "success": False,
                    "error": "File is not a valid SQLite database",
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {e}",
        }
    
    # Get file size
    file_size = db_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    # Check size limit (50MB)
    if file_size > 50 * 1024 * 1024:
        return {
            "success": False,
            "error": f"Database too large ({file_size_mb:.1f}MB). Maximum size is 50MB.",
        }
    
    return {
        "success": True,
        "message": f"Database ready for upload: {db_path.name}",
        "agent_id": agent_id,
        "database": {
            "name": db_path.name,
            "path": str(db_path),
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
        },
        "next_steps": [
            "1. Deploy your agent to A4E Hub",
            "2. In the deployment UI, click 'Configure Database Connection'",
            "3. Upload your database file using the SQLite upload option",
            "4. Or use the API: POST /api/agents/{agent_id}/databases with the file",
        ],
        "note": (
            "Database files cannot be uploaded via MCP directly due to binary transfer limitations. "
            "Use the A4E Hub UI or API to upload the database after deploying your agent."
        ),
    }


@mcp.tool()
def check_database(
    database_path: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Check if a database file is valid and ready for upload.
    
    Args:
        database_path: Path to the SQLite database file
        agent_name: Agent context (uses current project if not specified)
    
    Returns:
        Validation results and database info
    """
    project_dir = get_project_dir(agent_name)
    
    # Resolve database path
    db_path = Path(database_path)
    if not db_path.is_absolute():
        db_path = project_dir / database_path
    
    if not db_path.exists():
        return {
            "valid": False,
            "error": f"File not found: {db_path}",
        }
    
    # Check extension
    if not db_path.suffix.lower() in [".db", ".sqlite", ".sqlite3"]:
        return {
            "valid": False,
            "error": "Not a SQLite file extension",
        }
    
    # Check SQLite header and get info
    try:
        import sqlite3
        
        with open(db_path, "rb") as f:
            header = f.read(16)
            if not header.startswith(b"SQLite format 3"):
                return {
                    "valid": False,
                    "error": "Invalid SQLite header",
                }
        
        # Connect and get table info
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts
        table_info = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info[table] = count
        
        conn.close()
        
        file_size = db_path.stat().st_size
        
        return {
            "valid": True,
            "database": {
                "name": db_path.name,
                "path": str(db_path),
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
            },
            "tables": table_info,
            "table_count": len(tables),
            "total_rows": sum(table_info.values()),
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error reading database: {e}",
        }

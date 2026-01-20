"""
Database sync tools for A4E agents.
"""

from typing import Optional

from ...core import mcp, get_project_dir


@mcp.tool()
def sync_database(
    db_name: str,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Request a database sync back to S3.
    
    This is informational - actual sync happens automatically after
    agent tool execution. Use this to understand the sync process.
    
    Args:
        db_name: Name of the database file (e.g., "fitness.db")
        agent_name: Agent context (uses current project if not specified)
    
    Returns:
        Sync information and status
    """
    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name
    
    return {
        "success": True,
        "message": f"Database sync info for '{db_name}'",
        "agent_id": agent_id,
        "sync_behavior": {
            "automatic": True,
            "trigger": "After each tool execution that modifies the database",
            "detection": "MD5 checksum comparison",
            "storage": f"S3: databases/{{user_id}}/{agent_id}/{db_name}",
        },
        "manual_sync": {
            "endpoint": f"POST /api/agents/{agent_id}/databases/{db_name}/sync",
            "description": "Force sync even if checksum unchanged",
        },
        "notes": [
            "Databases are automatically synced after tool execution",
            "Changes are detected using MD5 checksums",
            "Only modified databases are uploaded to save bandwidth",
            "Sync happens in the background - no action needed",
        ],
    }


@mcp.tool()
def list_databases(
    agent_name: Optional[str] = None,
) -> dict:
    """
    List all databases configured for an agent.
    
    Shows both SQLite databases (synced to S3) and external
    database connections.
    
    Args:
        agent_name: Agent to list databases for (uses current project if not specified)
    
    Returns:
        List of configured databases
    """
    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name
    
    # Check for db_config.json
    db_config_path = project_dir / "db_config.json"
    db_config = None
    
    if db_config_path.exists():
        import json
        try:
            db_config = json.loads(db_config_path.read_text())
        except:
            pass
    
    # Check for local .db files
    local_dbs = []
    data_dir = project_dir / "data"
    if data_dir.exists():
        for db_file in data_dir.glob("*.db"):
            local_dbs.append({
                "name": db_file.name,
                "path": str(db_file),
                "size_bytes": db_file.stat().st_size,
                "type": "sqlite_local",
            })
    
    return {
        "success": True,
        "agent_id": agent_id,
        "external_connection": db_config,
        "local_databases": local_dbs,
        "api_endpoint": f"GET /api/agents/{agent_id}/databases",
        "notes": [
            "Local databases in 'data/' are for development only",
            "For production, upload databases via the Hub UI or API",
            "External connections use secrets configured during deployment",
        ],
    }

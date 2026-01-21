"""
Configure database connection for an agent.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import json

from ...core import mcp, get_project_dir


# Standard database configurations
DB_CONFIGS = {
    "supabase": {
        "display_name": "Supabase",
        "required_secrets": ["SUPABASE_URL", "SUPABASE_KEY"],
        "optional_secrets": ["SUPABASE_DB_URL"],
        "description": "Supabase PostgreSQL database with realtime and auth",
        "supports_validation": True,
    },
    "sqlite": {
        "display_name": "SQLite",
        "required_secrets": [],
        "optional_secrets": ["SQLITE_PATH"],
        "description": "Local file-based SQLite database",
        "supports_validation": True,
        "local_file": True,
    },
    "postgres": {
        "display_name": "PostgreSQL",
        "required_secrets": ["DATABASE_URL"],
        "optional_secrets": [],
        "description": "Standard PostgreSQL database connection",
        "supports_validation": False,
    },
    "mysql": {
        "display_name": "MySQL",
        "required_secrets": ["MYSQL_URL"],
        "optional_secrets": [],
        "description": "MySQL/MariaDB database connection",
        "supports_validation": False,
    },
    "mongodb": {
        "display_name": "MongoDB",
        "required_secrets": ["MONGODB_URL"],
        "optional_secrets": [],
        "description": "MongoDB NoSQL database connection",
        "supports_validation": False,
    },
}


@mcp.tool()
def configure_db_connection(
    db_type: str,
    credentials: Optional[Dict[str, str]] = None,
    file_path: Optional[str] = None,
    agent_name: Optional[str] = None,
    validate: bool = True,
) -> dict:
    """
    Configure a database connection for an agent.
    
    This tool helps you set up database credentials that will be injected
    into your agent's tools at runtime. Credentials are stored securely
    and never committed to your code.
    
    Supported database types:
    - supabase: Cloud PostgreSQL with realtime and auth (requires SUPABASE_URL, SUPABASE_KEY)
    - sqlite: Local file-based database (uses file_path parameter)
    - postgres: Standard PostgreSQL (requires DATABASE_URL)
    - mysql: MySQL/MariaDB (requires MYSQL_URL)
    - mongodb: MongoDB NoSQL (requires MONGODB_URL)
    
    Args:
        db_type: Type of database ("supabase", "sqlite", "postgres", "mysql", "mongodb")
        credentials: Dict of credential name -> value (optional, for validation)
        file_path: For SQLite, the path to the database file
        agent_name: Agent to configure (uses current project if not specified)
        validate: Whether to validate the connection (default True)
    
    Returns:
        Configuration status and next steps
    
    Examples:
        # Configure Supabase
        configure_db_connection(
            db_type="supabase",
            credentials={"SUPABASE_URL": "https://xxx.supabase.co", "SUPABASE_KEY": "..."}
        )
        
        # Configure SQLite
        configure_db_connection(
            db_type="sqlite",
            file_path="data/mydb.sqlite"
        )
    """
    # Validate db_type
    if db_type not in DB_CONFIGS:
        return {
            "success": False,
            "error": f"Unknown database type: {db_type}",
            "supported_types": list(DB_CONFIGS.keys()),
        }
    
    config = DB_CONFIGS[db_type]
    project_dir = get_project_dir(agent_name)
    agent_id = project_dir.name
    
    # Create or update db_config.json in the project
    db_config_path = project_dir / "db_config.json"
    
    existing_config = {}
    if db_config_path.exists():
        try:
            existing_config = json.loads(db_config_path.read_text())
        except json.JSONDecodeError:
            pass
    
    # Update config
    existing_config["db_type"] = db_type
    existing_config["required_secrets"] = config["required_secrets"]
    existing_config["optional_secrets"] = config["optional_secrets"]
    
    # Handle SQLite specific configuration
    validation_result = None
    if db_type == "sqlite":
        if file_path:
            existing_config["sqlite_path"] = file_path
            # Validate SQLite file if requested
            if validate:
                from .validate_sqlite import validate_sqlite
                validation_result = validate_sqlite(file_path, agent_name)
        else:
            # Runtime creation mode - no file needed upfront
            existing_config["sqlite_mode"] = "runtime"
            validation_result = {
                "valid": True,
                "mode": "runtime",
                "note": "SQLite database will be created at runtime",
            }
    
    # Handle Supabase validation
    elif db_type == "supabase" and credentials and validate:
        url = credentials.get("SUPABASE_URL")
        key = credentials.get("SUPABASE_KEY")
        if url and key:
            from .supabase import supabase_validate
            validation_result = supabase_validate(url, key)
    
    # Validate other credentials if provided
    elif credentials:
        missing = []
        for secret in config["required_secrets"]:
            if secret not in credentials or not credentials[secret]:
                missing.append(secret)
        
        if missing:
            validation_result = {
                "valid": False,
                "missing_required": missing,
            }
        else:
            validation_result = {
                "valid": True,
                "configured_secrets": list(credentials.keys()),
            }
    
    # Save config
    db_config_path.write_text(json.dumps(existing_config, indent=2))
    
    # Build next steps based on db_type
    if db_type == "sqlite":
        next_steps = [
            "1. Your SQLite database is configured locally",
            "2. Use 'validate_sqlite' to inspect the database structure",
            "3. Use 'sqlite_query' and 'sqlite_execute' to interact with the database",
        ]
        usage_example = """
# In your agent's tools, access SQLite like this:

from .validate_sqlite import sqlite_query, sqlite_execute

def my_tool(params: dict) -> dict:
    # Read data
    result = sqlite_query("data/mydb.sqlite", "SELECT * FROM users WHERE active = ?", [True])
    
    # Write data
    sqlite_execute("data/mydb.sqlite", "INSERT INTO logs (message) VALUES (?)", ["Hello"])
    
    return result
"""
    elif db_type == "supabase":
        next_steps = [
            "1. Add SUPABASE_URL and SUPABASE_KEY in the A4E Hub deployment UI",
            "2. Use 'supabase_select', 'supabase_insert', etc. to interact with your database",
            "3. Use 'supabase_rpc' to call stored procedures",
        ]
        usage_example = """
# In your agent's tools, access Supabase like this:

from .supabase import supabase_select, supabase_insert

def my_tool(params: dict) -> dict:
    url = params.get("db_connections", {}).get("supabase", {}).get("url")
    key = params.get("db_connections", {}).get("supabase", {}).get("key")
    
    # Read data
    result = supabase_select(url, key, "users", filters={"status": "active"})
    
    # Insert data
    supabase_insert(url, key, "logs", {"message": "Hello", "timestamp": "now()"})
    
    return result
"""
    else:
        next_steps = [
            f"1. Add your credentials in the A4E Hub deployment UI",
            f"2. Or set them as environment variables: {', '.join(config['required_secrets'])}",
            f"3. Use 'generate_db_tools' to create boilerplate code for {db_type}",
        ]
        usage_example = f"""
# In your agent's tools, access the database like this:

def my_tool(params: dict) -> dict:
    db_connections = params.get("db_connections", {{}})
    {db_type}_conn = db_connections.get("{db_type}", {{}})
    
    # {db_type}_conn will contain your connection details
    ...
"""
    
    return {
        "success": True,
        "message": f"Database configuration updated for agent '{agent_id}'",
        "db_type": db_type,
        "db_config": {
            "display_name": config["display_name"],
            "description": config["description"],
            "required_secrets": config["required_secrets"],
        },
        "validation": validation_result,
        "config_file": str(db_config_path),
        "next_steps": next_steps,
        "usage_example": usage_example,
    }


@mcp.tool()
def list_db_types() -> dict:
    """
    List available database types and their configuration requirements.
    
    Returns:
        Dict of available database types with their requirements
    """
    return {
        "success": True,
        "database_types": {
            db_type: {
                "display_name": config["display_name"],
                "description": config["description"],
                "required_secrets": config["required_secrets"],
                "optional_secrets": config["optional_secrets"],
            }
            for db_type, config in DB_CONFIGS.items()
        },
    }

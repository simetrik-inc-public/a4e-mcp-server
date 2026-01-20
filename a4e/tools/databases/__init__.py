"""Database tools for A4E agents."""

from .configure_connection import configure_db_connection, list_db_types
from .generate_db_tools import generate_db_tools
from .upload_database import upload_database, check_database
from .sync_database import sync_database, list_databases
from .validate_sqlite import validate_sqlite, sqlite_query, sqlite_execute

# Supabase integration
from .supabase import (
    # Client
    supabase_connect,
    supabase_validate,
    supabase_list_tables,
    # Query
    supabase_select,
    supabase_insert,
    supabase_update,
    supabase_delete,
    supabase_upsert,
    supabase_rpc,
    # Auth
    supabase_get_user,
    supabase_list_users,
)

__all__ = [
    # Configuration
    "configure_db_connection",
    "list_db_types",
    "generate_db_tools",
    # Upload/Sync
    "upload_database",
    "check_database",
    "sync_database",
    "list_databases",
    # SQLite
    "validate_sqlite",
    "sqlite_query",
    "sqlite_execute",
    # Supabase Client
    "supabase_connect",
    "supabase_validate",
    "supabase_list_tables",
    # Supabase Query
    "supabase_select",
    "supabase_insert",
    "supabase_update",
    "supabase_delete",
    "supabase_upsert",
    "supabase_rpc",
    # Supabase Auth
    "supabase_get_user",
    "supabase_list_users",
]

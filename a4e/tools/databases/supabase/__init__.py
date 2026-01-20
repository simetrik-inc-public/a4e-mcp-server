"""
Supabase integration tools for A4E agents.

Provides full Supabase functionality including:
- Connection and validation
- CRUD operations (select, insert, update, delete)
- RPC function calls
- Auth helpers
"""

from .client import (
    supabase_connect,
    supabase_validate,
    supabase_list_tables,
)
from .query import (
    supabase_select,
    supabase_insert,
    supabase_update,
    supabase_delete,
    supabase_upsert,
    supabase_rpc,
)
from .auth import (
    supabase_get_user,
    supabase_list_users,
)

__all__ = [
    # Client
    "supabase_connect",
    "supabase_validate",
    "supabase_list_tables",
    # Query
    "supabase_select",
    "supabase_insert",
    "supabase_update",
    "supabase_delete",
    "supabase_upsert",
    "supabase_rpc",
    # Auth
    "supabase_get_user",
    "supabase_list_users",
]

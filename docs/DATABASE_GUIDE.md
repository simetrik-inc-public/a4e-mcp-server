# Database Integration Guide

This guide explains how to integrate databases with your A4E agents, including SQLite, Supabase, and other database types.

## Overview

A4E supports multiple database types:

| Database | Type | Best For |
|----------|------|----------|
| **SQLite** | Local file | Simple apps, local data, prototyping |
| **Supabase** | Cloud PostgreSQL | Production apps, auth, realtime |
| **PostgreSQL** | Cloud/Self-hosted | Enterprise apps, complex queries |
| **MySQL** | Cloud/Self-hosted | Legacy systems, WordPress |
| **MongoDB** | NoSQL | Document storage, flexible schemas |

## Quick Start

### SQLite (Local Database)

```python
# Configure SQLite
configure_db_connection(
    db_type="sqlite",
    file_path="data/myapp.sqlite"
)

# Validate the database
validate_sqlite("data/myapp.sqlite")

# Query data
result = sqlite_query(
    "data/myapp.sqlite",
    "SELECT * FROM users WHERE active = ?",
    [True]
)

# Insert/Update data
sqlite_execute(
    "data/myapp.sqlite",
    "INSERT INTO logs (message, timestamp) VALUES (?, datetime('now'))",
    ["User logged in"]
)
```

### Supabase (Cloud Database)

```python
# Configure Supabase
configure_db_connection(
    db_type="supabase",
    credentials={
        "SUPABASE_URL": "https://xxx.supabase.co",
        "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
)

# Validate connection
supabase_validate(
    url="https://xxx.supabase.co",
    key="your-api-key"
)

# Query data
result = supabase_select(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="users",
    columns="id,email,name",
    filters={"status": "active"},
    limit=10
)

# Insert data
supabase_insert(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="users",
    data={"email": "user@example.com", "name": "John Doe"}
)
```

---

## SQLite Integration

### Validating a SQLite Database

```python
result = validate_sqlite("data/myapp.sqlite")

# Returns:
{
    "valid": True,
    "filename": "myapp.sqlite",
    "size_bytes": 24576,
    "size_display": "24.0 KB",
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "email", "type": "TEXT"},
                {"name": "created_at", "type": "DATETIME"}
            ],
            "row_count": 150
        }
    ],
    "total_tables": 1,
    "total_rows": 150
}
```

### Querying Data

```python
# Simple query
result = sqlite_query(
    file_path="data/myapp.sqlite",
    query="SELECT * FROM users LIMIT 10"
)

# Parameterized query (recommended for safety)
result = sqlite_query(
    file_path="data/myapp.sqlite",
    query="SELECT * FROM users WHERE email = ? AND status = ?",
    params=["user@example.com", "active"]
)

# Returns:
{
    "success": True,
    "columns": ["id", "email", "status"],
    "rows": [
        {"id": 1, "email": "user@example.com", "status": "active"}
    ],
    "row_count": 1
}
```

### Writing Data

```python
# Insert
result = sqlite_execute(
    file_path="data/myapp.sqlite",
    query="INSERT INTO users (email, name) VALUES (?, ?)",
    params=["new@example.com", "New User"]
)

# Update
result = sqlite_execute(
    file_path="data/myapp.sqlite",
    query="UPDATE users SET status = ? WHERE id = ?",
    params=["inactive", 123]
)

# Delete
result = sqlite_execute(
    file_path="data/myapp.sqlite",
    query="DELETE FROM users WHERE id = ?",
    params=[123]
)

# Returns:
{
    "success": True,
    "affected_rows": 1,
    "last_insert_id": 456,
    "message": "Query executed successfully. 1 row(s) affected."
}
```

---

## Supabase Integration

### Connection Setup

```python
# Full connection with config saving
supabase_connect(
    url="https://xxx.supabase.co",
    key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    save_config=True  # Saves to db_config.json
)

# Just validate (no config saving)
supabase_validate(
    url="https://xxx.supabase.co",
    key="your-api-key"
)

# List available tables
supabase_list_tables(
    url="https://xxx.supabase.co",
    key="your-api-key"
)
```

### CRUD Operations

#### Select (Read)

```python
# Basic select
result = supabase_select(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    columns="id,name,price",
    limit=20
)

# With filters
result = supabase_select(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    filters={
        "category": "electronics",           # equals
        "price": {"lt": 100},               # less than
        "name": {"ilike": "%phone%"}        # case-insensitive like
    },
    order="price.desc",
    limit=10
)

# Available filter operators:
# eq, neq, gt, gte, lt, lte, like, ilike, in
```

#### Insert (Create)

```python
result = supabase_insert(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    data={
        "name": "New Product",
        "price": 29.99,
        "category": "electronics"
    }
)
```

#### Update

```python
result = supabase_update(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    data={"price": 24.99, "on_sale": True},
    filters={"id": 123}  # Required to prevent bulk updates
)
```

#### Delete

```python
result = supabase_delete(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    filters={"id": 123}  # Required to prevent bulk deletes
)
```

#### Upsert (Insert or Update)

```python
result = supabase_upsert(
    url="https://xxx.supabase.co",
    key="your-api-key",
    table="products",
    data={"id": 123, "name": "Updated Name", "price": 19.99},
    on_conflict="id"  # Column to check for conflicts
)
```

### RPC (Stored Procedures)

Call database functions:

```python
result = supabase_rpc(
    url="https://xxx.supabase.co",
    key="your-api-key",
    function_name="get_user_stats",
    params={"user_id": 123}
)
```

### Authentication Helpers

```python
# Get user from access token
user = supabase_get_user(
    url="https://xxx.supabase.co",
    key="your-api-key",
    access_token="user-jwt-token"
)

# List all users (requires service_role key)
users = supabase_list_users(
    url="https://xxx.supabase.co",
    service_role_key="your-service-role-key",
    page=1,
    per_page=50
)

# Create a new user (requires service_role key)
new_user = supabase_create_user(
    url="https://xxx.supabase.co",
    service_role_key="your-service-role-key",
    email="newuser@example.com",
    password="securepassword123",
    user_metadata={"name": "John Doe"}
)

# Delete a user (requires service_role key)
supabase_delete_user(
    url="https://xxx.supabase.co",
    service_role_key="your-service-role-key",
    user_id="550e8400-e29b-41d4-a716-446655440000"
)
```

---

## Using Databases in Agent Tools

### Example: User Profile Tool with Supabase

```python
# tools/get_user_profile.py

def get_user_profile(params: dict) -> dict:
    """Get user profile from database."""
    user_id = params.get("user_id")
    
    # Get Supabase credentials from injected db_connections
    db = params.get("db_connections", {}).get("supabase", {})
    url = db.get("url")
    key = db.get("key")
    
    if not url or not key:
        return {"error": "Database not configured"}
    
    # Import the Supabase tools
    from a4e.tools.databases.supabase import supabase_select
    
    result = supabase_select(
        url=url,
        key=key,
        table="profiles",
        columns="id,name,email,avatar_url,bio",
        filters={"user_id": user_id}
    )
    
    if not result.get("success"):
        return {"error": result.get("error")}
    
    profiles = result.get("data", [])
    if not profiles:
        return {"error": "Profile not found"}
    
    return {
        "success": True,
        "profile": profiles[0]
    }
```

### Example: Todo List Tool with SQLite

```python
# tools/todo_manager.py

def add_todo(params: dict) -> dict:
    """Add a new todo item."""
    text = params.get("text")
    
    from a4e.tools.databases.validate_sqlite import sqlite_execute
    
    result = sqlite_execute(
        file_path="data/todos.sqlite",
        query="INSERT INTO todos (text, completed, created_at) VALUES (?, 0, datetime('now'))",
        params=[text]
    )
    
    return {
        "success": result.get("success"),
        "todo_id": result.get("last_insert_id"),
        "message": f"Added todo: {text}"
    }


def list_todos(params: dict) -> dict:
    """List all todos."""
    show_completed = params.get("show_completed", False)
    
    from a4e.tools.databases.validate_sqlite import sqlite_query
    
    query = "SELECT * FROM todos"
    query_params = []
    
    if not show_completed:
        query += " WHERE completed = ?"
        query_params.append(0)
    
    query += " ORDER BY created_at DESC"
    
    result = sqlite_query(
        file_path="data/todos.sqlite",
        query=query,
        params=query_params if query_params else None
    )
    
    return {
        "success": True,
        "todos": result.get("rows", []),
        "count": result.get("row_count", 0)
    }
```

---

## Configuration Files

### db_config.json

When you configure a database, a `db_config.json` file is created in your agent directory:

```json
{
  "db_type": "supabase",
  "required_secrets": ["SUPABASE_URL", "SUPABASE_KEY"],
  "optional_secrets": ["SUPABASE_DB_URL"]
}
```

For SQLite:

```json
{
  "db_type": "sqlite",
  "sqlite_path": "data/myapp.sqlite",
  "required_secrets": [],
  "optional_secrets": ["SQLITE_PATH"]
}
```

---

## Best Practices

### Security

1. **Never commit credentials** - Use environment variables or the A4E Hub secrets manager
2. **Use parameterized queries** - Prevent SQL injection attacks
3. **Require filters for updates/deletes** - Prevent accidental bulk operations
4. **Use appropriate API keys** - anon key for client, service_role for admin operations

### Performance

1. **Limit query results** - Always use `limit` parameter
2. **Select specific columns** - Don't use `SELECT *` in production
3. **Use indexes** - Create indexes for frequently filtered columns
4. **Cache connections** - Supabase tools automatically cache connections

### Error Handling

```python
result = supabase_select(...)

if not result.get("success"):
    error = result.get("error", "Unknown error")
    # Handle error appropriately
    return {"error": error}

data = result.get("data", [])
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid API key" | Wrong Supabase key | Use service_role key for admin ops, anon key for client |
| "File not found" | Wrong SQLite path | Check file path is relative to agent directory |
| "Invalid SQLite database" | Corrupted file | Re-create or restore from backup |
| "Connection refused" | Network/firewall | Check Supabase project is active, network allows HTTPS |
| "Row-level security" | RLS blocking access | Use service_role key or configure RLS policies |

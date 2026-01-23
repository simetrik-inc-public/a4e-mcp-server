# A4E Database Integration Guide

Complete guide for integrating databases with A4E agents.

## Supported Databases

| Database | Type | Use Case |
|----------|------|----------|
| **SQLite** | Local file | Simple data, prototyping, offline |
| **Supabase** | PostgreSQL + Auth | Full-featured apps, realtime |
| **PostgreSQL** | Relational | Production workloads |
| **MySQL** | Relational | Legacy systems, WordPress |
| **MongoDB** | NoSQL | Document-based data |

---

## Quick Start

### 1. Configure Connection

```bash
# Using MCP tool
configure_db_connection(
  db_type="supabase",
  credentials={
    "url": "https://your-project.supabase.co",
    "key": "your-anon-key"
  }
)
```

### 2. Generate Tools

```bash
# Auto-generate CRUD tools
generate_db_tools(db_type="supabase")
```

### 3. Use in Agent

Tools are automatically available to your agent after generation.

---

## SQLite Integration

### Configuration

SQLite requires no credentials. Databases can be:
- Created at runtime in `/tmp/`
- Uploaded via S3
- Synced from remote storage

### MCP Tools

```python
# Validate database structure
validate_sqlite(file_path="data.db")

# Read-only queries
sqlite_query(
  file_path="data.db",
  query="SELECT * FROM users WHERE active = ?",
  params=[True]
)

# Write operations
sqlite_execute(
  file_path="data.db",
  statement="INSERT INTO users (name, email) VALUES (?, ?)",
  params=["John", "john@example.com"]
)
```

### Generated Code Template

```python
# tools/db.py (auto-generated)
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = Path("/tmp/agent_data.db")

def _get_db_path() -> Path:
    """Get database path, checking for platform injection."""
    if hasattr(__builtins__, 'database_paths'):
        return Path(database_paths.get('data.db', _DEFAULT_DB_PATH))
    return _DEFAULT_DB_PATH

def _init_db():
    """Initialize database schema."""
    conn = sqlite3.connect(_get_db_path())
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def get_db():
    """Get database connection with row factory."""
    _init_db()
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn
```

### Example Tool

```python
from a4e.tools import tool
from typing import List, Dict, Any

@tool
def list_items(limit: int = 100) -> List[Dict[str, Any]]:
    """List all items from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items LIMIT ?", [limit])
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
```

---

## Supabase Integration

### Configuration

```python
configure_db_connection(
  db_type="supabase",
  credentials={
    "url": "https://your-project.supabase.co",
    "key": "your-anon-key",  # or service_role key for admin
    "db_url": "postgresql://..."  # optional direct DB access
  }
)
```

### Environment Variables

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
```

### MCP Tools

**Connection & Validation:**
```python
supabase_connect(url, key)        # Initialize and save config
supabase_validate(url, key)       # Test without saving
supabase_list_tables()            # List all tables
```

**CRUD Operations:**
```python
# SELECT
supabase_select(
  table="users",
  columns="id, name, email",
  filters={"active": True},
  order_by="created_at",
  limit=10
)

# INSERT
supabase_insert(
  table="users",
  data={"name": "John", "email": "john@example.com"}
)

# UPDATE (requires filters for safety)
supabase_update(
  table="users",
  data={"active": False},
  filters={"id": 123}
)

# DELETE (requires filters for safety)
supabase_delete(
  table="users",
  filters={"id": 123}
)

# UPSERT
supabase_upsert(
  table="users",
  data={"id": 123, "name": "John Updated"},
  on_conflict="id"
)

# RPC (stored procedures)
supabase_rpc(
  function_name="get_user_stats",
  params={"user_id": 123}
)
```

**Auth Tools (requires service_role key):**
```python
supabase_get_user(jwt_token)      # Get user from token
supabase_list_users()             # List all users
supabase_create_user(email, password)
supabase_delete_user(user_id)
```

### Generated Code Template

```python
# tools/db.py (auto-generated)
from typing import Dict, Any, Optional
import httpx

class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def from_(self, table: str):
        return QueryBuilder(self, table)

class QueryBuilder:
    def __init__(self, client: SupabaseClient, table: str):
        self.client = client
        self.table = table
        self.params = {}

    def select(self, columns: str = "*"):
        self.params["select"] = columns
        return self

    def eq(self, column: str, value: Any):
        self.params[column] = f"eq.{value}"
        return self

    def limit(self, count: int):
        self.params["limit"] = count
        return self

    def execute(self):
        url = f"{self.client.url}/rest/v1/{self.table}"
        response = httpx.get(url, headers=self.client.headers, params=self.params)
        return response.json()

def get_supabase(params: Dict[str, Any]) -> SupabaseClient:
    """Get Supabase client from injected credentials."""
    db_connections = params.get("db_connections", {})
    conn = db_connections.get("supabase", {})
    return SupabaseClient(conn["url"], conn["key"])
```

### Example Tool

```python
from a4e.tools import tool
from typing import Dict, Any, List

@tool
def get_user_orders(params: Dict[str, Any], user_id: str) -> List[Dict]:
    """Get all orders for a user."""
    client = get_supabase(params)
    return (
        client.from_("orders")
        .select("id, total, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
```

---

## PostgreSQL Integration

### Configuration

```python
configure_db_connection(
  db_type="postgresql",
  credentials={
    "url": "postgresql://user:pass@host:5432/dbname"
  }
)
```

### Generated Code Template

```python
# tools/db.py (auto-generated)
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = None  # Injected at runtime

@contextmanager
def get_connection():
    """Get database connection with automatic cleanup."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = None) -> list:
    """Execute a query and return results as list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:
                return [dict(row) for row in cur.fetchall()]
            return []
```

---

## MySQL Integration

### Configuration

```python
configure_db_connection(
  db_type="mysql",
  credentials={
    "url": "mysql://user:pass@host:3306/dbname"
  }
)
```

### Generated Code Template

```python
# tools/db.py (auto-generated)
import mysql.connector
from urllib.parse import urlparse

MYSQL_URL = None  # Injected at runtime

def get_connection():
    """Parse URL and create MySQL connection."""
    parsed = urlparse(MYSQL_URL)
    return mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:]
    )

def execute_query(query: str, params: tuple = None) -> list:
    """Execute query and return results."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results
```

---

## MongoDB Integration

### Configuration

```python
configure_db_connection(
  db_type="mongodb",
  credentials={
    "url": "mongodb+srv://user:pass@cluster.mongodb.net/dbname"
  }
)
```

### Generated Code Template

```python
# tools/db.py (auto-generated)
from pymongo import MongoClient
from urllib.parse import urlparse

MONGODB_URL = None  # Injected at runtime

def get_database():
    """Get MongoDB database from connection string."""
    client = MongoClient(MONGODB_URL)
    parsed = urlparse(MONGODB_URL)
    db_name = parsed.path[1:] if parsed.path else "default"
    return client[db_name]

def find_documents(collection: str, query: dict = None, limit: int = 100):
    """Find documents in a collection."""
    db = get_database()
    return list(db[collection].find(query or {}).limit(limit))

def insert_document(collection: str, document: dict):
    """Insert a document into a collection."""
    db = get_database()
    result = db[collection].insert_one(document)
    return str(result.inserted_id)
```

---

## Credential Injection

A4E automatically injects database credentials into tool parameters at runtime.

### How It Works

1. **Configuration Saved:** `db_config.json` stores encrypted credentials
2. **Runtime Injection:** Platform wraps tools with `_wrap_tool_with_context()`
3. **Access in Tools:** Credentials available via `params.get("db_connections")`

### Tool Signature Convention

```python
from a4e.tools import tool
from typing import Dict, Any

@tool
def my_database_tool(params: Dict[str, Any], other_param: str) -> Dict:
    """
    Tool description.

    Auto-injected params:
    - db_connections: Database credentials
    - database_paths: Paths to synced SQLite files
    """
    # Access Supabase credentials
    supabase = params.get("db_connections", {}).get("supabase", {})
    url = supabase.get("url")
    key = supabase.get("key")

    # Access SQLite path
    db_paths = params.get("database_paths", {})
    sqlite_path = db_paths.get("data.db")

    # ... tool implementation
```

---

## S3 Synchronization

SQLite databases can be synced to/from S3 for persistence.

### Upload Database

```python
upload_database(
  file_path="local/data.db",
  destination="data.db"
)
```

**Limits:**
- Max file size: 50MB
- Must be valid SQLite file

### Automatic Sync

After tool execution that modifies SQLite:
1. Platform detects changes
2. Database synced to S3
3. Available for future sessions

### Access Synced Database

```python
def _get_db_path() -> Path:
    # Platform injects paths to synced databases
    if hasattr(__builtins__, 'database_paths'):
        return Path(database_paths['data.db'])
    return Path("/tmp/data.db")
```

---

## Security Best Practices

### Credential Management

- Never commit credentials to code
- Use environment variables or `db_config.json`
- Use anon key for client-side, service_role for admin

### Query Safety

```python
# GOOD: Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = ?", [user_id])

# BAD: String interpolation (SQL injection risk)
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### Filter Requirements

Supabase UPDATE and DELETE require filters to prevent accidental bulk operations:

```python
# This will fail (no filter)
supabase_delete(table="users", filters={})

# This works
supabase_delete(table="users", filters={"id": 123})
```

### Read-Only Access

For read-only tools, use `sqlite_query` instead of `sqlite_execute`:

```python
# Read-only (safe)
sqlite_query(file_path, "SELECT * FROM users")

# Write operations (use carefully)
sqlite_execute(file_path, "DELETE FROM users WHERE id = ?", [123])
```

---

## Example: Complete Agent with Database

### Structure

```
my-agent/
├── agent.py
├── metadata.json
├── prompts/agent.md
├── tools/
│   ├── schemas.json
│   ├── db.py           # Database connection code
│   ├── get_users.py    # Read tool
│   └── create_user.py  # Write tool
└── views/
    └── user-list/
        └── view.tsx
```

### db.py

```python
from typing import Dict, Any
import httpx

class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def select(self, table: str, columns: str = "*", filters: dict = None):
        url = f"{self.url}/rest/v1/{table}"
        params = {"select": columns}
        if filters:
            for k, v in filters.items():
                params[k] = f"eq.{v}"
        response = httpx.get(url, headers=self.headers, params=params)
        return response.json()

    def insert(self, table: str, data: dict):
        url = f"{self.url}/rest/v1/{table}"
        response = httpx.post(url, headers=self.headers, json=data)
        return response.json()

def get_client(params: Dict[str, Any]) -> SupabaseClient:
    conn = params.get("db_connections", {}).get("supabase", {})
    return SupabaseClient(conn["url"], conn["key"])
```

### get_users.py

```python
from a4e.tools import tool
from typing import Dict, Any, List
from .db import get_client

@tool
def get_users(params: Dict[str, Any], limit: int = 10) -> List[Dict]:
    """Get list of users from the database."""
    client = get_client(params)
    return client.select("users", "id, name, email", limit=limit)
```

### create_user.py

```python
from a4e.tools import tool
from typing import Dict, Any
from .db import get_client

@tool
def create_user(params: Dict[str, Any], name: str, email: str) -> Dict:
    """Create a new user in the database."""
    client = get_client(params)
    return client.insert("users", {"name": name, "email": email})
```

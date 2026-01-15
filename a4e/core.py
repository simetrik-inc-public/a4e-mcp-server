"""
Core module with shared utilities and MCP instance.
"""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from typing import Optional
import os
import re
from jinja2 import Environment, FileSystemLoader

# Global project directory (set by CLI args)
_PROJECT_DIR: Optional[Path] = None

# Initialize MCP server
mcp = FastMCP(name="a4e-agent-creator")

# Load templates
template_dir = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=False,  # Explicit for code generation
)


def set_project_dir(path: Path) -> None:
    """Set the global project directory."""
    global _PROJECT_DIR
    _PROJECT_DIR = path


def get_configured_project_dir() -> Optional[Path]:
    """Get the configured project directory."""
    return _PROJECT_DIR


def sanitize_input(value: str, allowed_chars: str = r"a-zA-Z0-9_-") -> str:
    """
    Sanitize user input to prevent template injection.

    Args:
        value: Input string to sanitize
        allowed_chars: Regex character class of allowed characters

    Returns:
        Sanitized string with only allowed characters
    """
    pattern = f"[^{allowed_chars}]"
    return re.sub(pattern, "", value)


def get_project_dir(agent_name: Optional[str] = None) -> Path:
    """
    Resolve the agent project directory.

    Priority (highest to lowest):
    1. --project-dir CLI arg (explicit override)
    2. A4E_WORKSPACE env var (set by editor via ${workspaceFolder})
    3. Path.cwd() (fallback)

    Note: Tools should prefer using explicit project_path parameter when available,
    as this function relies on environment context that may not be available
    in all MCP clients.

    Args:
        agent_name: Optional agent ID to resolve path for

    Returns:
        Path to agent directory or project root

    Raises:
        ValueError: If agent creation attempted in invalid location
    """
    global _PROJECT_DIR

    root = None
    workspace_env = os.environ.get("A4E_WORKSPACE", "")

    # Priority 1: Explicit CLI override
    if _PROJECT_DIR:
        root = _PROJECT_DIR
    # Priority 2: Workspace from editor (if properly expanded)
    elif workspace_env and "${" not in workspace_env:
        # Only use if the variable was expanded and path exists
        workspace_path = Path(workspace_env)
        if workspace_path.exists() and workspace_path.is_dir():
            root = workspace_path.resolve()
    
    # Priority 3: Fallback to cwd
    if root is None:
        root = Path.cwd()

    if not agent_name:
        return root

    # Agents live in file-store/agent-store
    agent_store = root / "file-store" / "agent-store"

    # Safety: Warn if creating in HOME directory
    if root == Path.home() and not agent_store.exists():
        raise ValueError(
            f"Cannot determine workspace directory.\n"
            f"\n"
            f"Please specify project_path in your tool call:\n"
            f'  initialize_project(name="{agent_name}", project_path="/path/to/your/project", ...)\n'
            f"\n"
            f"The agent will be created at: {{project_path}}/file-store/agent-store/{agent_name}/"
        )

    return agent_store / agent_name


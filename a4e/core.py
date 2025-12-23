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
    3. Path.cwd() (fallback for development)

    Args:
        agent_name: Optional agent ID to resolve path for

    Returns:
        Path to agent directory or project root

    Raises:
        ValueError: If agent creation attempted in invalid location
    """
    global _PROJECT_DIR

    # Priority 1: Explicit CLI override
    if _PROJECT_DIR:
        root = _PROJECT_DIR
    # Priority 2: Workspace from editor (portable solution)
    elif os.environ.get("A4E_WORKSPACE"):
        root = Path(os.environ["A4E_WORKSPACE"]).resolve()
    # Priority 3: Fallback to cwd
    else:
        root = Path.cwd()

    if not agent_name:
        return root

    # Agents live in file-store/agent-store
    agent_store = root / "file-store" / "agent-store"

    # Safety: Prevent creating in user HOME without agent-store
    if root == Path.home() and not agent_store.exists():
        raise ValueError(
            f"Cannot create agent in HOME directory ({root}).\n"
            f"Solution: Add to your MCP config:\n"
            f'  "env": {{"A4E_WORKSPACE": "${{workspaceFolder}}"}}'
        )

    return agent_store / agent_name


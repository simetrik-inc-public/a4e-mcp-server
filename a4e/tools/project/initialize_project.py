"""
Initialize project tool.
"""

from pathlib import Path
from typing import Literal, Optional
import os

from ...core import mcp, jinja_env, sanitize_input, get_project_dir, get_configured_project_dir


@mcp.tool()
def initialize_project(
    name: str,
    display_name: str,
    description: str,
    category: Literal[
        "Concierge",
        "E-commerce",
        "Fitness & Health",
        "Education",
        "Entertainment",
        "Productivity",
        "Finance",
        "Customer Support",
        "General",
    ],
    template: Literal["basic", "with-tools", "with-views", "full"] = "basic",
) -> dict:
    """
    Initialize a new A4E agent project

    Args:
        name: Agent ID (lowercase, hyphens, e.g., "nutrition-coach")
        display_name: Human-readable name (e.g., "Nutrition Coach")
        description: Short description of the agent
        category: Agent category for marketplace
        template: Project template (basic=files only, with-tools=example tool, with-views=example view, full=both)

    Returns:
        Project details with created files and next steps
    """
    # Validate name format
    if not name.replace("-", "").replace("_", "").isalnum():
        return {
            "success": False,
            "error": "Agent name must be alphanumeric with hyphens/underscores only",
        }

    # Use helper to determine path
    project_dir = get_project_dir(name)

    if project_dir.exists():
        return {"success": False, "error": f"Directory '{project_dir}' already exists"}

    try:
        # Ensure file-store/agent-store structure exists
        agent_store_root = project_dir.parent
        agent_store_root.mkdir(parents=True, exist_ok=True)

        # Create agent directory
        project_dir.mkdir(exist_ok=True)
        (project_dir / "prompts").mkdir(exist_ok=True)
        (project_dir / "tools").mkdir(exist_ok=True)
        (project_dir / "views").mkdir(exist_ok=True)
        (project_dir / "skills").mkdir(exist_ok=True)

        # Sanitize inputs before template rendering
        safe_name = sanitize_input(name)

        # Generate agent.py
        agent_template = jinja_env.get_template("agent.py.j2")
        agent_code = agent_template.render(agent_id=safe_name)
        (project_dir / "agent.py").write_text(agent_code)

        # Generate metadata.json
        metadata_template = jinja_env.get_template("metadata.json.j2")
        # Sanitize text inputs (allow spaces and common punctuation for display_name and description)
        safe_display_name = sanitize_input(display_name, r"a-zA-Z0-9 _-")
        safe_description = sanitize_input(description, r"a-zA-Z0-9 .,!?_-")
        metadata = metadata_template.render(
            agent_id=safe_name,
            display_name=safe_display_name,
            description=safe_description,
            category=category,
        )
        (project_dir / "metadata.json").write_text(metadata)

        # Generate prompts/agent.md
        prompt_template = jinja_env.get_template("prompt.md.j2")
        prompt = prompt_template.render(
            display_name=safe_display_name,
            category=category,
            description=safe_description,
        )
        (project_dir / "prompts/agent.md").write_text(prompt)
        (project_dir / "prompts/reviewer.md").write_text("")
        (project_dir / "prompts/view_renderer.md").write_text("")

        # Generate AGENTS.md (root context file)
        agents_template = jinja_env.get_template("agents.md.j2")
        agents_md = agents_template.render(
            agent_id=safe_name,
            display_name=safe_display_name,
            category=category,
            description=safe_description,
        )
        (project_dir / "AGENTS.md").write_text(agents_md)

        # Generate subdirectory AGENTS.md files for AI coding agents
        tools_agents_template = jinja_env.get_template("tools/agent.md.j2")
        (project_dir / "tools" / "AGENTS.md").write_text(tools_agents_template.render())

        views_agents_template = jinja_env.get_template("views/agent.md.j2")
        (project_dir / "views" / "AGENTS.md").write_text(views_agents_template.render())

        prompts_agents_template = jinja_env.get_template("prompts/agent.md.j2")
        (project_dir / "prompts" / "AGENTS.md").write_text(prompts_agents_template.render())

        # Generate skills/AGENTS.md (skills documentation)
        skills_agents_template = jinja_env.get_template("skills/agents.md.j2")
        skills_agents_md = skills_agents_template.render(agent_id=safe_name)
        (project_dir / "skills/AGENTS.md").write_text(skills_agents_md)

        # Create welcome view (MANDATORY)
        from ..views.helpers import create_view
        create_view(
            view_id="welcome",
            description="Welcome view for the agent",
            props={"title": {"type": "string", "description": "Welcome title"}},
            project_dir=project_dir,
        )

        # Create example content based on template
        if template in ["with-tools", "full"]:
            # Create example tool
            example_tool_code = '''from a4e.sdk import tool
from typing import Optional, Any

@tool
def example_tool(
    query: str,
    max_results: Optional[int] = 10
) -> dict:
    """
    Example tool that demonstrates basic functionality
    
    Args:
        query: Search query or input text
        max_results: Maximum number of results to return
    """
    # TODO: Implement your tool logic here
    return {
        "status": "success",
        "message": f"Processed query: {query}",
        "results": []
    }
'''
            (project_dir / "tools" / "example_tool.py").write_text(example_tool_code)

        if template in ["with-views", "full"]:
            # Create example view (in addition to welcome)
            create_view(
                view_id="example_view",
                description="Example view demonstrating props usage",
                props={
                    "title": {"type": "string", "description": "View title"},
                    "count": {"type": "number", "description": "Count value"},
                },
                project_dir=project_dir,
            )

        # Create welcome skill (connects welcome view)
        from ..skills.helpers import create_skill
        create_skill(
            skill_id="show_welcome",
            name="Show Welcome",
            description="Display the welcome screen. Use when user wants to go home or start over.",
            intent_triggers=["start over", "go home", "main menu", "welcome", "inicio", "volver al inicio"],
            output_view="welcome",
            internal_tools=[],
            requires_auth=False,
            view_props={"title": {"type": "string", "description": "Welcome title"}},
            project_dir=project_dir,
        )

        # Auto-generate schemas after project initialization
        from ..schemas import generate_schemas
        generate_schemas(force=False, agent_name=name)

        _PROJECT_DIR = get_configured_project_dir()
        return {
            "success": True,
            "message": f"Initialized agent '{name}'",
            "path": str(project_dir),
            "diagnostic": {
                "workspace_env": os.environ.get("A4E_WORKSPACE"),
                "project_dir_flag": str(_PROJECT_DIR) if _PROJECT_DIR else None,
                "detected_root": str(get_project_dir()),
                "cwd": str(Path.cwd()),
            },
            "next_steps": [
                f"Add tools: add_tool(..., agent_name='{name}')",
                f"Add views: add_view(..., agent_name='{name}')",
                f"Add skills: add_skill(..., agent_name='{name}')",
                "Start dev server using 'dev_start'",
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

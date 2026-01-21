"""
Add view tool.
"""

from typing import Optional, List

from ...core import mcp, get_project_dir
from .helpers import create_view, update_dependencies, get_view_responsive_tips


@mcp.tool()
def add_view(
    view_id: str,
    description: str,
    props: dict,
    mobile_optimized: bool = False,
    dependencies: Optional[List[str]] = None,
    agent_name: Optional[str] = None,
) -> dict:
    """
    Add a new React view to an agent.
    
    Creates a view directory with view.tsx and view.schema.json files.
    The view is automatically responsive and includes an isMobile prop.
    
    Args:
        view_id: ID of the view (snake_case, e.g., "meal_plan", "user_profile")
        description: Short description of the view's purpose
        props: Dictionary of props with types. Can be simple or detailed:
            - Simple: {"title": "string", "count": "number"}
            - Detailed: {"title": {"type": "string", "description": "Page title", "required": true}}
        mobile_optimized: If True, creates an enhanced mobile-first template with:
            - Touch-friendly interactions
            - Mobile bottom action bar
            - Responsive grid layouts
            - Safe area insets for iOS
        dependencies: Optional list of npm packages this view uses (e.g., ["recharts", "date-fns"])
        agent_name: Optional agent ID if not running from agent directory
    
    Returns:
        Result with created files and tips
    
    Examples:
        # Basic view
        add_view(
            view_id="user_profile",
            description="Display user profile information",
            props={"name": "string", "email": "string", "avatar_url": "string"}
        )
        
        # Mobile-optimized view with detailed props
        add_view(
            view_id="product_list",
            description="Display product catalog",
            props={
                "products": {"type": "array", "description": "List of products"},
                "category": {"type": "string", "required": false}
            },
            mobile_optimized=True
        )
        
        # View with dependencies
        add_view(
            view_id="analytics_chart",
            description="Display analytics charts",
            props={"data": "array"},
            dependencies=["recharts", "date-fns"]
        )
    """
    # Validate view ID
    if not view_id.replace("_", "").isalnum():
        return {
            "success": False,
            "error": "View ID must be alphanumeric with underscores (snake_case)",
            "example": "user_profile, meal_plan, product_list",
        }

    project_dir = get_project_dir(agent_name)
    result = create_view(
        view_id=view_id, 
        description=description, 
        props=props, 
        project_dir=project_dir,
        mobile_optimized=mobile_optimized,
    )

    # Update dependencies if provided
    if result.get("success") and dependencies:
        deps_result = update_dependencies(dependencies, project_dir)
        if deps_result.get("success"):
            result["dependencies_added"] = deps_result.get("added", [])

    # Auto-generate schemas after adding view
    if result.get("success"):
        from ..schemas import generate_schemas
        generate_schemas(force=False, agent_name=agent_name)

    return result


@mcp.tool()
def get_mobile_view_tips() -> dict:
    """
    Get tips for creating mobile-responsive views.
    
    Returns best practices for making views work well on mobile devices.
    
    Returns:
        List of tips with examples
    """
    return {
        "success": True,
        "tips": get_view_responsive_tips(),
        "note": "Set mobile_optimized=True when creating views for the best mobile experience",
    }

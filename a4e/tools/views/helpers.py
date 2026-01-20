"""
Helper functions for view management.
"""

import json
from pathlib import Path
from typing import Optional

from ...core import jinja_env


# Mobile-optimized view template with enhanced responsive design
MOBILE_VIEW_TEMPLATE = '''"use client";
import React from "react";

interface {view_name}Props {{
  /** Whether the view is being displayed on a mobile device */
  isMobile?: boolean;
{props_interface}
}}

/**
 * {description}
 * 
 * This view is mobile-optimized with responsive layouts and touch-friendly interactions.
 */
export default function {view_name}View({{ 
  isMobile = false,
{props_destructure}
}}: {view_name}Props) {{
  return (
    <div 
      className={{`
        w-full min-h-full
        p-4 md:p-6 lg:p-8
        bg-gradient-to-b from-gray-950 to-black
        ${{isMobile ? 'touch-pan-y touch-pan-x pb-20' : ''}}
      `}}
    >
      {{/* Header */}}
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-white">
          {description}
        </h1>
      </div>

      {{/* Main Content - Responsive Grid */}}
      <div className={{`
        grid gap-4 md:gap-6
        ${{isMobile ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'}}
      `}}>
        {{/* Add your content cards here */}}
      </div>

      {{/* Mobile Bottom Action Bar */}}
      {{isMobile && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-white/10 p-4 safe-area-inset-bottom">
          <div className="flex gap-3 justify-center">
            {{/* Add mobile action buttons here */}}
          </div>
        </div>
      )}}
    </div>
  );
}}
'''


def create_view(
    view_id: str, 
    description: str, 
    props: dict, 
    project_dir: Path,
    mobile_optimized: bool = False,
) -> dict:
    """
    Helper to create a view directory with view.tsx and view.schema.json files.

    Args:
        view_id: ID of the view (snake_case)
        description: View purpose
        props: Dictionary of props with types (e.g., {"title": "string", "count": "number"})
        project_dir: Path to the agent project directory
        mobile_optimized: If True, creates an enhanced mobile-responsive view template

    Returns:
        Result dictionary with success status
    """
    views_dir = project_dir / "views"

    if not views_dir.exists():
        return {
            "success": False,
            "error": f"views/ directory not found at {views_dir}",
        }

    view_dir = views_dir / view_id
    if view_dir.exists():
        return {"success": False, "error": f"View '{view_id}' already exists"}

    try:
        view_dir.mkdir()

        # Convert snake_case to PascalCase for component name
        view_name = "".join(word.title() for word in view_id.split("_"))

        # Build props for templates
        props_with_mobile = {"isMobile": {"type": "boolean", "required": False, "description": "Whether running on mobile"}}
        props_with_mobile.update(props)

        if mobile_optimized:
            # Use enhanced mobile template
            code = _create_mobile_view(view_name, description, props)
        else:
            # Use standard template
            template = jinja_env.get_template("view.tsx.j2")
            code = template.render(
                view_name=view_name, description=description, props=props
            )
        
        (view_dir / "view.tsx").write_text(code)

        # Create view.schema.json (required by A4E View Renderer)
        schema_properties = {
            "isMobile": {
                "type": "boolean",
                "description": "Whether the view is displayed on a mobile device",
            }
        }
        required_props = []
        
        for prop_name, prop_type in props.items():
            # Handle both simple types ("string") and detailed types ({"type": "string", "description": "..."})
            if isinstance(prop_type, dict):
                schema_properties[prop_name] = {
                    "type": prop_type.get("type", "string"),
                    "description": prop_type.get("description", f"The {prop_name} prop"),
                }
                if prop_type.get("required", True):
                    required_props.append(prop_name)
            else:
                schema_properties[prop_name] = {
                    "type": prop_type,
                    "description": f"The {prop_name} prop",
                }
                required_props.append(prop_name)

        view_schema = {
            "name": view_id,
            "description": description,
            "mobile_optimized": mobile_optimized,
            "props": {
                "type": "object",
                "properties": schema_properties,
                "required": required_props,
            },
        }
        (view_dir / "view.schema.json").write_text(
            json.dumps(view_schema, indent=2)
        )

        return {
            "success": True,
            "message": f"Created {'mobile-optimized ' if mobile_optimized else ''}view '{view_id}'",
            "path": str(view_dir),
            "files": ["view.tsx", "view.schema.json"],
            "mobile_optimized": mobile_optimized,
            "tips": [
                "The view includes an isMobile prop that's automatically passed by the A4E Hub",
                "Use responsive Tailwind classes (sm:, md:, lg:, xl:) for different screen sizes",
                "Add touch-pan-y class for better mobile scrolling",
            ] if mobile_optimized else [],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _create_mobile_view(view_name: str, description: str, props: dict) -> str:
    """Create a mobile-optimized view template."""
    # Build interface props
    props_interface = []
    props_destructure = []
    
    for prop_name, prop_type in props.items():
        if isinstance(prop_type, dict):
            ts_type = prop_type.get("type", "any")
            required = prop_type.get("required", True)
            desc = prop_type.get("description", "")
        else:
            ts_type = prop_type
            required = True
            desc = f"The {prop_name} prop"
        
        # Add JSDoc comment and interface line
        if desc:
            props_interface.append(f"  /** {desc} */")
        props_interface.append(f"  {prop_name}{'?' if not required else ''}: {ts_type};")
        props_destructure.append(f"  {prop_name},")
    
    return MOBILE_VIEW_TEMPLATE.format(
        view_name=view_name,
        description=description,
        props_interface="\n".join(props_interface),
        props_destructure="\n".join(props_destructure),
    )


def get_view_responsive_tips() -> list:
    """Get tips for making views responsive and mobile-friendly."""
    return [
        {
            "tip": "Use the isMobile prop",
            "description": "The A4E Hub automatically passes isMobile=true on mobile devices",
            "example": "className={`p-4 ${isMobile ? 'pb-20' : 'p-6'}`}",
        },
        {
            "tip": "Responsive grid layouts",
            "description": "Use Tailwind's responsive grid classes",
            "example": "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        },
        {
            "tip": "Touch-friendly interactions",
            "description": "Add touch classes for better mobile scrolling",
            "example": "className='touch-pan-y touch-pan-x'",
        },
        {
            "tip": "Mobile bottom bar",
            "description": "Reserve space for fixed bottom navigation on mobile",
            "example": "className={`${isMobile ? 'pb-20' : ''}`}",
        },
        {
            "tip": "Responsive text sizes",
            "description": "Scale text for different screen sizes",
            "example": "text-xl md:text-2xl lg:text-3xl",
        },
        {
            "tip": "Safe area insets",
            "description": "Handle notches and home indicators on iOS",
            "example": "className='safe-area-inset-bottom'",
        },
    ]

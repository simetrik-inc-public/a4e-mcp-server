# View System Guide

This document explains how views work in the A4E agent framework, including the critical `#VIEW` and `#PARAMS` system for production.

## Overview

Views are React components that render your agent's responses. The framework supports two modes:

| Mode | How Views are Selected | Use Case |
|------|------------------------|----------|
| **Development** | Skill matching via `intent_triggers` | Local testing with dev_runner |
| **Production** | LLM outputs `#VIEW:` tags | A4E playground and production |

## Production View System

In production, the LLM parses `#VIEW:` and `#PARAMS:` tags from the agent's text response to determine which view to show.

### Response Format

Every agent response MUST end with:

```
#VIEW: <view_id>
#PARAMS: {"key": "value"}
```

### Example Agent Response

When user says "Show me beachfront properties":

```
Here are our beautiful beachfront properties!

#VIEW: category_browse
#PARAMS: {"category": "beachfront"}
```

## Complete Skill + View Example

### 1. Define the Skill (`skills/schemas.json`)

```json
{
  "browse_category": {
    "id": "browse_category",
    "name": "Browse by Category",
    "description": "Browse properties filtered by a specific category",
    "intent_triggers": [
      "beachfront",
      "mountain",
      "lakefront",
      "show me beachfront",
      "show me mountain",
      "browse category"
    ],
    "requires_auth": false,
    "internal_tools": [
      "search_properties"
    ],
    "output": {
      "view": "category_browse"
    }
  }
}
```

### 2. Define the View (`views/schemas.json`)

```json
{
  "category_browse": {
    "id": "category_browse",
    "description": "Browse properties by category with filtering and sorting",
    "params": {
      "categories": {
        "type": "array",
        "description": "List of available categories with counts"
      },
      "activeCategory": {
        "type": "string",
        "description": "Currently selected category ID"
      },
      "properties": {
        "type": "array",
        "description": "List of properties in the selected category"
      },
      "totalResults": {
        "type": "number",
        "description": "Total number of properties in category"
      }
    }
  }
}
```

### 3. Create the View Component (`views/category_browse/view.tsx`)

```tsx
"use client";
import React from "react";

interface Property {
  id: string;
  name: string;
  location: { city: string; state: string };
  price: number;
  rating: number;
  images: string[];
  category: string;
}

interface Category {
  id: string;
  name: string;
  icon: string;
  count: number;
}

interface CategoryBrowseProps {
  categories: Category[];
  activeCategory: string;
  properties: Property[];
  totalResults: number;
}

export default function CategoryBrowseView({
  categories,
  activeCategory,
  properties,
  totalResults,
}: CategoryBrowseProps) {
  return (
    <div className="p-6">
      {/* Category Pills */}
      <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`px-4 py-2 rounded-full whitespace-nowrap ${
              cat.id === activeCategory
                ? "bg-rose-500 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {cat.icon} {cat.name}
          </button>
        ))}
      </div>

      {/* Results Header */}
      <h2 className="text-xl font-semibold mb-4">
        {totalResults} {activeCategory} properties
      </h2>

      {/* Property Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {properties.map((property) => (
          <div
            key={property.id}
            className="rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-shadow"
          >
            <div className="aspect-square relative">
              <img
                src={property.images[0]}
                alt={property.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-4">
              <div className="flex justify-between items-start">
                <h3 className="font-medium truncate">{property.name}</h3>
                <span className="flex items-center text-sm">
                  ★ {property.rating}
                </span>
              </div>
              <p className="text-gray-500 text-sm">
                {property.location.city}, {property.location.state}
              </p>
              <p className="mt-2">
                <span className="font-semibold">${property.price}</span>
                <span className="text-gray-500"> / night</span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 4. Configure the Agent Prompt (`prompts/agent.md`)

```markdown
# Travel Assistant

You are a Travel Assistant for vacation rentals.

## CRITICAL: Using Views

**You MUST call the `render_view` tool to display views to the user.**

When to call render_view:
- User says "hello", "hi", "start" → Call `render_view(view_id="welcome")`
- User wants to browse properties → Call `render_view(view_id="property_grid")`
- User asks for a category (beachfront, mountain, etc.) → Call `render_view(view_id="category_browse", category="<category>")`

## Response Format

ALWAYS end your responses with:
```
#VIEW: <view_id>
#PARAMS: {"key": "value"}
```

## View Selection Guide

| User Intent | #VIEW Value | #PARAMS |
|------------|-------------|---------|
| hello, hi, start | welcome | {} |
| hotels, properties, search | property_grid | {} |
| beachfront | category_browse | {"category": "beachfront"} |
| lakefront | category_browse | {"category": "lakefront"} |
| mountain | category_browse | {"category": "mountain"} |

## Examples

### User: "Show me beachfront properties"
Response:
```
Here are our beachfront properties!

#VIEW: category_browse
#PARAMS: {"category": "beachfront"}
```

### User: "Show me hotels"
Response:
```
Here are the available properties!

#VIEW: property_grid
#PARAMS: {}
```
```

## render_view Tool (Optional)

For agents that need more control, add a `render_view` tool:

### Tool Schema (`tools/schemas.json`)

```json
{
  "render_view": {
    "name": "render_view",
    "description": "Render a view to display in the chat interface. Call this tool whenever you need to show a view to the user.",
    "parameters": {
      "type": "object",
      "properties": {
        "view_id": {
          "type": "string",
          "description": "The view to render: 'welcome', 'property_grid', 'category_browse', 'property_detail', 'booking_summary', 'favorites_list'"
        },
        "category": {
          "type": "string",
          "description": "For category_browse, the category to filter (e.g., 'beachfront', 'mountain')"
        },
        "location": {
          "type": "string",
          "description": "For property_grid, the search location (e.g., 'Malibu')"
        }
      },
      "required": ["view_id"]
    }
  }
}
```

### Tool Implementation (`tools/render_view.py`)

```python
from typing import Optional

def render_view(
    view_id: str,
    category: Optional[str] = None,
    location: Optional[str] = None,
) -> dict:
    """Render a view to display in the chat interface."""

    # Sample data - replace with actual data fetching
    sample_properties = [
        {
            "id": "prop_001",
            "name": "Oceanfront Villa",
            "location": {"city": "Malibu", "state": "California"},
            "price": 450,
            "rating": 4.97,
            "images": ["https://images.unsplash.com/..."],
            "category": "beachfront"
        }
    ]

    if view_id == "category_browse":
        active_cat = category or "beachfront"
        filtered = [p for p in sample_properties if p["category"] == active_cat]

        return {
            "status": "success",
            "action": "render_view",
            "view": {
                "type": "view",
                "id": "category_browse",
                "params": {
                    "categories": [
                        {"id": "beachfront", "name": "Beachfront", "icon": "🏖️", "count": 45},
                        {"id": "mountain", "name": "Mountain", "icon": "🏔️", "count": 32},
                    ],
                    "activeCategory": active_cat,
                    "properties": filtered,
                    "totalResults": len(filtered)
                }
            }
        }

    # Handle other views...
    return {"status": "error", "message": f"Unknown view: {view_id}"}
```

## Testing Views

### Development Mode

```bash
python -m a4e.dev_runner --agent-path file-store/agent-store/my-agent --port 5001
```

In dev mode, the `dev_runner.py` matches skills based on `intent_triggers` and renders the corresponding view.

### Production Mode (Playground)

1. Start dev server with ngrok:
   ```bash
   ngrok http 5001
   ```

2. Open playground:
   ```
   https://dev-a4e.global.simetrik.com/builder/playground?url=<ngrok-url>&agent=<agent-name>
   ```

3. Test by typing trigger phrases and verifying views change

### Debugging View Issues

If views aren't changing in production:

1. **Check console logs** for `[StreamClient] View is NONE or empty`
2. **Verify prompt** includes `#VIEW` and `#PARAMS` format
3. **Check view IDs** match between prompt, schemas, and view folders
4. **Test locally** with dev_runner first

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| View shows NONE | LLM not outputting #VIEW tag | Update agent prompt with explicit examples |
| View ID mismatch | Schema says `travel_welcome` but prompt says `welcome` | Add alias in views/schemas.json |
| Params not passed | #PARAMS format incorrect | Use exact JSON format: `{"key": "value"}` |
| CORS errors | ngrok or server config | Ensure CORS middleware allows all origins |

## Best Practices

1. **Keep prompts simple** - Use clear, explicit examples for each view
2. **Use consistent view IDs** - Match IDs across prompt, schemas, and folders
3. **Test incrementally** - Verify each view works before adding more
4. **Add aliases** - Support both short (`welcome`) and full (`travel_welcome`) IDs
5. **Log view selection** - Add console logs to debug production issues

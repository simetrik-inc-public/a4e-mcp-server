# Agent Structure Reference

Complete templates and examples for A4E agent components.

## Directory Structure

```
{agent_id}/
├── agent.py                 # Entry point
├── metadata.json           # Agent configuration
├── model_config.yaml       # LLM settings
├── prompts/
│   ├── agent.md           # System prompt
│   └── orchestrator.md    # Optional orchestrator prompt
├── views/
│   ├── schemas.json       # Combined view schemas
│   └── {view_name}/
│       ├── view.tsx       # React component
│       └── view.schema.json
├── tools/
│   ├── schemas.json       # Combined tool schemas
│   └── {tool_name}.py     # Tool implementations
└── skills/
    ├── schemas.json       # Skill registry
    └── {skill_id}/
        └── SKILL.md
```

---

## Core Files

### agent.py

Entry point that creates the agent instance.

```python
from autogen import AssistantAgent
from a4e.agent_factory import AgentFactory

def create_agent(
    agent_id: str,
    llm_config: dict,
    include_agents: list[str] = None
) -> AssistantAgent:
    """Create and return the agent instance."""

    factory = AgentFactory(
        agent_id=agent_id,
        llm_config=llm_config
    )

    return factory.create(
        include_agents=include_agents or []
    )
```

### metadata.json

Agent identity and configuration.

```json
{
  "id": "weather-assistant",
  "name": "Weather Assistant",
  "description": "Provides weather forecasts, alerts, and climate information",
  "version": "1.0.0",
  "avatar": "https://example.com/weather-avatar.png",
  "capabilities": {
    "chat": true,
    "tools": true,
    "views": true,
    "handover": false,
    "payment": false
  },
  "settings": {
    "useOrchestrator": false,
    "maxTurns": 10,
    "temperature": 0.7
  },
  "tags": ["weather", "forecast", "utility"],
  "author": "A4E Team",
  "created": "2024-01-15T00:00:00Z",
  "updated": "2024-01-15T00:00:00Z"
}
```

### model_config.yaml

LLM configuration.

```yaml
# Default configuration
provider: openai
model: gpt-4o
temperature: 0.7
max_tokens: 4096

# Alternative configurations
# provider: google
# model: gemini-1.5-pro

# provider: cerebras
# model: llama3.1-70b
```

### prompts/agent.md

System prompt defining personality and expertise.

```markdown
# Weather Assistant

You are a friendly and knowledgeable weather assistant. Your expertise includes:

- Current weather conditions
- Multi-day forecasts
- Severe weather alerts
- Climate patterns and trends
- Travel weather recommendations

## Personality

- Warm and approachable
- Clear and concise in explanations
- Proactive about weather safety
- Uses weather-related analogies when helpful

## Guidelines

1. Always provide temperatures in both Fahrenheit and Celsius
2. Include humidity and wind information when relevant
3. Warn users about severe weather conditions
4. Suggest appropriate clothing or precautions when asked

## Response Format

When providing weather information:
- Lead with the most important information
- Use the weather-view to display forecasts
- Include relevant safety tips for extreme conditions
```

### prompts/orchestrator.md (Optional)

For multi-step task decomposition.

```markdown
# Task Orchestrator

You are responsible for breaking down complex user requests into actionable steps.

## Process

1. Analyze the user's request
2. Identify required information and tools
3. Create a step-by-step plan
4. Execute each step in order
5. Synthesize results into a coherent response

## Guidelines

- Keep steps atomic and focused
- Identify dependencies between steps
- Handle errors gracefully
- Provide progress updates for long tasks
```

---

## Tool Templates

### Basic Tool

```python
# tools/get_weather.py

from a4e.tools import tool
from typing import Optional

@tool
def get_weather(
    city: str,
    units: Optional[str] = "fahrenheit"
) -> dict:
    """
    Get current weather for a city.

    Args:
        city: Name of the city
        units: Temperature units (fahrenheit or celsius)

    Returns:
        Weather data including temperature, condition, humidity
    """
    # Implementation
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny",
        "humidity": 45,
        "units": units
    }
```

### Tool with External API

```python
# tools/fetch_forecast.py

from a4e.tools import tool
import httpx
from typing import List

@tool
async def fetch_forecast(
    city: str,
    days: int = 5
) -> List[dict]:
    """
    Fetch weather forecast for upcoming days.

    Args:
        city: Name of the city
        days: Number of days to forecast (1-10)

    Returns:
        List of daily forecasts
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/forecast",
            params={"city": city, "days": days}
        )
        return response.json()["forecasts"]
```

### Tool with Database

```python
# tools/save_location.py

from a4e.tools import tool
from a4e.database import get_db

@tool
def save_location(
    user_id: str,
    city: str,
    is_default: bool = False
) -> dict:
    """
    Save a user's preferred location.

    Args:
        user_id: User identifier
        city: City name to save
        is_default: Set as default location

    Returns:
        Saved location record
    """
    db = get_db()

    if is_default:
        db.execute(
            "UPDATE locations SET is_default = false WHERE user_id = ?",
            [user_id]
        )

    result = db.execute(
        """
        INSERT INTO locations (user_id, city, is_default)
        VALUES (?, ?, ?)
        RETURNING *
        """,
        [user_id, city, is_default]
    )

    return dict(result.fetchone())
```

### tools/schemas.json

Auto-generated schema file.

```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city.",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "Name of the city"
          },
          "units": {
            "type": "string",
            "enum": ["fahrenheit", "celsius"],
            "description": "Temperature units"
          }
        },
        "required": ["city"]
      }
    }
  ]
}
```

---

## View Templates

### Basic View

```tsx
// views/weather-card/view.tsx

"use client";

import React from "react";

interface WeatherCardProps {
  city: string;
  temperature: number;
  condition: string;
  humidity: number;
  isMobile?: boolean;
}

export default function WeatherCard({
  city,
  temperature,
  condition,
  humidity,
  isMobile
}: WeatherCardProps) {
  return (
    <div className={`
      bg-gradient-to-br from-blue-400 to-blue-600
      rounded-xl shadow-lg text-white
      ${isMobile ? 'p-4' : 'p-6'}
    `}>
      <h2 className="text-xl font-semibold">{city}</h2>
      <div className="text-5xl font-bold my-4">
        {temperature}°
      </div>
      <p className="text-lg capitalize">{condition}</p>
      <p className="text-sm opacity-80">
        Humidity: {humidity}%
      </p>
    </div>
  );
}
```

### Mobile-Optimized Grid View

```tsx
// views/forecast-grid/view.tsx

"use client";

import React from "react";

interface ForecastDay {
  date: string;
  high: number;
  low: number;
  condition: string;
  icon: string;
}

interface ForecastGridProps {
  forecasts: ForecastDay[];
  isMobile?: boolean;
}

export default function ForecastGrid({
  forecasts,
  isMobile
}: ForecastGridProps) {
  return (
    <div className="w-full">
      <h2 className={`
        font-semibold mb-4
        ${isMobile ? 'text-lg' : 'text-xl'}
      `}>
        5-Day Forecast
      </h2>

      <div className={`
        grid gap-3
        ${isMobile
          ? 'grid-cols-2'
          : 'grid-cols-5'
        }
      `}>
        {forecasts.map((day) => (
          <div
            key={day.date}
            className="bg-white rounded-lg p-4 shadow-sm text-center"
          >
            <p className="text-sm text-gray-500">{day.date}</p>
            <div className="text-3xl my-2">{day.icon}</div>
            <p className="font-semibold">{day.high}°</p>
            <p className="text-gray-400">{day.low}°</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Interactive View with State

```tsx
// views/location-picker/view.tsx

"use client";

import React, { useState } from "react";
import { Search, MapPin } from "lucide-react";

interface LocationPickerProps {
  savedLocations: string[];
  onSelect?: (city: string) => void;
  isMobile?: boolean;
}

export default function LocationPicker({
  savedLocations,
  onSelect,
  isMobile
}: LocationPickerProps) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (city: string) => {
    setSelected(city);
    onSelect?.(city);
  };

  return (
    <div className={`w-full ${isMobile ? 'p-3' : 'p-6'}`}>
      {/* Search Input */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search cities..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={`
            w-full pl-10 pr-4 py-3 rounded-lg border
            focus:ring-2 focus:ring-blue-500 focus:border-transparent
            ${isMobile ? 'text-base' : 'text-sm'}
          `}
        />
      </div>

      {/* Saved Locations */}
      <div className="space-y-2">
        {savedLocations
          .filter(loc => loc.toLowerCase().includes(search.toLowerCase()))
          .map((city) => (
            <button
              key={city}
              onClick={() => handleSelect(city)}
              className={`
                w-full flex items-center gap-3 p-3 rounded-lg
                transition-colors
                ${selected === city
                  ? 'bg-blue-100 text-blue-700'
                  : 'hover:bg-gray-100'
                }
              `}
            >
              <MapPin className="w-5 h-5" />
              <span>{city}</span>
            </button>
          ))}
      </div>
    </div>
  );
}
```

### view.schema.json

```json
{
  "name": "weather-card",
  "description": "Display current weather for a location",
  "props": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "City name"
      },
      "temperature": {
        "type": "number",
        "description": "Current temperature"
      },
      "condition": {
        "type": "string",
        "description": "Weather condition"
      },
      "humidity": {
        "type": "number",
        "description": "Humidity percentage"
      },
      "isMobile": {
        "type": "boolean",
        "description": "Mobile viewport flag (auto-injected)"
      }
    },
    "required": ["city", "temperature", "condition", "humidity"]
  }
}
```

---

## Skill Templates

### Basic Skill

```markdown
<!-- skills/check-weather/SKILL.md -->

---
name: check-weather
description: Get current weather for a location
triggers:
  - "what's the weather"
  - "weather in"
  - "current weather"
  - "how's the weather"
view: weather-card
tools:
  - get_weather
requires_auth: false
---

# Check Weather

When a user asks about current weather:

1. Extract the location from their message
2. Call `get_weather` with the location
3. Display results using `weather-card` view

## Handling Missing Location

If no location is specified:
- Check if user has a saved default location
- If not, ask them to specify a location
```

### Skill with Authentication

```markdown
<!-- skills/save-preferences/SKILL.md -->

---
name: save-preferences
description: Save user's weather preferences and locations
triggers:
  - "save this location"
  - "set default city"
  - "remember this place"
view: preferences-saved
tools:
  - save_location
  - get_user_preferences
requires_auth: true
---

# Save Preferences

This skill requires user authentication.

## Flow

1. Verify user is authenticated
2. Extract location from context
3. Ask if this should be the default
4. Save using `save_location` tool
5. Confirm with `preferences-saved` view

## Error Handling

- If not authenticated, prompt user to log in
- If location is ambiguous, ask for clarification
```

### skills/schemas.json

```json
{
  "skills": [
    {
      "id": "check-weather",
      "name": "Check Weather",
      "description": "Get current weather for a location",
      "triggers": [
        "what's the weather",
        "weather in",
        "current weather"
      ],
      "view": "weather-card",
      "tools": ["get_weather"],
      "requires_auth": false
    },
    {
      "id": "save-preferences",
      "name": "Save Preferences",
      "description": "Save user's weather preferences",
      "triggers": [
        "save this location",
        "set default city"
      ],
      "view": "preferences-saved",
      "tools": ["save_location", "get_user_preferences"],
      "requires_auth": true
    }
  ]
}
```

---

## Available Dependencies

### View Imports (Walled Garden)

Views can import from these pre-approved packages:

```tsx
// React
import React, { useState, useEffect, useMemo } from "react";
import { createRoot } from "react-dom/client";

// Icons
import { Search, MapPin, Sun, Cloud } from "lucide-react";

// Animation
import { motion, AnimatePresence } from "framer-motion";

// Utilities
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// A4E SDK (for agent communication)
import { useAgent, sendMessage } from "@/lib/sdk";
```

### Tool Imports

Tools can use any Python package available in the runtime:

```python
# HTTP clients
import httpx
import requests

# Data processing
import pandas as pd
import numpy as np

# Database
import sqlalchemy
from supabase import create_client

# Utilities
from datetime import datetime
from typing import Optional, List, Dict
import json
import yaml
```

---

## Complete Example Agent

See `file-store/agent-store/` for full working examples:

- **jimmy**: Concierge agent with handover
- **aero**: Product catalog with search
- **smartgym**: Equipment recommendations
- **kanban-board**: Task management
- **supabase-table-reader**: Database integration

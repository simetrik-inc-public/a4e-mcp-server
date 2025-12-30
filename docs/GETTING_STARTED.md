# Getting Started with A4E Agent Creator

This guide will walk you through creating your first conversational AI agent in under 5 minutes.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/a4e-mcp-server.git
cd a4e-mcp-server

# Install dependencies
uv sync
```

## Quick Start: Create Your First Agent

### Step 1: Initialize a New Agent

Use the interactive wizard to create a new agent:

```bash
uv run a4e init
```

You'll be prompted for:
- **Agent name**: lowercase with hyphens (e.g., `nutrition-coach`)
- **Display name**: human-readable name (e.g., `Nutrition Coach`)
- **Description**: what your agent does
- **Category**: choose from available categories
- **Template**: basic, with-tools, with-views, or full

**Non-interactive mode:**
```bash
uv run a4e init --name nutrition-coach --display-name "Nutrition Coach" \
  --description "Personalized nutrition guidance" --category "Fitness & Health" \
  --template basic --yes
```

### Step 2: Navigate to Your Agent

```bash
cd nutrition-coach
```

Your agent structure:
```
nutrition-coach/
├── agent.py              # Agent factory
├── metadata.json         # Marketplace metadata
├── AGENTS.md             # AI coding guide
├── prompts/
│   ├── agent.md          # Main personality
│   └── ...
├── tools/
│   └── schemas.json      # Tool definitions
├── views/
│   ├── welcome/          # Mandatory welcome view
│   └── schemas.json
└── skills/
    ├── show_welcome/     # Default skill
    └── schemas.json
```

### Step 3: Add a Tool

Tools are Python functions your agent can call. Add one interactively:

```bash
uv run a4e add tool
```

Or with options:
```bash
uv run a4e add tool calculate_bmi -d "Calculate Body Mass Index"
```

This creates `tools/calculate_bmi.py`:
```python
from a4e.sdk import tool
from typing import Optional

@tool
def calculate_bmi(
    weight_kg: float,
    height_m: float,
) -> dict:
    """Calculate Body Mass Index"""
    bmi = weight_kg / (height_m ** 2)
    return {"bmi": round(bmi, 1), "status": "success"}
```

### Step 4: Add a View

Views are React components that render your agent's responses:

```bash
uv run a4e add view bmi-result -d "Display BMI calculation result"
```

This creates `views/bmi-result/view.tsx`:
```tsx
"use client";
import React from "react";

interface BmiResultProps {
  bmi: number;
  category: string;
}

export default function BmiResultView(props: BmiResultProps) {
  const { bmi, category } = props;
  return (
    <div className="p-6">
      <h2>Your BMI: {bmi}</h2>
      <p>Category: {category}</p>
    </div>
  );
}
```

### Step 5: Add a Skill

Skills connect user intents to tools and views:

```bash
uv run a4e add skill calculate_bmi_skill \
  --name "Calculate BMI" \
  --view bmi-result \
  --triggers "calculate bmi,check my bmi,what is my bmi"
```

### Step 6: Validate Your Agent

Check for errors before testing:

```bash
uv run a4e validate
```

### Step 7: Start the Development Server

```bash
uv run a4e dev start
```

This starts a local server with ngrok tunnel for testing.

## Next Steps

- [CLI Reference](../CLI.md) - Full command documentation
- [Examples](./EXAMPLES.md) - Sample agent implementations
- [AGENTS.md](../AGENTS.md) - Project architecture reference

## Common Workflows

### List Everything
```bash
uv run a4e list all
```

### Check Agent Info
```bash
uv run a4e info
```

### Remove a Component
```bash
uv run a4e remove tool calculate_bmi
uv run a4e remove view bmi-result
uv run a4e remove skill calculate_bmi_skill
```

### Deploy to Production
```bash
uv run a4e deploy
```

## Using with MCP (IDE Integration)

If you're using Cursor, VS Code with Claude, or Claude Desktop, you can use the MCP tools directly:

1. Configure the MCP server in your IDE
2. Use natural language to manage agents:
   - "Initialize a new fitness agent"
   - "Add a tool for tracking workouts"
   - "Create a view for showing progress charts"

See [README.md](../README.md) for MCP setup instructions.

## Troubleshooting

### Command Not Found
Make sure you're running commands with `uv run`:
```bash
uv run a4e --help
```

### Development Server Issues
1. Check if port 5000 is in use:
   ```bash
   lsof -i :5000
   ```
2. Set ngrok token:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

### Validation Errors
Run with verbose output:
```bash
uv run a4e validate --agent ./path/to/agent
```

## Getting Help

- Run `uv run a4e --help` for CLI help
- Check [AGENTS.md](../AGENTS.md) for architecture details
- Open an issue on GitHub for bugs

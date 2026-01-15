# Getting Started with A4E

Create your first conversational AI agent in under 5 minutes.

## Prerequisites

### Python 3.10+

```bash
# Check your version
python --version

# Install if needed (macOS)
brew install python@3.10

# Install if needed (Ubuntu/Debian)
sudo apt update && sudo apt install python3.10
```

### ngrok Account (for dev server)

The development server uses ngrok to create public tunnels.

1. Sign up: https://ngrok.com/signup
2. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure:

```bash
# Option A: Install ngrok CLI
brew install ngrok/ngrok/ngrok  # macOS
ngrok config add-authtoken YOUR_TOKEN

# Option B: Environment variable
export NGROK_AUTHTOKEN=YOUR_TOKEN
```

## Installation

```bash
pip install a4e
```

Verify:

```bash
a4e --version
```

## Create Your First Agent

### Step 1: Initialize

```bash
# Interactive mode (recommended)
a4e init

# Or non-interactive
a4e init --name nutrition-coach \
  --display-name "Nutrition Coach" \
  --description "Personalized nutrition guidance" \
  --category "Fitness & Health" \
  --template basic --yes
```

### Step 2: Explore the structure

```bash
cd nutrition-coach
```

```
nutrition-coach/
├── agent.py              # Agent configuration
├── metadata.json         # Marketplace metadata
├── AGENTS.md             # AI coding assistant guide
├── prompts/
│   └── agent.md          # System prompt / personality
├── tools/
│   └── schemas.json      # Tool definitions
├── views/
│   ├── welcome/          # Default welcome view
│   └── schemas.json      # View definitions
└── skills/
    ├── show_welcome/     # Default skill
    └── schemas.json      # Skill definitions
```

### Step 3: Add a Tool

```bash
# Interactive
a4e add tool

# Or with options
a4e add tool calculate_bmi -d "Calculate Body Mass Index"
```

This creates `tools/calculate_bmi.py`:

```python
from typing import Dict, Any

def calculate_bmi(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Body Mass Index."""
    weight = params.get("weight_kg")
    height = params.get("height_m")
    
    bmi = weight / (height ** 2)
    
    return {
        "bmi": round(bmi, 1),
        "status": "success"
    }
```

### Step 4: Add a View

```bash
a4e add view bmi-result -d "Display BMI calculation result"
```

This creates `views/bmi-result/view.tsx`:

```tsx
"use client";
import React from "react";

interface BmiResultProps {
  bmi: number;
  category: string;
}

export default function BmiResultView({ bmi, category }: BmiResultProps) {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold">Your BMI: {bmi}</h2>
      <p className="text-gray-600">Category: {category}</p>
    </div>
  );
}
```

### Step 5: Add a Skill

Skills connect user intents to tools and views:

```bash
a4e add skill show_bmi \
  --name "Calculate BMI" \
  --view bmi-result \
  --triggers "calculate bmi,check my bmi,what is my bmi" \
  --tools calculate_bmi
```

### Step 6: Validate

```bash
a4e validate
```

Expected output:

```
Validating agent: nutrition-coach
✓ Required files present
✓ Python syntax valid
✓ Type hints present
✓ Schemas generated
✓ Skills valid

Validation passed!
```

### Step 7: Start Dev Server

```bash
a4e dev start
```

This starts:
- Local server at `http://localhost:5000`
- ngrok tunnel for external access
- File watcher for hot-reload

## Using with AI Assistant (MCP)

Instead of CLI commands, you can use A4E directly from your AI assistant.

### Setup

```bash
# Configure for your IDE
a4e mcp setup cursor       # Cursor
a4e mcp setup claude-code  # Claude Code
a4e mcp setup antigravity  # Antigravity

# Restart your IDE
```

### Usage

Ask your AI assistant:

- "Create an agent called fitness-tracker"
- "Add a tool to log workouts"
- "Add a view to show progress charts"
- "Start the development server"
- "Validate and deploy the agent"

## Common Workflows

### List components

```bash
a4e list all
a4e list tools
a4e list views
a4e list skills
```

### Get agent info

```bash
a4e info
a4e info --json
```

### Remove components

```bash
a4e remove tool calculate_bmi
a4e remove view bmi-result
a4e remove skill show_bmi
```

### Deploy to production

```bash
a4e deploy
```

## Troubleshooting

### Command not found

```bash
# Ensure pip scripts are in PATH
export PATH="$HOME/.local/bin:$PATH"

# Or use pipx
pipx install a4e
```

### ngrok errors

```bash
# Verify ngrok is configured
ngrok config check

# Add token if missing
ngrok config add-authtoken YOUR_TOKEN

# Or pass directly
a4e dev start --auth-token YOUR_TOKEN
```

### Port in use

```bash
# Check what's using port 5000
lsof -i :5000

# Use different port
a4e dev start --port 5001
```

### Validation errors

```bash
# Run with verbose output
a4e validate --agent ./path/to/agent

# Common fixes:
# - Missing files: Re-run a4e init
# - Type hints: Add return types to functions
# - Schema errors: Re-run a4e add tool/view
```

## Next Steps

- [CLI Reference](../CLI.md) - Full command documentation
- [Examples](./EXAMPLES.md) - Sample agent implementations
- [View System](./VIEW_SYSTEM.md) - How views work in production

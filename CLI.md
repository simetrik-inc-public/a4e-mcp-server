# A4E CLI Reference

Complete command reference for the A4E Agent Creator CLI.

## Installation & Running

```bash
# Using uv (recommended)
uv run a4e --help

# Using python directly
python -m a4e.cli --help
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `a4e init` | Initialize a new agent project |
| `a4e add` | Add tools, views, or skills |
| `a4e list` | List tools, views, or skills |
| `a4e remove` | Remove tools, views, or skills |
| `a4e validate` | Validate agent project |
| `a4e deploy` | Deploy agent to production |
| `a4e info` | Display agent information |
| `a4e dev` | Development server commands |

---

## `a4e init`

Initialize a new A4E agent project with an interactive wizard.

```bash
a4e init [OPTIONS]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Agent ID (lowercase, hyphens) |
| `--display-name` | `-d` | Human-readable name |
| `--description` | | Short description |
| `--category` | `-c` | Agent category |
| `--template` | `-t` | Project template |
| `--directory` | | Directory to create agent in |
| `--yes` | `-y` | Skip interactive prompts |

### Categories

- Concierge
- E-commerce
- Fitness & Health
- Education
- Entertainment
- Productivity
- Finance
- Customer Support
- General

### Templates

| Template | Description |
|----------|-------------|
| `basic` | Minimal files only |
| `with-tools` | Basic + example tool |
| `with-views` | Basic + example view |
| `full` | Basic + example tool + view |

### Examples

```bash
# Interactive mode
a4e init

# Non-interactive mode
a4e init --name nutrition-coach --display-name "Nutrition Coach" \
  --description "Personalized nutrition guidance" \
  --category "Fitness & Health" --template basic --yes
```

---

## `a4e add`

Add components to your agent.

### `a4e add tool`

Add a new tool (Python function) to the agent.

```bash
a4e add tool [TOOL_NAME] [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--description` | `-d` | Tool description |
| `--parameters` | `-p` | Parameters as JSON string |
| `--agent` | `-a` | Agent name/path |
| `--yes` | `-y` | Skip interactive prompts |

```bash
# Interactive
a4e add tool

# With options
a4e add tool calculate_bmi -d "Calculate Body Mass Index"

# With parameters
a4e add tool search_products -d "Search products" \
  -p '{"query": {"type": "string", "required": true}}'
```

### `a4e add view`

Add a new React view to the agent.

```bash
a4e add view [VIEW_ID] [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--description` | `-d` | View description |
| `--props` | `-p` | Props as JSON string |
| `--agent` | `-a` | Agent name/path |
| `--yes` | `-y` | Skip interactive prompts |

```bash
# Interactive
a4e add view

# With options
a4e add view bmi-result -d "Display BMI result"

# With props
a4e add view product-card -d "Product display" \
  -p '{"title": {"type": "string"}, "price": {"type": "number"}}'
```

### `a4e add skill`

Add a new skill to the agent.

```bash
a4e add skill [SKILL_ID] [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Display name |
| `--description` | `-d` | Skill description |
| `--triggers` | `-t` | Comma-separated intent triggers |
| `--view` | `-v` | Output view ID |
| `--tools` | | Comma-separated internal tools |
| `--auth` | | Requires authentication |
| `--agent` | `-a` | Agent name/path |
| `--yes` | `-y` | Skip interactive prompts |

```bash
# Interactive
a4e add skill

# With options
a4e add skill show_bmi --name "Show BMI" --view bmi-result \
  --triggers "calculate bmi,check my bmi"
```

---

## `a4e list`

List components in your agent.

### `a4e list tools`

```bash
a4e list tools [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent name/path |
| `--verbose` | `-v` | Show detailed information |

### `a4e list views`

```bash
a4e list views [OPTIONS]
```

### `a4e list skills`

```bash
a4e list skills [OPTIONS]
```

### `a4e list all`

List all tools, views, and skills.

```bash
a4e list all [OPTIONS]
```

---

## `a4e remove`

Remove components from your agent.

### `a4e remove tool`

```bash
a4e remove tool TOOL_NAME [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent name/path |
| `--yes` | `-y` | Skip confirmation |

```bash
a4e remove tool calculate_bmi --yes
```

### `a4e remove view`

```bash
a4e remove view VIEW_ID [OPTIONS]
```

**Note:** The `welcome` view cannot be removed.

### `a4e remove skill`

```bash
a4e remove skill SKILL_ID [OPTIONS]
```

**Note:** The `show_welcome` skill cannot be removed.

---

## `a4e validate`

Validate the agent project for errors and warnings.

```bash
a4e validate [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent name/path |
| `--strict` | `-s` | Treat warnings as errors |

### Validation Checks

| Check | Type | Description |
|-------|------|-------------|
| Required files | Error | agent.py, metadata.json, prompts/agent.md |
| Python syntax | Error | All .py files must be valid |
| Type hints | Error | Public functions need type hints |
| Schemas | Error | schemas.json must exist if tools/views present |
| Skill dependencies | Error | Output view must exist |
| Skill docs | Warning | Each skill should have SKILL.md |

```bash
# Basic validation
a4e validate

# Strict mode (warnings fail)
a4e validate --strict
```

---

## `a4e deploy`

Deploy the agent to production.

```bash
a4e deploy [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent name/path |
| `--skip-validation` | | Skip pre-deployment validation |
| `--yes` | `-y` | Skip confirmation |

```bash
# Deploy with validation
a4e deploy

# Skip validation
a4e deploy --skip-validation --yes
```

---

## `a4e info`

Display information about the agent.

```bash
a4e info [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent name/path |
| `--json` | `-j` | Output as JSON |

```bash
# Human-readable
a4e info

# JSON output
a4e info --json
```

---

## `a4e dev`

Development server commands.

### `a4e dev start`

Start the development server with ngrok tunnel.

```bash
a4e dev start [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--directory` | Directory containing agent-store |
| `--port` | Local port (default: 5000) |
| `--auth-token` | Ngrok auth token |

```bash
a4e dev start --directory file-store/agent-store
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `A4E_WORKSPACE` | Default workspace directory |
| `NGROK_AUTHTOKEN` | Ngrok authentication token |

---

## Troubleshooting

### Development Server Issues

1. **Port in use:**
   ```bash
   # macOS/Linux
   lsof -i :5000
   kill -9 <PID>

   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /T /F
   ```

2. **Ngrok not configured:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

3. **Manual server start:**
   ```bash
   python a4e/dev_runner.py --agent-path ./my-agent
   ```

### Validation Errors

Common fixes:
- **Missing files**: Run `a4e init` to regenerate structure
- **Type hints**: Add return type annotations to functions
- **Schema errors**: Run `a4e add tool/view` to regenerate

### Import Errors

Ensure dependencies are installed:
```bash
uv sync
# or
pip install -e .
```

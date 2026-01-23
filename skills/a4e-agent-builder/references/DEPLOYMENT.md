# A4E Deployment Guide

Complete guide for deploying agents to the A4E Hub.

## Overview

The deployment workflow consists of:
1. **Validation** - Ensure agent structure is correct
2. **Dev Mode** - Test locally with ngrok tunnel
3. **Playground Testing** - Verify in A4E Hub playground
4. **Deployment** - Deploy to production

---

## Validation

Before deploying, validate your agent structure:

### Using CLI

```bash
uv run a4e validate
```

### Using MCP Tool

Call the `validate` tool in your IDE.

### What's Validated

| Check | Required | Description |
|-------|----------|-------------|
| `agent.py` | Yes | Entry point exists and has valid Python syntax |
| `metadata.json` | Yes | Valid JSON with required fields |
| `prompts/agent.md` | Yes | System prompt exists |
| `tools/schemas.json` | Yes | Tool schemas are valid |
| `views/schemas.json` | Yes | View schemas are valid |
| Type hints | Yes | Public functions have type annotations |
| Skill dependencies | Yes | Skills reference existing views/tools |

### Validation Modes

**Standard validation:**
```bash
uv run a4e validate
```

**Strict validation (for deployment):**
```bash
uv run a4e validate --strict
```

Strict mode enforces:
- All schemas regenerated and up-to-date
- No unused tools or views
- Complete documentation

---

## Dev Mode

Dev mode creates a local server with ngrok tunnel for testing.

### Start Dev Server

```bash
# Default port (5000)
uv run a4e dev start

# Custom port
uv run a4e dev start --port 8000

# With specific agent
uv run a4e dev start --agent my-agent
```

### What Happens

1. **Local Server Starts**
   - FastMCP server on specified port
   - REST API endpoints for agent interaction
   - SSE support for streaming responses

2. **ngrok Tunnel Created**
   - Public HTTPS URL generated
   - URL copied to clipboard automatically

3. **File Watching**
   - Monitors agent directory for changes
   - Auto-reloads on file modifications

### Dev Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent-info` | GET | Agent metadata |
| `/tools` | GET | Available tools |
| `/views` | GET | Available views |
| `/skills` | GET | Available skills |
| `/system-prompt` | GET | System prompt |
| `/download` | GET | Download agent as ZIP |
| `/api/agents/{name}/unified-stream` | POST | Stream agent responses |
| `/mcp/*` | * | MCP SSE endpoints |

### Stop Dev Server

```bash
uv run a4e dev stop --port 5000
```

---

## Playground Testing

### Access Playground

After starting dev mode, access the playground:

```
https://dev-a4e.global.simetrik.com/builder/playground?url=<ngrok_url>&agent=<agent_id>
```

The URL is automatically copied to your clipboard when dev mode starts.

### Testing Checklist

- [ ] Agent responds to basic messages
- [ ] Tools execute correctly
- [ ] Views render properly
- [ ] Skills trigger on expected phrases
- [ ] Error handling works
- [ ] Mobile views display correctly (resize browser)

### Debug Mode

In the playground:
1. Open browser DevTools (F12)
2. Check Console for errors
3. Network tab shows API calls
4. View rendered output in Elements tab

---

## Deployment

### Using CLI

```bash
# Interactive deployment
uv run a4e deploy

# With options
uv run a4e deploy --agent my-agent --skip-validation --yes
```

### Using MCP Tool

Call the `deploy` tool in your IDE.

### Deployment Process

1. **Pre-deployment Validation**
   - Strict validation runs automatically
   - All errors must be resolved

2. **Schema Regeneration**
   - `tools/schemas.json` regenerated
   - `views/schemas.json` regenerated
   - `skills/schemas.json` regenerated

3. **Upload to Hub**
   - Agent files packaged
   - Uploaded to A4E Hub
   - Registered in agent registry

4. **Confirmation**
   - Deployment URL provided
   - Agent available in Hub

### Deployment Options

| Option | Description |
|--------|-------------|
| `--agent` | Specify agent to deploy |
| `--skip-validation` | Skip pre-deployment validation |
| `--yes` | Auto-confirm prompts |
| `--environment` | Target environment (staging/prod) |

---

## Hub Integration

### A4E Hub URL

```
https://dev-a4e.global.simetrik.com
```

### Agent Access

After deployment, agents are accessible at:
- **Playground:** `/builder/playground?agent=<agent_id>`
- **Chat:** `/chat/<agent_id>`
- **API:** `/api/agents/<agent_id>`

### Agent Registry

Deployed agents appear in:
- Hub agent list
- Agent selection dropdown
- Handover targets for other agents

---

## Post-Deployment

### Verification Steps

1. **Test in Production**
   ```
   https://dev-a4e.global.simetrik.com/chat/<agent_id>
   ```

2. **Check Agent Info**
   - Verify metadata is correct
   - Confirm version number
   - Check capability flags

3. **Test All Features**
   - Run through all skills
   - Test tool execution
   - Verify view rendering

### Monitoring

- Check Hub dashboard for usage metrics
- Monitor error rates
- Review conversation logs

### Rollback

If issues are found:
1. Fix the issue locally
2. Test in dev mode
3. Redeploy with fixes

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Agent

on:
  push:
    branches: [main]
    paths:
      - 'agents/my-agent/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: cd a4e-mcp-server && uv sync

      - name: Validate agent
        run: uv run a4e validate --agent my-agent --strict

      - name: Deploy
        run: uv run a4e deploy --agent my-agent --yes
        env:
          A4E_API_KEY: ${{ secrets.A4E_API_KEY }}
```

---

## Troubleshooting

### "Validation failed"

```bash
# See detailed errors
uv run a4e validate --verbose

# Fix issues and retry
uv run a4e validate
```

### "ngrok tunnel failed"

1. Check ngrok authentication: `ngrok config check`
2. Verify internet connection
3. Try different port: `--port 8000`

### "Agent not found in Hub"

1. Verify deployment succeeded
2. Check agent ID spelling
3. Confirm environment (staging vs prod)

### "Views not rendering"

1. Check browser console for errors
2. Verify view schema matches props
3. Test view in isolation

### "Tools not executing"

1. Check tool implementation for errors
2. Verify parameters match schema
3. Test tool directly in dev mode

---

## Best Practices

### Before Deployment

- [ ] Run full validation
- [ ] Test all skills in dev mode
- [ ] Review system prompt
- [ ] Check mobile responsiveness
- [ ] Test error scenarios

### Version Control

- Tag releases in git
- Use semantic versioning
- Keep changelog updated

### Environment Management

- Use staging for testing
- Promote to prod after verification
- Keep environments in sync

### Documentation

- Update metadata description
- Document new features
- Note breaking changes

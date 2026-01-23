# A4E Agent Builder Skill - Installation Guide

This guide explains how to install the A4E Agent Builder skill across different AI development tools that support the [Agent Skills](https://agentskills.io) standard.

## Overview

The **A4E Agent Builder** skill provides AI assistants with comprehensive knowledge about building, managing, and deploying A4E agents. It includes:

- Agent architecture and structure
- MCP server tools reference
- Database integration patterns
- Mobile-optimized view development
- UI/UX design guidelines
- Deployment workflows

## Prerequisites

Before installing the skill, ensure you have:

1. **Git** installed (for cloning the repository)
2. **A4E MCP Server** (optional but recommended for full functionality)
   - Repository: https://github.com/simetrik-inc-public/a4e-mcp-server
   - See [MCP-INSTALLATION.md](references/MCP-INSTALLATION.md) for setup

## Installation Methods

### Method 1: Git Clone (Recommended)

Clone the entire MCP repository to get the skill and stay up-to-date:

```bash
# Clone the repository
git clone https://github.com/simetrik-inc-public/a4e-mcp-server.git

# The skill is located at:
# a4e-mcp-server/skills/a4e-agent-builder/
```

Then follow the platform-specific instructions below to link or copy the skill to your AI assistant.

### Method 2: Direct Download

Download just the skill directory:

```bash
# Create skills directory if it doesn't exist
mkdir -p ~/Downloads/a4e-agent-builder

# Download using curl (requires GitHub raw URL)
# Or manually download from GitHub
```

---

## Platform-Specific Installation

### Claude Code

Claude Code automatically discovers skills in two locations:

**Personal Skills** (available across all projects):
```bash
# Copy to personal skills directory
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.claude/skills/

# Or create a symlink for auto-updates
ln -s "$(pwd)/a4e-mcp-server/skills/a4e-agent-builder" ~/.claude/skills/
```

**Project Skills** (specific to current project):
```bash
# Copy to project skills directory
mkdir -p .claude/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder .claude/skills/

# Or symlink
ln -s "$(pwd)/a4e-mcp-server/skills/a4e-agent-builder" .claude/skills/
```

**Verification:**
- Restart Claude Code or reload the window
- Ask: "What skills are available?"
- Invoke directly: `/a4e-agent-builder`

---

### Cursor

Cursor supports Agent Skills in similar locations:

**Personal Skills:**
```bash
# macOS/Linux
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.cursor/skills/

# Windows (PowerShell)
Copy-Item -Recurse a4e-mcp-server\skills\a4e-agent-builder "$env:USERPROFILE\.cursor\skills\"
```

**Project Skills:**
```bash
# macOS/Linux
mkdir -p .cursor/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder .cursor/skills/

# Windows (PowerShell)
New-Item -ItemType Directory -Force .cursor\skills
Copy-Item -Recurse a4e-mcp-server\skills\a4e-agent-builder .cursor\skills\
```

**Verification:**
- Restart Cursor
- Check if skill appears in the skills menu
- Test with: `@a4e-agent-builder`

---

### Claude Desktop

Claude Desktop integrates skills through the MCP server configuration:

**Edit:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "a4e": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/a4e-mcp-server",
        "python",
        "-m",
        "a4e.server"
      ]
    }
  },
  "skills": {
    "directories": [
      "/absolute/path/to/a4e-mcp-server/skills"
    ]
  }
}
```

Replace `/absolute/path/to/a4e-mcp-server` with your actual path.

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Verification:**
- Restart Claude Desktop
- Skills should load automatically from the configured directory

---

### VS Code with Continue

Continue extension supports skills through workspace configuration:

**Edit:** `.vscode/settings.json` or `settings.json` globally

```json
{
  "continue.skills": {
    "directories": [
      "${workspaceFolder}/a4e-mcp-server/skills",
      "~/.continue/skills"
    ]
  }
}
```

Or copy to Continue's skills directory:

```bash
# macOS/Linux
mkdir -p ~/.continue/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.continue/skills/

# Windows
New-Item -ItemType Directory -Force "$env:USERPROFILE\.continue\skills"
Copy-Item -Recurse a4e-mcp-server\skills\a4e-agent-builder "$env:USERPROFILE\.continue\skills\"
```

**Verification:**
- Reload VS Code window
- Check Continue's skill list

---

### Windsurf

Windsurf (by Codeium) supports Agent Skills:

```bash
# Copy to Windsurf skills directory
mkdir -p ~/.windsurf/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.windsurf/skills/
```

**Verification:**
- Restart Windsurf
- Skills should be available in the chat interface

---

### Cline (formerly Claude Dev)

Cline supports skills through VS Code settings:

```bash
# Copy to Cline skills directory
mkdir -p ~/.cline/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.cline/skills/
```

Or configure in VS Code settings:

```json
{
  "cline.skills.directories": [
    "~/.cline/skills"
  ]
}
```

---

### Aider

Aider uses a skills directory in your project or home:

```bash
# Project-level
mkdir -p .aider/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder .aider/skills/

# User-level
mkdir -p ~/.aider/skills
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.aider/skills/
```

---

### Generic Agent Skills Compatible Tools

For any tool supporting the [Agent Skills standard](https://agentskills.io):

1. **Locate the skills directory** for your tool (check documentation)
2. **Copy or symlink** the skill directory:
   ```bash
   cp -r a4e-mcp-server/skills/a4e-agent-builder /path/to/tool/skills/
   ```
3. **Restart** the tool or reload the configuration
4. **Verify** by listing available skills or invoking `/a4e-agent-builder`

---

## Verification

After installation, verify the skill is loaded:

1. **Check skill list:**
   - Ask your AI assistant: "What skills are available?"
   - Look for `a4e-agent-builder` in the response

2. **Invoke the skill:**
   - Use the slash command: `/a4e-agent-builder`
   - Or ask: "How do I create an A4E agent?"

3. **Check skill metadata:**
   - The assistant should know about:
     - Agent architecture
     - MCP tools
     - Database integration
     - View development

---

## Troubleshooting

### Skill not detected

**Check directory structure:**
```bash
ls -R /path/to/skills/a4e-agent-builder/
```

Should show:
```
SKILL.md
SKILL-INSTALLATION.md
references/
  AGENT-STRUCTURE.md
  MCP-TOOLS.md
  DATABASE-GUIDE.md
  ...
```

**Verify SKILL.md has proper frontmatter:**
```bash
head -n 12 /path/to/skills/a4e-agent-builder/SKILL.md
```

Should start with:
```yaml
---
name: a4e-agent-builder
description: Build and manage A4E ...
---
```

### Symlinks not working

Some tools may not support symlinks. Use direct copy instead:
```bash
cp -r a4e-mcp-server/skills/a4e-agent-builder /path/to/skills/
```

### Path issues on Windows

Use PowerShell and escape backslashes:
```powershell
$source = "C:\path\to\a4e-mcp-server\skills\a4e-agent-builder"
$dest = "$env:USERPROFILE\.claude\skills\a4e-agent-builder"
Copy-Item -Recurse $source $dest
```

### Skill works but references don't load

Ensure the `references/` directory was copied:
```bash
ls /path/to/skills/a4e-agent-builder/references/
```

Should contain all 8 documentation files.

---

## Updating the Skill

To update to the latest version:

**If installed via git clone:**
```bash
cd a4e-mcp-server
git pull origin main
```

**If installed via copy:**
```bash
# Re-copy from the updated repository
cp -r a4e-mcp-server/skills/a4e-agent-builder ~/.claude/skills/
```

**If using symlink:**
- Symlinks auto-update when you `git pull` the source repository

---

## Uninstallation

To remove the skill:

```bash
# Remove from personal directory
rm -rf ~/.claude/skills/a4e-agent-builder

# Remove from project directory
rm -rf .claude/skills/a4e-agent-builder

# Remove symlink (doesn't delete source)
rm ~/.claude/skills/a4e-agent-builder
```

---

## Additional Resources

- **Agent Skills Standard:** https://agentskills.io
- **A4E MCP Server:** https://github.com/simetrik-inc-public/a4e-mcp-server
- **MCP Installation Guide:** [references/MCP-INSTALLATION.md](references/MCP-INSTALLATION.md)
- **Agent Structure Reference:** [references/AGENT-STRUCTURE.md](references/AGENT-STRUCTURE.md)
- **Skills Validation Tool:** https://github.com/agentskills/agentskills/tree/main/skills-ref

---

## Platform Support Matrix

| Platform | Skills Support | Installation Method | Auto-Discovery |
|----------|---------------|---------------------|----------------|
| Claude Code | ✅ Full | Copy/Symlink | ✅ Yes |
| Cursor | ✅ Full | Copy/Symlink | ✅ Yes |
| Claude Desktop | ✅ Via MCP | Config File | ✅ Yes |
| VS Code (Continue) | ✅ Full | Copy/Settings | ✅ Yes |
| Windsurf | ✅ Full | Copy | ✅ Yes |
| Cline | ✅ Full | Copy/Settings | ✅ Yes |
| Aider | ✅ Full | Copy | ⚠️ Manual |
| GitHub Copilot | ⚠️ Limited | N/A | ❌ No |
| Other Agent Skills tools | ✅ Standard | Copy | Varies |

**Legend:**
- ✅ Full: Complete Agent Skills support
- ⚠️ Limited: Partial or experimental support
- ❌ No: Not supported

---

## Contributing

Found an issue or want to improve the skill? Contribute to the repository:

https://github.com/simetrik-inc-public/a4e-mcp-server

---

## License

This skill is licensed under the MIT License. See the repository for details.

# Bug Report: Production View Renderer Returns "NONE" Instead of Skill's Output View

## Summary

When testing agents in the A4E Playground with a dev server (via ngrok), the View Renderer returns `{"id":"NONE","params":{}}` even when skills are properly configured with `output.view` values.

## Environment

- **Agent**: `travel-assistant`
- **Dev Server**: Running on port 5001, exposed via ngrok
- **Playground URL**: `https://dev-a4e.global.simetrik.com/builder/playground`
- **Test Input**: "Show me the lakefront hotels"

## Expected Behavior

1. Skill Selector matches `browse_category` skill (has "lakefront" trigger)
2. Skill's `output.view` is `"category_browse"`
3. View Renderer returns `{"id":"category_browse","params":{...}}`
4. Frontend renders the `category_browse` view

## Actual Behavior

1. Conversational agent responds: "¡Claro! Mostrando las propiedades lakefront para ti."
2. View Renderer returns: `{"id":"NONE","params":{}}`
3. Frontend shows: `[StreamClient] View is NONE or empty, skipping: NONE`
4. View does NOT change

## Stream Output Evidence

```
message {"type":"chat","content":"¡Claro! Mostrando las propiedades lakefront para ti."}
message {"type":"status","content":"Reviewing response quality..."}
message {"type":"view","content":{"id":"NONE","params":{}}}
message {"type":"done"}
```

## Dev Server Configuration (Verified Working)

### Skills Endpoint (`/skills`)
```json
{
  "browse_category": {
    "id": "browse_category",
    "intent_triggers": ["show me the lakefront hotels", "lakefront", ...],
    "output": {"view": "category_browse"}
  }
}
```

### New Endpoints Added
- `GET /skills/{skill_id}/instructions` - Returns SKILL.md file
- `POST /tools/{tool_name}/call` - Executes tool and returns result

### All Endpoints Return Valid Data
```bash
# Skills
curl http://localhost:5001/skills  # Returns 9 skills with output.view

# SKILL.md
curl http://localhost:5001/skills/browse_category/instructions  # Returns SKILL.md

# Tool Call
curl -X POST http://localhost:5001/tools/get_property_categories/call \
  -H "Content-Type: application/json" \
  -d '{"include_counts": true}'  # Returns categories data
```

## Root Cause Analysis

### Issue 1: Production Doesn't Use Dev Server's System Prompt

The dev server logs show production called:
- `GET /skills` ✓
- `GET /views` ✓

But did NOT call:
- `GET /system-prompt` ✗

Evidence: The agent responded in **Spanish** ("¡Claro!") even though the dev server's prompt says "Respond in English only".

### Issue 2: View Renderer Not Using Skill's output.view

The skill `browse_category` has `"output": {"view": "category_browse"}`, but the View Renderer returns `"NONE"` instead.

Possible causes:
1. View Renderer doesn't read the skill's `output.view` from `/skills` response
2. View Renderer fails silently when calling `/skills/{id}/instructions`
3. View Renderer defaults to "NONE" on any error

### Issue 3: View Renderer Not Calling Tools

The View Renderer should call `/tools/{tool_name}/call` to generate `view_params`, but this endpoint was never called (not in dev server logs).

## Proposed Fixes

### Option A: Use Dev Server's System Prompt
Production should fetch and use `/system-prompt` from the dev server so the conversational agent outputs `#VIEW:` and `#PARAMS:` tags.

### Option B: Fix View Renderer Agent
The View Renderer should:
1. Read the matched skill's `output.view` value
2. Call `/skills/{skill_id}/instructions` to get SKILL.md
3. Call `/tools/{tool_name}/call` to execute internal tools
4. Return `{"id": "<view_id>", "params": {...}}`

### Option C: Add Fallback to Skill's output.view
If View Renderer fails, fallback to the skill's `output.view` with empty params:
```python
# Pseudocode
try:
    view_params = view_renderer.generate_params(skill)
except Exception:
    # Fallback to skill's configured view
    return {"id": skill.output.view, "params": {}}
```

## How to Reproduce

1. Create agent with skills that have `output.view` configured
2. Start dev server: `python dev_runner.py --agent-path <agent> --port 5001`
3. Expose via ngrok: `ngrok http 5001`
4. Open playground: `https://dev-a4e.global.simetrik.com/builder/playground?url=<ngrok-url>`
5. Type a message that matches a skill's intent_trigger
6. Observe: View returns "NONE" instead of the skill's `output.view`

## Files to Check in Production

1. **View Renderer Agent Implementation** - How it gets the view ID
2. **Skill Selector → View Renderer handoff** - Is `output.view` passed?
3. **Error handling** - Where is "NONE" set as a fallback?
4. **System prompt fetching** - Does production call `/system-prompt`?

## Contact

Please reach out if you need access to the dev server logs or additional debugging information.

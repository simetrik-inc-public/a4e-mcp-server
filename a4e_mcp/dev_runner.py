import sys
import os
import importlib.util
import inspect
import json
import argparse
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Dict, Callable

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Anthropic client singleton
_anthropic_client = None

def get_anthropic_client():
    """Get or create Anthropic client for LLM calls"""
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            raise ValueError("ANTHROPIC_API_KEY environment variable not set. Please add it to .env file.")
        _anthropic_client = Anthropic(api_key=api_key)
    return _anthropic_client

def draft_to_widget_params(draft: dict) -> dict:
    """Convert Supabase draft data to rfs_form widget params format"""
    return {
        "title": draft.get("title") or None,
        "problem_description": draft.get("problem_description") or None,
        "industry": draft.get("industry") or None,
        "budget_min": draft.get("budget_min"),
        "budget_max": draft.get("budget_max"),
        "timeline_months": draft.get("timeline_months"),
        "equity_offered": draft.get("equity_offered"),
        "equity_percentage": draft.get("equity_percentage"),
        "step": _calculate_step(draft),
        "is_complete": draft.get("is_complete", False)
    }

def _calculate_step(draft: dict) -> int:
    """Calculate which step of the form the user is on based on filled fields"""
    steps = ["title", "problem_description", "industry", "budget_min", "timeline_months"]
    for i, field in enumerate(steps):
        if not draft.get(field):
            return i + 1
    return len(steps) + 1  # All done

# Mock a4e SDK and autogen
def _mock_dependencies():
    """Mock a4e.sdk and autogen_agentchat to allow agent.py to load"""
    if "a4e" not in sys.modules:
        a4e = ModuleType("a4e")
        sdk = ModuleType("a4e.sdk")
        
        class MockAgentFactory:
            @staticmethod
            async def create_agent(*args, **kwargs):
                return "MockAgentInstance"
        
        sdk.AgentFactory = MockAgentFactory
        
        # Mock tool decorator
        def tool(func):
            func._is_tool = True
            return func
        sdk.tool = tool
        
        a4e.sdk = sdk
        sys.modules["a4e"] = a4e
        sys.modules["a4e.sdk"] = sdk

    if "autogen_agentchat" not in sys.modules:
        autogen = ModuleType("autogen_agentchat")
        agents = ModuleType("autogen_agentchat.agents")
        
        class AssistantAgent:
            pass
            
        agents.AssistantAgent = AssistantAgent
        autogen.agents = agents
        sys.modules["autogen_agentchat"] = autogen
        sys.modules["autogen_agentchat.agents"] = agents

def run_agent_server(agent_path: Path, port: int):
    """Run the agent in a FastMCP server with REST API endpoints"""
    from mcp.server.fastmcp import FastMCP
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse, Response
    from starlette.middleware.cors import CORSMiddleware
    import zipfile
    import io

    _mock_dependencies()

    agent_name = agent_path.name
    mcp = FastMCP(name=agent_name)

    # Load metadata
    metadata_path = agent_path / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())

    # Load tools schemas
    tools_schemas_path = agent_path / "tools" / "schemas.json"
    tools_schemas = []
    if tools_schemas_path.exists():
        tools_schemas = json.loads(tools_schemas_path.read_text())

    # Load widgets schemas
    widgets_schemas_path = agent_path / "widgets" / "schemas.json"
    widgets_schemas = {}
    if widgets_schemas_path.exists():
        widgets_schemas = json.loads(widgets_schemas_path.read_text())

    # Load system prompt
    prompt_path = agent_path / "prompts" / "agent.md"
    system_prompt = ""
    if prompt_path.exists():
        system_prompt = prompt_path.read_text()

    # Load agent tools into MCP AND store for direct execution
    loaded_tools: Dict[str, Callable] = {}
    tools_dir = agent_path / "tools"
    if tools_dir.exists():
        sys.path.insert(0, str(agent_path))
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name == "__init__.py":
                continue

            try:
                spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj):
                            if getattr(obj, "_is_tool", False) or name == tool_file.stem:
                                # Register with FastMCP
                                mcp.tool()(obj)
                                # ALSO store for direct execution in unified_stream
                                loaded_tools[name] = obj
                                print(f"Registered tool: {name}")
            except Exception as e:
                print(f"Failed to load tool {tool_file}: {e}")

    # Add system prompt resource
    @mcp.resource("agent://system_prompt")
    def get_system_prompt() -> str:
        return system_prompt or "You are a helpful assistant."

    # REST API Endpoints
    async def agent_info(request):
        return JSONResponse(metadata)

    async def get_tools(request):
        # Convert schema format to frontend expected format
        tools = []
        for schema in tools_schemas:
            params = []
            if "inputSchema" in schema and "properties" in schema["inputSchema"]:
                required = schema["inputSchema"].get("required", [])
                for param_name, param_info in schema["inputSchema"]["properties"].items():
                    params.append({
                        "name": param_name,
                        "type": param_info.get("type", "string"),
                        "description": param_info.get("description", ""),
                        "required": param_name in required
                    })
            tools.append({
                "name": schema.get("name", ""),
                "description": schema.get("description", ""),
                "parameters": params
            })
        return JSONResponse(tools)

    async def get_widgets(request):
        # Convert widgets schema to frontend expected format
        widgets = []
        for widget_id, widget_data in widgets_schemas.items():
            props = []
            if "params" in widget_data:
                for prop_name, prop_info in widget_data["params"].items():
                    props.append({
                        "name": prop_name,
                        "type": prop_info.get("type", "string"),
                        "required": True,  # Default to required
                        "description": prop_info.get("description", "")
                    })
            widgets.append({
                "id": widget_data.get("id", widget_id),
                "description": widget_data.get("description", ""),
                "props": props
            })
        return JSONResponse(widgets)

    async def get_widget_source(request):
        """Get source code for a specific widget"""
        widget_id = request.path_params["widget_id"]
        widget_file = agent_path / "widgets" / widget_id / "widget.tsx"
        
        if not widget_file.exists():
            return JSONResponse({"error": "Widget not found"}, status_code=404)
            
        return Response(
            content=widget_file.read_text(),
            media_type="text/plain"
        )

    async def download_source(request):
        """Download the entire agent source as a zip file"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(agent_path):
                for file in files:
                    # Skip __pycache__ and hidden files
                    if "__pycache__" in root or file.startswith("."):
                        continue
                        
                    file_path = os.path.join(root, file)
                    archive_name = os.path.relpath(file_path, agent_path)
                    zip_file.write(file_path, archive_name)
        
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{agent_name}.zip"'}
        )

    async def get_prompt(request):
        return JSONResponse({"prompt": system_prompt})

    async def unified_stream(request):
        """
        LLM-powered streaming endpoint for agent interaction.

        Flow:
        1. Parse request and extract session_id
        2. Load current draft from Supabase
        3. Call Claude API with context + tools
        4. Execute tool calls (save_rfs_draft)
        5. Stream response with widget updates from database state
        """
        from sse_starlette.sse import EventSourceResponse
        import asyncio

        try:
            payload = await request.json()
            print(f"\n{'='*60}")
            print(f"[unified_stream] 📥 RAW PAYLOAD: {json.dumps(payload, indent=2)[:500]}")
        except Exception as e:
            print(f"[unified_stream] ❌ Failed to parse JSON: {e}")
            payload = {}

        # Extract data from payload (frontend sends message directly, not in messages array)
        user_message = payload.get("message", "")
        metadata = payload.get("metadata", {})
        current_state = payload.get("currentState", {})

        # Get session_id - CRITICAL for Supabase persistence
        session_id = metadata.get("sessionId", f"anonymous_{int(time.time())}")
        print(f"[unified_stream] 📋 SESSION_ID: {session_id}")
        print(f"[unified_stream] 💬 MESSAGE: {user_message[:100] if user_message else 'EMPTY'}")

        # Fallback: check messages array format
        if not user_message:
            messages_array = payload.get("messages", [])
            if messages_array:
                last_msg = messages_array[-1]
                if isinstance(last_msg, dict):
                    user_message = last_msg.get("content", "")
                else:
                    user_message = str(last_msg)

        if not user_message:
            user_message = "Hello!"

        async def event_generator():
            try:
                # 1. Send initial status
                yield {
                    "data": json.dumps({
                        "type": "status",
                        "content": "Loading your draft..."
                    })
                }
                await asyncio.sleep(0.1)

                # 2. Load current draft from Supabase
                current_draft = {}
                get_draft_func = loaded_tools.get("get_rfs_draft")
                if get_draft_func:
                    try:
                        draft_result = get_draft_func(session_id=session_id)
                        if draft_result.get("success"):
                            current_draft = draft_result.get("draft", {})
                            print(f"[unified_stream] Loaded draft for session {session_id}: {current_draft}")
                    except Exception as e:
                        print(f"[unified_stream] Error loading draft: {e}")

                # 3. Update status
                yield {
                    "data": json.dumps({
                        "type": "status",
                        "content": "Thinking..."
                    })
                }

                # 4. Prepare Claude API call
                try:
                    client = get_anthropic_client()
                except ValueError as e:
                    # No API key configured
                    error_msg = str(e)
                    yield {"data": json.dumps({"type": "chat", "content": f"Configuration Error: {error_msg}", "complete": True})}
                    yield {"data": json.dumps({"type": "done", "content": "Stream complete"})}
                    yield {"data": "[DONE]"}
                    return

                # Determine which field is NEXT to fill
                next_field = None
                field_order = ["title", "problem_description", "industry", "budget_min", "timeline_months"]
                for field in field_order:
                    if not current_draft.get(field):
                        next_field = field
                        break

                # Build context with current draft state
                draft_context = f"""
## Current RFS Draft State
- Title: {current_draft.get('title') or '❌ EMPTY'}
- Problem Description: {current_draft.get('problem_description') or '❌ EMPTY'}
- Industry: {current_draft.get('industry') or '❌ EMPTY'}
- Budget Min: {current_draft.get('budget_min') or '❌ EMPTY'}
- Timeline (months): {current_draft.get('timeline_months') or '❌ EMPTY'}

## NEXT FIELD TO COLLECT: {next_field or 'ALL COMPLETE'}

## FIELD DEFINITIONS - READ CAREFULLY:
- **title**: The NAME of the project/startup idea. Examples: "Shopify competitor", "AI Writing Tool", "Food Delivery App", "Wix competitor". This is what the user wants to BUILD, not an industry category.
- **problem_description**: A description of the problem or opportunity. What pain point does this solve?
- **industry**: The sector/category like "E-commerce", "Fintech", "Healthcare", "SaaS", "EdTech"
- **budget_min**: The minimum budget in dollars (NUMBER ONLY, no currency symbols)
- **timeline_months**: How many months to complete (NUMBER ONLY)

## STRICT RULES:
1. When user says something like "wix competitor", "shopify competitor", "uber for X", "airbnb clone" → this is the TITLE, not an industry
2. When user mentions a sector like "e-commerce", "fintech", "healthcare" explicitly as the industry → this is INDUSTRY
3. ALWAYS fill fields in order: title → problem_description → industry → budget_min → timeline_months
4. The NEXT field to fill is: **{next_field}**
5. If user provides info for a later field, save it anyway, but still ask for missing earlier fields

## EXAMPLES:
- "wix competitor" → save as title="Wix competitor"
- "quiero hacer un competidor de shopify" → save as title="Competidor de Shopify"
- "la industria es e-commerce" → save as industry="E-commerce"
- "el problema es que las plataformas son muy caras" → save as problem_description="Las plataformas actuales son muy caras"
- "tengo $50000 de presupuesto" → save as budget_min=50000
- "necesito 6 meses" → save as timeline_months=6

## SESSION ID FOR ALL TOOL CALLS: {session_id}
"""

                full_system_prompt = f"{system_prompt}\n\n{draft_context}"

                # Define tools for Claude
                claude_tools = [
                    {
                        "name": "save_rfs_draft",
                        "description": "Save a single field to the RFS draft in Supabase. Call this IMMEDIATELY when the user provides any form data. The session_id is required.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "session_id": {
                                    "type": "string",
                                    "description": f"The user's session ID. Always use: {session_id}"
                                },
                                "field": {
                                    "type": "string",
                                    "description": "The field name to update",
                                    "enum": ["title", "problem_description", "industry", "budget_min", "budget_max", "timeline_months", "equity_offered", "equity_percentage"]
                                },
                                "value": {
                                    "description": "The value to save. Use string for text fields, number for numeric fields, boolean for equity_offered."
                                }
                            },
                            "required": ["session_id", "field", "value"]
                        }
                    }
                ]

                # Build messages for Claude
                claude_messages = [{"role": "user", "content": user_message}]

                # 5. Call Claude API
                print(f"[unified_stream] Calling Claude with message: {user_message[:100]}...")

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=full_system_prompt,
                    tools=claude_tools,
                    messages=claude_messages
                )

                # 6. Process the response - handle tool use loop
                response_text = ""
                final_draft = current_draft.copy()
                tool_results = []

                # Process content blocks
                for content_block in response.content:
                    if content_block.type == "text":
                        response_text = content_block.text
                    elif content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_id = content_block.id

                        print(f"[unified_stream] Tool call: {tool_name}({tool_input})")

                        # Execute the tool
                        tool_func = loaded_tools.get(tool_name)
                        if tool_func:
                            try:
                                # Ensure session_id is set
                                if "session_id" not in tool_input:
                                    tool_input["session_id"] = session_id

                                tool_result = tool_func(**tool_input)
                                print(f"[unified_stream] Tool result: {tool_result}")

                                # Update draft from result
                                if tool_result.get("success") and "draft" in tool_result:
                                    final_draft = tool_result["draft"]

                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": json.dumps(tool_result)
                                })
                            except Exception as e:
                                print(f"[unified_stream] Tool error: {e}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": json.dumps({"error": str(e)})
                                })

                # If there were tool calls, get a follow-up response
                if tool_results and response.stop_reason == "tool_use":
                    yield {
                        "data": json.dumps({
                            "type": "status",
                            "content": "Saving your data..."
                        })
                    }

                    # Continue conversation with tool results
                    continuation_messages = claude_messages + [
                        {"role": "assistant", "content": response.content},
                        {"role": "user", "content": tool_results}
                    ]

                    follow_up = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system=full_system_prompt,
                        tools=claude_tools,
                        messages=continuation_messages
                    )

                    # Get text from follow-up
                    for block in follow_up.content:
                        if block.type == "text":
                            response_text = block.text
                            break

                # 7. Stream the text response
                if response_text:
                    words = response_text.split(" ")
                    for i, word in enumerate(words):
                        yield {
                            "data": json.dumps({
                                "type": "chat",
                                "content": word + " ",
                                "complete": False
                            })
                        }
                        await asyncio.sleep(0.03)

                # 8. Complete chat
                yield {
                    "data": json.dumps({
                        "type": "chat",
                        "content": "",
                        "complete": True
                    })
                }

                # 9. Send status before widget
                yield {
                    "data": json.dumps({
                        "type": "status",
                        "content": "Reviewing response quality..."
                    })
                }
                await asyncio.sleep(0.1)

                # 10. ALWAYS fetch fresh state from Supabase before sending widget
                # This ensures we have ALL fields, not just what the tool returned
                fresh_draft = final_draft.copy()
                if get_draft_func:
                    try:
                        fresh_result = get_draft_func(session_id=session_id)
                        if fresh_result.get("success") and fresh_result.get("draft"):
                            fresh_draft = fresh_result["draft"]
                            print(f"[unified_stream] Fetched fresh draft from DB: {fresh_draft}")
                    except Exception as e:
                        print(f"[unified_stream] Error fetching fresh draft: {e}")

                widget_params = draft_to_widget_params(fresh_draft)
                print(f"\n{'='*60}")
                print(f"[unified_stream] 🎯 FINAL WIDGET PARAMS TO SEND:")
                print(f"  title: {widget_params.get('title')}")
                print(f"  problem_description: {widget_params.get('problem_description')}")
                print(f"  industry: {widget_params.get('industry')}")
                print(f"  budget_min: {widget_params.get('budget_min')}")
                print(f"  step: {widget_params.get('step')}")
                print(f"{'='*60}\n")

                yield {
                    "data": json.dumps({
                        "type": "widget",
                        "id": "rfs_form",
                        "params": widget_params
                    })
                }

                # 11. Done signal
                yield {
                    "data": json.dumps({
                        "type": "done",
                        "content": "Stream complete"
                    })
                }

                yield {"data": "[DONE]"}

            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}"
                print(f"[unified_stream] Exception: {traceback.format_exc()}")
                yield {"data": json.dumps({"type": "chat", "content": error_msg, "complete": True})}
                yield {"data": json.dumps({"type": "done", "content": "Stream complete with error"})}
                yield {"data": "[DONE]"}

        return EventSourceResponse(event_generator())

    print(f"Starting agent server on port {port}...")
    # FastMCP uses starlette/uvicorn internally for SSE
    import uvicorn
    
    # Get the SSE ASGI app from FastMCP
    sse_app = mcp.sse_app()

    # Create combined app with REST endpoints + MCP SSE
    app = Starlette(
        routes=[
            Route("/agent-info", agent_info),
            Route("/tools", get_tools),
            Route("/widgets", get_widgets),
            Route("/widgets/{widget_id}/source", get_widget_source),
            Route("/system-prompt", get_prompt),
            Route("/download", download_source),
            Route("/api/agents/{agent_name}/unified-stream", unified_stream, methods=["POST"]),
            Mount("/", sse_app),  # Mount MCP SSE at root
        ]
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Run uvicorn directly with our port
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-path", required=True, help="Path to agent directory")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    args = parser.parse_args()
    
    run_agent_server(Path(args.agent_path), args.port)

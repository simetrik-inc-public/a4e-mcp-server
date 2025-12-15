import sys
import os
import importlib.util
import inspect
import json
import argparse
from pathlib import Path
from types import ModuleType
from typing import Any, Optional


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

    # Load views schemas
    views_schemas_path = agent_path / "views" / "schemas.json"
    views_schemas = {}
    if views_schemas_path.exists():
        views_schemas = json.loads(views_schemas_path.read_text())

    # Load system prompt
    prompt_path = agent_path / "prompts" / "agent.md"
    system_prompt = ""
    if prompt_path.exists():
        system_prompt = prompt_path.read_text()

    # Load agent tools into MCP
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
                            if (
                                getattr(obj, "_is_tool", False)
                                or name == tool_file.stem
                            ):
                                # Register with FastMCP
                                mcp.tool()(obj)
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
                for param_name, param_info in schema["inputSchema"][
                    "properties"
                ].items():
                    params.append(
                        {
                            "name": param_name,
                            "type": param_info.get("type", "string"),
                            "description": param_info.get("description", ""),
                            "required": param_name in required,
                        }
                    )
            tools.append(
                {
                    "name": schema.get("name", ""),
                    "description": schema.get("description", ""),
                    "parameters": params,
                }
            )
        return JSONResponse(tools)

    async def get_views(request):
        # Convert views schema to frontend expected format
        views = []
        for view_id, view_data in views_schemas.items():
            props = []
            if "params" in view_data:
                for prop_name, prop_info in view_data["params"].items():
                    props.append(
                        {
                            "name": prop_name,
                            "type": prop_info.get("type", "string"),
                            "required": True,  # Default to required
                            "description": prop_info.get("description", ""),
                        }
                    )
            views.append(
                {
                    "id": view_data.get("id", view_id),
                    "description": view_data.get("description", ""),
                    "props": props,
                }
            )
        return JSONResponse(views)

    async def get_view_source(request):
        """Get source code for a specific view"""
        view_id = request.path_params["view_id"]
        view_file = agent_path / "views" / view_id / "view.tsx"

        if not view_file.exists():
            return JSONResponse({"error": "View not found"}, status_code=404)

        return Response(content=view_file.read_text(), media_type="text/plain")

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
            headers={"Content-Disposition": f'attachment; filename="{agent_name}.zip"'},
        )

    async def get_prompt(request):
        return JSONResponse({"prompt": system_prompt})

    async def unified_stream(request):
        from sse_starlette.sse import EventSourceResponse
        import asyncio
        import json

        try:
            payload = await request.json()
        except:
            payload = {}

        # Extract last user message
        messages = payload.get("messages", [])
        last_message = "Hello!"
        if messages:
            last_message = messages[-1].get("content", "")

        async def event_generator():
            # Simulate thinking delay
            await asyncio.sleep(0.5)

            # 1. Send status
            yield {
                "data": json.dumps(
                    {"type": "status", "content": "Processing request..."}
                )
            }
            await asyncio.sleep(0.5)

            # 2. Stream text response
            response_text = f"I received your message: '{last_message}'. I am running in Dev Mode via MCP!"

            # Split into chunks
            words = response_text.split(" ")
            for word in words:
                yield {
                    "data": json.dumps(
                        {"type": "chat", "content": word + " ", "complete": False}
                    )
                }
                await asyncio.sleep(0.1)

            # 3. Complete chat
            yield {
                "data": json.dumps({"type": "chat", "content": "", "complete": True})
            }

            # 4. Done signal
            yield {"data": json.dumps({"type": "done", "content": "Stream complete"})}

            # SSE Done
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
            Route("/views", get_views),
            Route("/views/{view_id}/source", get_view_source),
            Route("/system-prompt", get_prompt),
            Route("/download", download_source),
            Route(
                "/api/agents/{agent_name}/unified-stream",
                unified_stream,
                methods=["POST"],
            ),
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

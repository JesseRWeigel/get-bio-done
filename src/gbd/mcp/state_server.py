"""gbd-state MCP server — Project state queries.

Exposes tools for reading and modifying GBD project state,
including phases, decisions, results, and metrics.
"""

from __future__ import annotations

import json
import asyncio
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from gbd.core.constants import get_layout
from gbd.core.state import StateEngine

server = Server("gbd-state")


def _engine(project_dir: str | None = None) -> StateEngine:
    if project_dir:
        from gbd.core.constants import ProjectLayout
        return StateEngine(ProjectLayout(root=Path(project_dir)))
    return StateEngine(get_layout())


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_project_state",
            description="Get the full project state including phases, conventions, decisions, and metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project root directory (optional, auto-detected if omitted)"},
                },
            },
        ),
        Tool(
            name="get_current_phase",
            description="Get the current active phase and plan.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_decisions",
            description="Get the decision log, optionally filtered by phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "phase": {"type": "string", "description": "Filter decisions by phase ID"},
                    "limit": {"type": "integer", "description": "Max number of recent decisions to return"},
                },
            },
        ),
        Tool(
            name="get_result",
            description="Retrieve an intermediate result stored for cross-phase access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "key": {"type": "string", "description": "Result key to look up"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="set_result",
            description="Store an intermediate result for cross-phase access.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "key": {"type": "string", "description": "Result key"},
                    "value": {"description": "Result value (any JSON-serializable type)"},
                },
                "required": ["key", "value"],
            },
        ),
        Tool(
            name="add_decision",
            description="Record a research decision with rationale.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "phase": {"type": "string", "description": "Phase ID this decision belongs to"},
                    "decision": {"type": "string", "description": "What was decided"},
                    "rationale": {"type": "string", "description": "Why this was decided"},
                    "agent": {"type": "string", "description": "Which agent made the decision"},
                },
                "required": ["phase", "decision", "rationale"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    project_dir = arguments.get("project_dir")
    engine = _engine(project_dir)

    if name == "get_project_state":
        state = engine.load()
        return [TextContent(type="text", text=json.dumps(state.model_dump(mode="json"), indent=2))]

    elif name == "get_current_phase":
        state = engine.load()
        phase_info = {
            "current_phase": state.current_phase,
            "current_plan": state.current_plan,
            "current_milestone": state.current_milestone,
        }
        if state.current_phase and state.current_phase in state.phases:
            phase_info["phase_detail"] = state.phases[state.current_phase].model_dump(mode="json")
        return [TextContent(type="text", text=json.dumps(phase_info, indent=2))]

    elif name == "get_decisions":
        state = engine.load()
        decisions = [d.model_dump(mode="json") for d in state.decisions]
        phase_filter = arguments.get("phase")
        if phase_filter:
            decisions = [d for d in decisions if d["phase"] == phase_filter]
        limit = arguments.get("limit")
        if limit:
            decisions = decisions[-limit:]
        return [TextContent(type="text", text=json.dumps(decisions, indent=2))]

    elif name == "get_result":
        value = engine.get_result(arguments["key"])
        return [TextContent(type="text", text=json.dumps({"key": arguments["key"], "value": value}))]

    elif name == "set_result":
        engine.set_result(arguments["key"], arguments["value"])
        return [TextContent(type="text", text=json.dumps({"status": "ok", "key": arguments["key"]}))]

    elif name == "add_decision":
        engine.add_decision(
            phase=arguments["phase"],
            decision=arguments["decision"],
            rationale=arguments["rationale"],
            agent=arguments.get("agent", ""),
        )
        return [TextContent(type="text", text=json.dumps({"status": "ok", "decision": arguments["decision"]}))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

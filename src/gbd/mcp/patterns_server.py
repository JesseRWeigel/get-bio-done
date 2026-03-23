"""gbd-patterns MCP server — Cross-project learned patterns.

Stores and retrieves patterns learned from completed research projects:
successful pipelines, common pitfalls, performance benchmarks, and
reusable workflow templates for bioinformatics.
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("gbd-patterns")

PATTERNS_DIR = Path(__file__).resolve().parents[1] / "specs" / "references"
KNOWLEDGE_PATTERN = "patterns.json"


def _patterns_path(project_dir: str | None = None) -> Path:
    if project_dir:
        return Path(project_dir) / "knowledge" / KNOWLEDGE_PATTERN
    return PATTERNS_DIR / KNOWLEDGE_PATTERN


def _load_patterns(project_dir: str | None = None) -> list[dict]:
    path = _patterns_path(project_dir)
    if path.exists():
        return json.loads(path.read_text())
    return []


def _save_patterns(patterns: list[dict], project_dir: str | None = None) -> None:
    path = _patterns_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(patterns, indent=2))


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_patterns",
            description="List all learned patterns, optionally filtered by category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "category": {
                        "type": "string",
                        "description": "Filter by category",
                        "enum": ["methodology", "pitfall", "performance", "workflow", "tooling"],
                    },
                },
            },
        ),
        Tool(
            name="add_pattern",
            description="Record a new learned pattern from a completed project or phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "title": {"type": "string", "description": "Short title for the pattern"},
                    "category": {
                        "type": "string",
                        "enum": ["methodology", "pitfall", "performance", "workflow", "tooling"],
                    },
                    "description": {"type": "string", "description": "What was learned"},
                    "context": {"type": "string", "description": "Data type / analysis where this applies"},
                    "recommendation": {"type": "string", "description": "What to do next time"},
                    "source_project": {"type": "string", "description": "Which project this came from"},
                },
                "required": ["title", "category", "description", "recommendation"],
            },
        ),
        Tool(
            name="search_patterns",
            description="Search patterns by keyword to find relevant past experience.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "query": {"type": "string", "description": "Search term"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_patterns_for_method",
            description="Get patterns relevant to a specific analysis type (RNA-seq, WGS, scRNA-seq, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "method": {"type": "string", "description": "Analysis type (e.g., 'RNA-seq', 'WGS', 'scRNA-seq', 'ChIP-seq')"},
                },
                "required": ["method"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    project_dir = arguments.get("project_dir")

    if name == "list_patterns":
        patterns = _load_patterns(project_dir)
        category = arguments.get("category")
        if category:
            patterns = [p for p in patterns if p.get("category") == category]
        return [TextContent(type="text", text=json.dumps(patterns, indent=2))]

    elif name == "add_pattern":
        patterns = _load_patterns(project_dir)
        new_pattern = {
            "id": f"PAT-{len(patterns) + 1:03d}",
            "title": arguments["title"],
            "category": arguments["category"],
            "description": arguments["description"],
            "context": arguments.get("context", ""),
            "recommendation": arguments["recommendation"],
            "source_project": arguments.get("source_project", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        patterns.append(new_pattern)
        _save_patterns(patterns, project_dir)
        return [TextContent(type="text", text=json.dumps({"status": "ok", "pattern": new_pattern}, indent=2))]

    elif name == "search_patterns":
        patterns = _load_patterns(project_dir)
        query = arguments["query"].lower()
        matches = [
            p for p in patterns
            if query in p.get("title", "").lower()
            or query in p.get("description", "").lower()
            or query in p.get("context", "").lower()
            or query in p.get("recommendation", "").lower()
        ]
        return [TextContent(type="text", text=json.dumps(matches, indent=2))]

    elif name == "get_patterns_for_method":
        patterns = _load_patterns(project_dir)
        method = arguments["method"].lower()
        matches = [
            p for p in patterns
            if method in p.get("title", "").lower()
            or method in p.get("description", "").lower()
            or method in p.get("context", "").lower()
        ]
        return [TextContent(type="text", text=json.dumps(matches, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

"""gbd-protocols MCP server — Bioinformatics methodology protocols.

Provides access to step-by-step methodology guides for bioinformatics
workflows: RNA-seq, WGS, variant calling, scRNA-seq, ChIP-seq, etc.
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

server = Server("gbd-protocols")

PROTOCOLS_DIR = Path(__file__).resolve().parents[1] / "specs" / "references" / "protocols"


def _list_protocols() -> list[dict]:
    """Discover all protocol markdown files."""
    protocols = []
    if PROTOCOLS_DIR.exists():
        for f in sorted(PROTOCOLS_DIR.glob("*.md")):
            protocols.append({
                "id": f.stem,
                "filename": f.name,
                "path": str(f),
            })
    return protocols


def _read_protocol(protocol_id: str) -> str | None:
    """Read a protocol file by its stem name."""
    path = PROTOCOLS_DIR / f"{protocol_id}.md"
    if path.exists():
        return path.read_text()
    return None


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_protocols",
            description="List all available bioinformatics methodology protocols (RNA-seq, WGS, variant calling, scRNA-seq, etc.).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_protocol",
            description="Get the full text of a specific bioinformatics methodology protocol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "protocol_id": {
                        "type": "string",
                        "description": "Protocol identifier (stem of the .md file, e.g. 'rnaseq-protocols', 'variant-calling-protocols')",
                    },
                },
                "required": ["protocol_id"],
            },
        ),
        Tool(
            name="search_protocols",
            description="Search protocol files for a keyword or phrase. Returns matching sections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term or phrase"},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_protocols":
        return [TextContent(type="text", text=json.dumps(_list_protocols(), indent=2))]

    elif name == "get_protocol":
        content = _read_protocol(arguments["protocol_id"])
        if content is None:
            available = [p["id"] for p in _list_protocols()]
            return [TextContent(type="text", text=json.dumps({
                "error": f"Protocol '{arguments['protocol_id']}' not found",
                "available": available,
            }))]
        return [TextContent(type="text", text=content)]

    elif name == "search_protocols":
        query = arguments["query"].lower()
        matches = []
        for proto in _list_protocols():
            content = Path(proto["path"]).read_text()
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if query in line.lower():
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    matches.append({
                        "protocol": proto["id"],
                        "line": i + 1,
                        "context": "\n".join(lines[start:end]),
                    })
        return [TextContent(type="text", text=json.dumps(matches, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

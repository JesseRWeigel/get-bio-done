"""gbd-conventions MCP server — Pipeline parameter lock management.

Manages convention locks that ensure bioinformatics pipeline parameters
(reference genome, aligner, variant caller, significance thresholds, etc.)
stay consistent across all phases of a research project.
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

from gbd.core.constants import get_layout, ProjectLayout, CONVENTION_FIELDS
from gbd.core.state import StateEngine
from gbd.core.conventions import (
    list_all_fields,
    check_conventions,
    diff_conventions,
    get_field_description,
    get_field_examples,
)

server = Server("gbd-conventions")


def _engine(project_dir: str | None = None) -> StateEngine:
    if project_dir:
        return StateEngine(ProjectLayout(root=Path(project_dir)))
    return StateEngine(get_layout())


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_convention_fields",
            description="List all convention lock fields with descriptions and examples. Fields: reference_genome, gene_annotation_source, aligner, variant_caller, significance_threshold, multiple_testing_correction, normalization_method, quality_thresholds, filtering_criteria, container_env_versions.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="check_conventions",
            description="Check which conventions are locked and which are still unlocked. Returns coverage stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_convention",
            description="Get the current locked value for a specific convention field.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "field": {"type": "string", "description": "Convention field name", "enum": CONVENTION_FIELDS},
                },
                "required": ["field"],
            },
        ),
        Tool(
            name="set_convention",
            description="Lock a convention field to a specific value. Once locked, any change is flagged as a conflict.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "field": {"type": "string", "enum": CONVENTION_FIELDS},
                    "value": {"type": "string", "description": "The value to lock"},
                    "locked_by": {"type": "string", "description": "Phase/plan that is locking this field"},
                    "rationale": {"type": "string", "description": "Why this value was chosen"},
                },
                "required": ["field", "value", "locked_by"],
            },
        ),
        Tool(
            name="diff_conventions",
            description="Compare proposed convention values against current locks. Identifies conflicts, new fields, and matches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "proposed": {
                        "type": "object",
                        "description": "Map of field name to proposed value",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["proposed"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_convention_fields":
        return [TextContent(type="text", text=json.dumps(list_all_fields(), indent=2))]

    project_dir = arguments.get("project_dir")
    engine = _engine(project_dir)

    if name == "check_conventions":
        report = check_conventions(engine)
        return [TextContent(type="text", text=json.dumps(report, indent=2))]

    elif name == "get_convention":
        state = engine.load()
        field = arguments["field"]
        lock = state.conventions.get(field)
        if lock:
            result = {
                "field": field,
                "value": lock.value,
                "locked_by": lock.locked_by,
                "locked_at": lock.locked_at,
                "rationale": lock.rationale,
            }
        else:
            result = {
                "field": field,
                "value": None,
                "description": get_field_description(field),
                "examples": get_field_examples(field),
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "set_convention":
        engine.set_convention(
            field=arguments["field"],
            value=arguments["value"],
            locked_by=arguments["locked_by"],
            rationale=arguments.get("rationale", ""),
        )
        return [TextContent(type="text", text=json.dumps({"status": "ok", "field": arguments["field"], "value": arguments["value"]}))]

    elif name == "diff_conventions":
        report = diff_conventions(engine, arguments["proposed"])
        return [TextContent(type="text", text=json.dumps(report, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

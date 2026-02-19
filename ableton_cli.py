#!/usr/bin/env python3
"""
ableton_cli.py — Direct CLI for calling Ableton MCP tools from the terminal.

Usage:
    uv run --directory /path/to/ableton-mcp python ableton_cli.py TOOL_NAME [JSON_ARGS]

Examples:
    python ableton_cli.py get_tempo
    python ableton_cli.py set_tempo '{"bpm": 120}'
    python ableton_cli.py discover_all_tracks
    python ableton_cli.py fire_clip '{"track_index": 0, "clip_index": 0}'
    python ableton_cli.py load_device '{"track_number": 1, "device_name": "Auto Filter"}'
    python ableton_cli.py ramp_volume '{"track_index": 0, "start_volume": 0, "end_volume": 0.85, "beats": 4, "bpm": 90}'
"""

import json
import sys

from ableton_mcp.server import mcp


def main():
    if len(sys.argv) < 2:
        print("Usage: python ableton_cli.py TOOL_NAME [JSON_ARGS]")
        print("\nAvailable tools:")
        for name in sorted(mcp._tool_manager._tools.keys()):
            print(f"  {name}")
        sys.exit(1)

    tool_name = sys.argv[1]

    if tool_name == "--list":
        for name in sorted(mcp._tool_manager._tools.keys()):
            print(name)
        sys.exit(0)

    args = {}
    if len(sys.argv) > 2:
        args = json.loads(sys.argv[2])

    # Get the tool function directly
    tool = mcp._tool_manager._tools.get(tool_name)
    if not tool:
        print(f"Unknown tool: {tool_name}")
        print(f"Use --list to see available tools")
        sys.exit(1)

    # Call the tool function
    result = tool.fn(**args)
    print(result)


if __name__ == "__main__":
    main()

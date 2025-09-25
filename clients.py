#!/usr/bin/env python3
"""
MCP Client for Esri Living Atlas Tools

This script provides a command-line interface to interact with the Esri Living Atlas MCP server.
It can list available tools and call them with provided parameters.

Usage:
    python clients.py list-tools
    python clients.py call-tool <tool_name> <param1> <value1> <param2> <value2> ...

Example:
    python clients.py call-tool query_layer layer_name usgs-gauges where "state = 'MI'" return_count_only true
"""

import asyncio
import sys
import json
from fastmcp import Client
import httpx


async def list_tools(server_url):
    """List all available tools from the MCP server."""
    try:
        async with Client(server_url) as client:
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Error listing tools: {e}")


async def call_tool(server_url, tool_name, **kwargs):
    """Call a specific tool with parameters."""
    try:
        async with Client(server_url) as client:
            result = await client.call_tool(tool_name, kwargs)
            print("Tool result:")
            print(json.dumps(result.structured_content, indent=2))
    except Exception as e:
        print(f"Error calling tool: {e}")


def parse_args():
    """Parse command-line arguments."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list-tools":
        return command, {}
    elif command == "call-tool":
        if len(sys.argv) < 3:
            print("Usage: python clients.py call-tool <tool_name> [param value ...]")
            sys.exit(1)
        tool_name = sys.argv[2]
        params = {}
        i = 3
        while i < len(sys.argv) - 1:
            key = sys.argv[i]
            value = sys.argv[i + 1]
            # Try to parse as JSON, otherwise keep as string
            try:
                params[key] = json.loads(value)
            except json.JSONDecodeError:
                params[key] = value
            i += 2
        return command, {"tool_name": tool_name, "params": params}
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


async def main():
    server_url = "http://localhost:8000/mcp"

    command, args = parse_args()

    if command == "list-tools":
        await list_tools(server_url)
    elif command == "call-tool":
        await call_tool(server_url, args["tool_name"], **args["params"])


if __name__ == "__main__":
    asyncio.run(main())
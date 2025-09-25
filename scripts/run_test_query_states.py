import asyncio
from fastmcp import Client
import httpx
import json

async def run_test():
    http_server_url = "http://localhost:8000/mcp"
    print(f"Attempting to connect to FastMCP server at {http_server_url}")
    try:
        async with Client(http_server_url) as client:
            print("Successfully connected to FastMCP server.")
            
            print("Calling query_layer tool for states layer...")
            result = await client.call_tool("query_layer", {"layer_name": "states", "where": "1=1", "out_fields": "STATE_NAME"})
            print("Query states layer result:")
            print(result.structured_content)
            assert "features" in result.structured_content
            assert len(result.structured_content["features"]) > 0
            print("Test query states layer passed!")

            print("\nCalling get_layer_fields tool for states layer...")
            fields_result = await client.call_tool("get_layer_fields", {"layer_name": "states"})
            print("Get layer fields result:")
            print(fields_result.structured_content)
            assert "fields" in fields_result.structured_content
            assert len(fields_result.structured_content["fields"]) > 0
            print("Test get_layer_fields passed!")

            print("\nCalling get_state_geometry tool for Michigan...")
            geometry_result = await client.call_tool("get_state_geometry", {"state_name": "Michigan"})
            print("Get state geometry result:")
            print(geometry_result.structured_content)
            assert "rings" in geometry_result.structured_content or "x" in geometry_result.structured_content # Geometry can be polygon or point
            print("Test get_state_geometry passed!")

    except httpx.ConnectError as e:
        print(f"Connection Error: Could not connect to the server. Is it running? {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())

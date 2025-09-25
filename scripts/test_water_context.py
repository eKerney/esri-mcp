import asyncio
from fastmcp import Client
import httpx

async def main():
    http_server_url = "http://localhost:8000/mcp"
    try:
        async with Client(http_server_url) as client:
            result = await client.call_tool("create_water_map_context", {"geojson_path": "/Users/erickerney/dev/ai/esri-mcp/virginia_usgs.geojson"})
            print(result.structured_content)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
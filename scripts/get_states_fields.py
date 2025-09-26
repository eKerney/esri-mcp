import asyncio
from fastmcp import Client
import httpx

async def main():
    http_server_url = "http://localhost:8000/mcp"
    try:
        async with Client(http_server_url) as client:
            result = await client.call_tool("get_layer_fields", {"layer_name": "states"})
            print(result.structured_content)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
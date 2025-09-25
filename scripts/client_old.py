import asyncio
from fastmcp import Client
import httpx
import json

async def main():
    http_server_url = "http://localhost:8000/mcp"
    print(f"Attempting to connect to FastMCP server at {http_server_url}")
    try:
        async with Client(http_server_url) as client:
            print("Successfully connected to FastMCP server.")
            
            print("Calling get_state_geometry tool for Michigan...")
            michigan_geometry_result = await client.call_tool("get_state_geometry", {"state_name": "Michigan"})
            michigan_geometry = michigan_geometry_result.structured_content
            print("get_state_geometry tool call successful.")
            print(f"Michigan Geometry: {michigan_geometry}")

            if "error" in michigan_geometry:
                print(f"Error getting Michigan geometry: {michigan_geometry['error']}")
                return

            print("Calling query_layer tool for usgs-gauges with Michigan geometry...")
            # Convert the geometry dictionary to a JSON string for the spatial_filter parameter
            spatial_filter_str = json.dumps(michigan_geometry)
            usgs_stations_count_result = await client.call_tool(
                "query_layer",
                {
                    "layer_name": "usgs-gauges",
                    "spatial_filter": spatial_filter_str,
                    "return_count_only": True
                }
            )
            usgs_stations_count = usgs_stations_count_result.structured_content
            print("query_layer tool call successful.")
            
            # Only print the count
            if "count" in usgs_stations_count:
                print(f"USGS Stations in Michigan: {usgs_stations_count['count']}")
            else:
                print(f"USGS Stations in Michigan: {usgs_stations_count}")

    except httpx.ConnectError as e:
        print(f"Connection Error: Could not connect to the server. Is it running? {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

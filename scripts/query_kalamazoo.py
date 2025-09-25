import asyncio
from fastmcp import Client
import httpx
import json

def get_envelope(geometry):
    rings = geometry.get("rings", [])
    all_points = [point for ring in rings for point in ring]
    if not all_points:
        return None
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys)}

async def main():
    http_server_url = "http://localhost:8000/mcp"
    print(f"Attempting to connect to FastMCP server at {http_server_url}")
    try:
        async with Client(http_server_url) as client:
            print("Successfully connected to FastMCP server.")
            
            print("Calling query_layer tool for Kalamazoo County geometry...")
            kalamazoo_result = await client.call_tool("query_layer", {
                "layer_name": "counties",
                "where": "NAME = 'Kalamazoo' AND STATEFP = '26'",
                "out_fields": "",
                "return_geometry": True
            })
            kalamazoo_data = kalamazoo_result.structured_content
            print("query_layer tool call successful for Kalamazoo County.")
            
            if "features" in kalamazoo_data and kalamazoo_data["features"]:
                kalamazoo_geometry = kalamazoo_data["features"][0]["geometry"]
                print("Kalamazoo County geometry retrieved.")
                envelope = get_envelope(kalamazoo_geometry)
                if not envelope:
                    print("Error: Could not compute envelope.")
                    return
                print(f"Envelope: {envelope}")
            else:
                print(f"Error: No geometry found for Kalamazoo County. Response: {kalamazoo_data}")
                return

            print("Calling query_layer tool for usgs-gauges with Kalamazoo County envelope...")
            spatial_filter_str = json.dumps(envelope)
            usgs_result = await client.call_tool(
                "query_layer",
                {
                    "layer_name": "usgs-gauges",
                    "spatial_filter": spatial_filter_str,
                    "return_count_only": True
                }
            )
            usgs_data = usgs_result.structured_content
            print("query_layer tool call successful for USGS gauges.")
            
            if "count" in usgs_data:
                print(f"USGS Stations in Kalamazoo County, Michigan: {usgs_data['count']}")
            else:
                print(f"USGS Stations in Kalamazoo County, Michigan: {usgs_data}")

    except httpx.ConnectError as e:
        print(f"Connection Error: Could not connect to the server. Is it running? {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
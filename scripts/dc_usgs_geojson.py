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
            
            print("Calling query_layer tool for usgs-gauges in Washington DC...")
            usgs_result = await client.call_tool(
                "query_layer",
                {
                    "layer_name": "usgs-gauges",
                    "where": "state = 'DC'",
                    "out_fields": "*",
                    "return_geometry": True
                }
            )
            usgs_data = usgs_result.structured_content
            print("query_layer tool call successful for USGS gauges.")
            
            if "features" in usgs_data:
                features = usgs_data["features"]
                geojson_features = []
                for feature in features:
                    attrs = feature.get("attributes", {})
                    lat = attrs.get("latitude")
                    lon = attrs.get("longitude")
                    if lat is not None and lon is not None:
                        geojson_feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": attrs
                        }
                        geojson_features.append(geojson_feature)
                
                geojson = {
                    "type": "FeatureCollection",
                    "features": geojson_features
                }
                
                geojson_path = "/Users/erickerney/dev/ai/esri-mcp/dc_usgs.geojson"
                with open(geojson_path, "w") as f:
                    json.dump(geojson, f, indent=2)
                
                print(f"GeoJSON file created: dc_usgs.geojson with {len(geojson_features)} features")
                
                # Now display it
                print("Calling display_geojson tool...")
                display_result = await client.call_tool("display_geojson", {"geojson_path": geojson_path})
                print(display_result.structured_content)
            else:
                print(f"Error: No features found. Response: {usgs_data}")

    except httpx.ConnectError as e:
        print(f"Connection Error: Could not connect to the server. Is it running? {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
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
            
            print("Calling query_layer tool for Wayne County geometry...")
            wayne_result = await client.call_tool("query_layer", {
                "layer_name": "counties",
                "where": "NAME = 'Wayne' AND STATEFP = '26'",
                "out_fields": "",
                "return_geometry": True
            })
            wayne_data = wayne_result.structured_content
            print("query_layer tool call successful for Wayne County.")
            
            if "features" in wayne_data and wayne_data["features"]:
                wayne_geometry = wayne_data["features"][0]["geometry"]
                print("Wayne County geometry retrieved.")
                envelope = get_envelope(wayne_geometry)
                if not envelope:
                    print("Error: Could not compute envelope.")
                    return
                print(f"Envelope: {envelope}")
            else:
                print(f"Error: No geometry found for Wayne County. Response: {wayne_data}")
                return

            xmin, ymin, xmax, ymax = envelope['xmin'], envelope['ymin'], envelope['xmax'], envelope['ymax']
            where_clause = f"latitude >= {ymin} AND latitude <= {ymax} AND longitude >= {xmin} AND longitude <= {xmax}"
            
            print("Calling query_layer tool for usgs-gauges in Wayne County...")
            usgs_result = await client.call_tool(
                "query_layer",
                {
                    "layer_name": "usgs-gauges",
                    "where": where_clause,
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
                
                with open("/Users/erickerney/dev/ai/esri-mcp/wayne_usgs.geojson", "w") as f:
                    json.dump(geojson, f, indent=2)
                
                print(f"GeoJSON file created: wayne_usgs.geojson with {len(geojson_features)} features")
            else:
                print(f"Error: No features found. Response: {usgs_data}")

    except httpx.ConnectError as e:
        print(f"Connection Error: Could not connect to the server. Is it running? {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
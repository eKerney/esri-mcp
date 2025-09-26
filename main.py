from fastmcp import FastMCP
import requests
import json
import urllib.parse
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastMCP(name="Esri Living Atlas")

# Add CORS middleware for web app access
app.http_app().add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAYER_MAPPING = {
    "states": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized_Boundaries/FeatureServer/0",
    "counties": "https://services4.arcgis.com/QdHwhlbx61LR3TWb/arcgis/rest/services/US_Counties/FeatureServer/0",
    "usgs-gauges": "https://mapservices.weather.noaa.gov/eventdriven/rest/services/water/riv_gauges/MapServer/0",
    "rivers": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Rivers_and_Streams/FeatureServer/0",
    "dams": "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/NID_v1/FeatureServer/0",
    "watersheds": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Watershed_Boundary_Dataset/FeatureServer/0",
    "impaired-waters": "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/EPA_Impaired_Waters_Y2025Q3/FeatureServer/1",
    "water-quality": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Water_Quality_Monitoring_Stations/FeatureServer/0",
    "sample-points": "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Census/MapServer/0" # New sample layer
}

app.http_app().add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # Allows all origins for dev (use r"http://localhost:5173.*" for specific)
    allow_credentials=True,
    allow_methods=["*"],  # Allows OPTIONS, POST, etc.
    allow_headers=["*"],  # Covers Content-Type, Accept, X-Session-ID, Authorization
)

@app.tool()
def query_layer(layer_name: str, where: str = "1=1", out_fields: str = "*", return_count_only: bool = False, spatial_filter: Optional[str] = None, return_geometry: bool = False) -> dict:
    """
    Queries a feature layer from the Esri Living Atlas.

    :param layer_name: The name of the layer to query. Available layers: states, counties, usgs-gauges, rivers, dams, watersheds, impaired-waters, water-quality, sample-points.
    :param where: The WHERE clause for the query. Use field names like 'state' for usgs-gauges (e.g., "state = 'MI'"), 'STATE_NAME' for states (e.g., "STATE_NAME = 'Michigan'"), 'State' for rivers (e.g., "State = 'VA'"), etc. Default is "1=1" for all features.
    :param out_fields: Comma-separated list of fields to return (e.g., "NAME,STATE"). Use "*" for all fields.
    :param return_count_only: Set to true to return only the feature count, not the data.
    :param spatial_filter: A spatial filter in Esri JSON format (optional).
    :param return_geometry: Set to true to include geometry in the response.

    Examples:
    - Count USGS gages in Michigan: layer_name="usgs-gauges", where="state = 'MI'", return_count_only=true
    - Get state boundaries: layer_name="states", where="STATE_NAME = 'Michigan'", return_geometry=true
    - Query rivers in Virginia: layer_name="rivers", where="State = 'VA'"

    :return: The JSON response from the server, or {"error": "message"} if failed.
    """
    if layer_name not in LAYER_MAPPING:
        return {"error": f"Invalid layer name: {layer_name}. Available layers: {list(LAYER_MAPPING.keys())}"}

    layer_url = LAYER_MAPPING[layer_name]
    
    # Always include f=json as a query parameter
    query_url = f"{layer_url}/query?f=json"

    headers = {"Accept": "application/json"}

    params = {
        "where": where,
        "outFields": out_fields,
        "returnCountOnly": str(return_count_only).lower()
    }
    if return_geometry:
        params["returnGeometry"] = "true"
    if spatial_filter:
        # Parse the JSON string for geometry
        geometry_obj = json.loads(spatial_filter)
        if "rings" in geometry_obj:
            # Polygon
            params["geometry"] = urllib.parse.quote(spatial_filter)
            params["geometryType"] = "esriGeometryPolygon"
        else:
            # Envelope
            params["geometry"] = f"{geometry_obj['xmin']},{geometry_obj['ymin']},{geometry_obj['xmax']},{geometry_obj['ymax']}"
            params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"
    response = requests.post(query_url, data=params, headers=headers, timeout=30)

    response.raise_for_status()
    return response.json()

@app.tool()
def get_layer_fields(layer_name: str) -> dict:
    """
    Gets the fields of a feature layer from the Esri Living Atlas.

    :param layer_name: The name of the layer to get fields from. Available layers: states, counties, usgs-gauges, sample-points.
    :return: The JSON response from the server.
    """
    if layer_name not in LAYER_MAPPING:
        return {"error": f"Invalid layer name: {layer_name}. Available layers: {list(LAYER_MAPPING.keys())}"}

    layer_url = LAYER_MAPPING[layer_name]
    params = {
        "f": "json"
    }
    response = requests.get(layer_url, params=params, timeout=30)
    print(f"Raw response for {layer_name}: {response.text}")
    response.raise_for_status()
    return {"fields": response.json().get("fields", [])}

@app.tool()
def get_state_geometry(state_name: str) -> dict:
    """
    Gets the geometry of a state from the 'states' layer.

    :param state_name: The name of the state (e.g., "Michigan").
    :return: The geometry of the state in Esri JSON format.
    """
    states_layer_url = LAYER_MAPPING["states"]
    where_clause = f"STATE_NAME = \'{state_name}\'"
    params = {
        "where": where_clause,
        "outFields": "",
        "returnGeometry": "true",
        "f": "json"
    }
    response = requests.get(f"{states_layer_url}/query", params=params, timeout=30)
    response.raise_for_status()
    features = response.json().get("features", [])
    if features:
        return features[0]["geometry"]
    return {"error": f"State \'{state_name}\' not found or has no geometry."}

@app.tool()
def query_geojson(layer_name: str, where: str = "1=1", out_fields: str = "*", limit: int = 1000) -> str:
    """
    Queries a feature layer and returns the results as a GeoJSON string.

    :param layer_name: The name of the layer to query. Available layers: states, counties, usgs-gauges, rivers, dams, watersheds, impaired-waters, water-quality, sample-points.
    :param where: The WHERE clause for the query (e.g., "STATE = 'MI'").
    :param out_fields: Comma-separated list of fields to return (e.g., "NAME,STATE"). Use "*" for all.
    :param limit: Maximum number of features to return (default 1000).
    :return: A GeoJSON FeatureCollection as a string, or error message.
    """
    if layer_name not in LAYER_MAPPING:
        return f"Error: Invalid layer name '{layer_name}'. Available: {list(LAYER_MAPPING.keys())}"

    layer_url = LAYER_MAPPING[layer_name]
    query_url = f"{layer_url}/query?f=json"

    params = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "true",
        "resultRecordCount": str(limit),
        "outSR": "4326"  # WGS84 for GeoJSON
    }

    try:
        response = requests.post(query_url, data=params, headers={"Accept": "application/json"}, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return f"Query error: {data['error']}"

        features = data.get("features", [])
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for feature in features:
            geom = feature.get("geometry", {})
            props = feature.get("attributes", {})

            # Convert Esri geometry to GeoJSON
            if "x" in geom and "y" in geom:
                # Point
                geojson_geom = {
                    "type": "Point",
                    "coordinates": [geom["x"], geom["y"]]
                }
            elif "rings" in geom:
                # Polygon
                geojson_geom = {
                    "type": "Polygon",
                    "coordinates": geom["rings"]
                }
            elif "paths" in geom:
                # Polyline
                geojson_geom = {
                    "type": "LineString",
                    "coordinates": geom["paths"][0] if geom["paths"] else []
                }
            else:
                geojson_geom = None

            if geojson_geom:
                geojson["features"].append({
                    "type": "Feature",
                    "geometry": geojson_geom,
                    "properties": props
                })

        return json.dumps(geojson, indent=4)
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
def save_geojson(content: str, file_path: str) -> str:
    """
    Saves a GeoJSON string to a file.

    :param content: The GeoJSON string content.
    :param file_path: The absolute path where to save the file (e.g., "/path/to/data.geojson").
    :return: Success message or error.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"GeoJSON saved to {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


@app.tool()
def display_geojson(geojson_path: str) -> str:
    """
    Displays a GeoJSON file in a browser map using geojsonio.

    :param geojson_path: The absolute path to the GeoJSON file.
    :return: A message indicating success or error.
    """
    import subprocess
    try:
        result = subprocess.run(["geojsonio", geojson_path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return "GeoJSON displayed in browser successfully."
        else:
            return f"Error running geojsonio: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "GeoJSON display initiated (browser may have opened)."
    except Exception as e:
        return f"Error: {str(e)}"

@app.tool()
def create_arcgis_app(geojson_path: str) -> str:
    """
    Creates a simple ArcGIS JS Maps SDK app with the GeoJSON data and opens it in the browser.

    :param geojson_path: The absolute path to the GeoJSON file.
    :return: A message indicating success or error.
    """
    import json
    import subprocess
    import platform
    try:
        with open(geojson_path, 'r') as f:
            geojson = json.load(f)
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>GeoJSON Layer - ArcGIS JS SDK</title>
  <link rel="stylesheet" href="https://js.arcgis.com/4.28/esri/themes/light/main.css" />
  <script src="https://js.arcgis.com/4.28/"></script>
  <style>
    html, body, #viewDiv {{
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div id="viewDiv"></div>
  <script>
    require([
      "esri/Map",
      "esri/views/MapView",
      "esri/layers/GeoJSONLayer"
    ], function(Map, MapView, GeoJSONLayer) {{
      const geojson = {json.dumps(geojson)};
      const blob = new Blob([JSON.stringify(geojson)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const layer = new GeoJSONLayer({{
        url: url
      }});
      const map = new Map({{
        basemap: "gray-vector",
        layers: [layer]
      }});
      const view = new MapView({{
        container: "viewDiv",
        map: map,
        center: [-77, 39],  // Default center, can be adjusted
        zoom: 6
      }});
    }});
  </script>
</body>
</html>"""
        
        app_path = "/Users/erickerney/dev/ai/esri-mcp/arcgis_app.html"
        with open(app_path, 'w') as f:
            f.write(html_content)
        
        # Open in browser
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", app_path])
        elif platform.system() == "Windows":
            subprocess.run(["start", app_path], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", app_path])
        
        return f"ArcGIS app created and opened: {app_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.tool()
def create_arcgis_app_with_rivers(geojson_path: str) -> str:
    """
    Creates a simple ArcGIS JS Maps SDK app with the GeoJSON data and rivers for the state of the GeoJSON data, then opens it in the browser.

    :param geojson_path: The absolute path to the GeoJSON file.
    :return: A message indicating success or error.
    """
    import json
    import subprocess
    import platform
    try:
        with open(geojson_path, 'r') as f:
            geojson = json.load(f)
        
        # Get state from the first feature's properties
        features = geojson.get("features", [])
        if not features:
            return "Error: No features found in GeoJSON."
        state = features[0].get("properties", {}).get("state")
        if not state:
            return "Error: State not found in GeoJSON properties."
        
        # Compute center from GeoJSON
        coords = []
        for feature in features:
            geom = feature.get("geometry", {})
            if geom.get("type") == "Point":
                coords.append(geom["coordinates"])
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            center_lon = (min(lons) + max(lons)) / 2
            center_lat = (min(lats) + max(lats)) / 2
        else:
            center_lon, center_lat = -77, 39  # default
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>GeoJSON and Rivers Layer - ArcGIS JS SDK</title>
  <link rel="stylesheet" href="https://js.arcgis.com/4.28/esri/themes/light/main.css" />
  <script src="https://js.arcgis.com/4.28/"></script>
  <style>
    html, body, #viewDiv {{
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div id="viewDiv"></div>
  <script>
    require([
      "esri/Map",
      "esri/views/MapView",
      "esri/layers/GeoJSONLayer",
      "esri/layers/FeatureLayer"
    ], function(Map, MapView, GeoJSONLayer, FeatureLayer) {{
      const geojson = {json.dumps(geojson)};
      const blob = new Blob([JSON.stringify(geojson)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const layer = new GeoJSONLayer({{
        url: url
      }});
      const riversLayer = new FeatureLayer({{
        url: "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Rivers_and_Streams/FeatureServer/0",
        definitionExpression: "State = '{state}'"
      }});
      const map = new Map({{
        basemap: "gray-vector",
        layers: [riversLayer, layer]  // Rivers below points
      }});
      const view = new MapView({{
        container: "viewDiv",
        map: map,
        center: [{center_lon}, {center_lat}],
        zoom: 8
      }});
    }});
  </script>
</body>
</html>"""
        
        app_path = "/Users/erickerney/dev/ai/esri-mcp/arcgis_app_with_rivers.html"
        with open(app_path, 'w') as f:
            f.write(html_content)
        
        # Open in browser
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", app_path])
        elif platform.system() == "Windows":
            subprocess.run(["start", app_path], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", app_path])
        
        return f"ArcGIS app with rivers for {state} created and opened: {app_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.tool()
def create_water_map_context(geojson_path: str) -> str:
    """
    Creates a comprehensive water-related ArcGIS JS Maps SDK app with the GeoJSON gages, rivers, dams, watersheds, and water quality stations for the state, then opens it in the browser.

    :param geojson_path: The absolute path to the GeoJSON file.
    :return: A message indicating success or error.
    """
    import json
    import subprocess
    import platform
    try:
        with open(geojson_path, 'r') as f:
            geojson = json.load(f)

        # Get state from the first feature's properties
        features = geojson.get("features", [])
        if not features:
            return "Error: No features found in GeoJSON."
        state_abbr = features[0].get("properties", {}).get("state")
        if not state_abbr:
            return "Error: State not found in GeoJSON properties."

        # Map abbreviations to full state names for dams filter
        state_abbr_to_name = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        state = state_abbr_to_name.get(state_abbr, state_abbr)
        
        # Compute center from GeoJSON
        coords = []
        for feature in features:
            geom = feature.get("geometry", {})
            if geom.get("type") == "Point":
                coords.append(geom["coordinates"])
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            center_lon = (min(lons) + max(lons)) / 2
            center_lat = (min(lats) + max(lats)) / 2
        else:
            center_lon, center_lat = -77, 39  # default
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>Water Map Context - ArcGIS JS SDK</title>
  <link rel="stylesheet" href="https://js.arcgis.com/4.28/esri/themes/light/main.css" />
  <script src="https://js.arcgis.com/4.28/"></script>
  <style>
    html, body, #viewDiv {{
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div id="viewDiv"></div>
  <script>
    require([
      "esri/Map",
      "esri/views/MapView",
      "esri/layers/GeoJSONLayer",
      "esri/layers/FeatureLayer",
      "esri/widgets/Legend"
    ], function(Map, MapView, GeoJSONLayer, FeatureLayer, Legend) {{
      const geojson = {json.dumps(geojson)};
      const blob = new Blob([JSON.stringify(geojson)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
       const gagesLayer = new GeoJSONLayer({{
         url: url,
         title: "USGS Gaging Stations",
         opacity: 0.6,
         renderer: {{
           type: "unique-value",
           field: "status",
           uniqueValueInfos: [
             {{ value: "no_flooding", symbol: {{ type: "simple-marker", color: "green", size: 8, outline: {{ color: "black", width: 1 }} }} }},
             {{ value: "action", symbol: {{ type: "simple-marker", color: "yellow", size: 10, outline: {{ color: "black", width: 2 }}, halo: {{ color: "yellow", size: 2 }} }} }},
             {{ value: "minor", symbol: {{ type: "simple-marker", color: "orange", size: 12, outline: {{ color: "black", width: 2 }}, halo: {{ color: "orange", size: 3 }} }} }},
             {{ value: "moderate", symbol: {{ type: "simple-marker", color: "red", size: 14, outline: {{ color: "black", width: 2 }}, halo: {{ color: "red", size: 4 }} }} }},
             {{ value: "major", symbol: {{ type: "simple-marker", color: "purple", size: 16, outline: {{ color: "black", width: 2 }}, halo: {{ color: "purple", size: 5 }} }} }}
           ],
           defaultSymbol: {{ type: "simple-marker", color: "gray", size: 8, outline: {{ color: "black", width: 1 }} }}
         }},
         popupTemplate: {{
           title: "USGS Gaging Station",
           content: "Station: {{gaugelid}}<br>Location: {{location}}<br>Status: {{status}}<br>State: {{state}}"
         }}
       }});
       const riversLayer = new FeatureLayer({{
         url: "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Rivers_and_Streams/FeatureServer/0",
         definitionExpression: "State = '{state}'",
         title: "Rivers",
         opacity: 0.6,
         renderer: {{
           type: "simple",
           symbol: {{
             type: "simple-line",
             color: "blue",
             width: 3
           }}
         }},
         popupTemplate: {{
           title: "River",
           content: "Name: {{Name}}<br>Feature: {{Feature}}<br>Miles: {{Miles}}"
         }}
       }});
       const watershedsLayer = new FeatureLayer({{
          url: "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/3",
          definitionExpression: "states LIKE '%TX%'",
          title: "HUC6 Watersheds",
          opacity: 0.8,
          renderer: {
            type: "simple",
            symbol: {
              type: "esriSFS",
              style: "esriSFSSolid",
              color: [0, 0, 0, 0],
              outline: {
                type: "esriSLS",
                style: "esriSLSSolid",
                color: [132, 0, 168, 255],
                width: 1.25
              }
            }
          },
          minScale: 0,
          maxScale: 0,
          labelingInfo: null
       }});
       const damsLayer = new FeatureLayer({{
         url: "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/NID_v1/FeatureServer/0",
         definitionExpression: "State = '{state}'",
         title: "Dams",
         opacity: 0.6,
         renderer: {{
           type: "unique-value",
           field: "PRIMARY_DAM_TYPE",
           uniqueValueInfos: [
             {{ value: "Earth", symbol: {{ type: "simple-marker", style: "triangle", color: "saddlebrown", size: 4, outline: {{ color: "black", width: 1 }} }} }},
             {{ value: "Concrete", symbol: {{ type: "simple-marker", style: "triangle", color: "gray", size: 4, outline: {{ color: "black", width: 1 }} }} }},
             {{ value: "Rockfill", symbol: {{ type: "simple-marker", style: "triangle", color: "darkgray", size: 4, outline: {{ color: "black", width: 1 }} }} }},
             {{ value: "Other", symbol: {{ type: "simple-marker", style: "triangle", color: "orange", size: 4, outline: {{ color: "black", width: 1 }} }} }}
           ],
           defaultSymbol: {{ type: "simple-marker", style: "triangle", color: "orange", size: 4, outline: {{ color: "black", width: 1 }} }}
         }},
         popupTemplate: {{
           title: "Dam",
           content: "Name: {{NAME}}<br>Type: {{PRIMARY_DAM_TYPE}}<br>Height: {{NID_HEIGHT}} ft<br>State: {{STATE}}"
         }}
       }});
       console.log("Dams filter:", damsLayer.definitionExpression);
      const map = new Map({{
        basemap: "dark-gray-vector",
        layers: [watershedsLayer, riversLayer, damsLayer, gagesLayer]  // Order: base to top
      }});
      const view = new MapView({{
        container: "viewDiv",
        map: map,
        center: [{center_lon}, {center_lat}],
        zoom: 8
      }});
      const legend = new Legend({{
        view: view
      }});
       view.ui.add(legend, "bottom-right");
       const legendButton = document.createElement("button");
       legendButton.innerHTML = "Toggle Legend";
       legendButton.onclick = () => {{ legend.visible = !legend.visible; }};
       view.ui.add(legendButton, "top-left");
       // Debug loading
      riversLayer.when(() => console.log("Rivers loaded"), (error) => console.log("Rivers error", error));
       watershedsLayer.when(() => console.log("Watersheds loaded"), (error) => console.log("Watersheds error", error));
    }});
  </script>
</body>
</html>"""
        
        app_path = "/Users/erickerney/dev/ai/esri-mcp/water_map_context.html"
        with open(app_path, 'w') as f:
            f.write(html_content)
        
        # Open in browser
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", app_path])
        elif platform.system() == "Windows":
            subprocess.run(["start", app_path], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", app_path])
        
        return f"Water map context for {state} created and opened: {app_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.tool()
def create_embeddable_water_map(state: str) -> str:
    """
    Creates embeddable HTML for a comprehensive water map of the specified state using Esri REST URLs directly.

    :param state: The state abbreviation (e.g., 'TX' for Texas).
    :return: HTML string for embedding the map.
    """
    # Map state abbr to full name
    state_abbr_to_name = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
        'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
        'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
        'DC': 'District of Columbia'
    }
    # Check if state is full name, convert to abbr
    state_upper = state.upper()
    full_names_upper = {v.upper(): k for k, v in state_abbr_to_name.items()}
    print(f"Input state: {state}, upper: {state_upper}, in dict: {state_upper in full_names_upper}")
    if state_upper in full_names_upper:
        abbr = full_names_upper[state_upper]
        full_state = state_abbr_to_name[abbr]
        state = abbr
        print(f"Converted to abbr: {state}, full: {full_state}")
    else:
        # Assume abbr, get full
        full_state = state_abbr_to_name.get(state_upper, state_upper)
        state = state_upper  # normalize to upper for abbr
        print(f"Assumed abbr: {state}, full: {full_state}")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>Water Map - {full_state}</title>
  <link rel="stylesheet" href="https://js.arcgis.com/4.28/esri/themes/light/main.css" />
  <script src="https://js.arcgis.com/4.28/"></script>
  <style>
    html, body, #viewDiv {{
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div id="viewDiv"></div>
  <script>
    require([
      "esri/Map",
      "esri/views/MapView",
      "esri/layers/FeatureLayer",
      "esri/widgets/Legend"
    ], function(Map, MapView, FeatureLayer, Legend) {{
      const gagesLayer = new FeatureLayer({{
        url: "https://mapservices.weather.noaa.gov/eventdriven/rest/services/water/riv_gauges/MapServer/0",
        definitionExpression: "state = '{state}'",
        title: "USGS Gaging Stations",
        opacity: 0.6,
        renderer: {{
          type: "unique-value",
          field: "status",
          uniqueValueInfos: [
            {{ value: "no_flooding", symbol: {{ type: "simple-marker", color: "green", size: 8, outline: {{ color: "black", width: 1 }} }} }},
            {{ value: "action", symbol: {{ type: "simple-marker", color: "yellow", size: 10, outline: {{ color: "black", width: 2 }}, halo: {{ color: "yellow", size: 2 }} }} }},
            {{ value: "minor", symbol: {{ type: "simple-marker", color: "orange", size: 12, outline: {{ color: "black", width: 2 }}, halo: {{ color: "orange", size: 3 }} }} }},
            {{ value: "moderate", symbol: {{ type: "simple-marker", color: "red", size: 14, outline: {{ color: "black", width: 2 }}, halo: {{ color: "red", size: 4 }} }} }},
            {{ value: "major", symbol: {{ type: "simple-marker", color: "purple", size: 16, outline: {{ color: "black", width: 2 }}, halo: {{ color: "purple", size: 5 }} }} }}
          ],
          defaultSymbol: {{ type: "simple-marker", color: "gray", size: 8, outline: {{ color: "black", width: 1 }} }}
        }},
        popupTemplate: {{
          title: "USGS Gaging Station",
          content: "Station: {{gaugelid}}<br>Location: {{location}}<br>Status: {{status}}<br>State: {{state}}"
        }}
      }});
      const riversLayer = new FeatureLayer({{
         url: "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Rivers_and_Streams/FeatureServer/0",
         definitionExpression: "State = '{state}'",
        title: "Rivers",
        opacity: 0.6,
        renderer: {{
          type: "simple",
          symbol: {{
            type: "simple-line",
            color: "blue",
            width: 3
          }}
        }},
        popupTemplate: {{
          title: "River",
          content: "Name: {{Name}}<br>Feature: {{Feature}}<br>Miles: {{Miles}}"
        }}
      }});
      const watershedsLayer = new FeatureLayer({{
        url: "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/3",
        definitionExpression: "states LIKE '%{state}%'",
        title: "HUC6 Watersheds",
        opacity: 0.8,
        minScale: 0,
        maxScale: 0,
        labelingInfo: null,
        renderer: {{
          type: "simple",
          symbol: {{
            type: "simple-fill",
            color: [0, 0, 0, 0],
            outline: {{
              color: [132, 0, 168, 255],
              width: 1.25
            }}
          }}
        }}
      }});
      const damsLayer = new FeatureLayer({{
        url: "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/NID_v1/FeatureServer/0",
        definitionExpression: "State = '{full_state}'",
        title: "Dams",
        opacity: 0.6,
        renderer: {{
          type: "unique-value",
          field: "PRIMARY_DAM_TYPE",
          uniqueValueInfos: [
            {{ value: "Earth", symbol: {{ type: "simple-marker", style: "triangle", color: "saddlebrown", size: 4, outline: {{ color: "black", width: 1 }} }} }},
            {{ value: "Concrete", symbol: {{ type: "simple-marker", style: "triangle", color: "gray", size: 4, outline: {{ color: "black", width: 1 }} }} }},
            {{ value: "Rockfill", symbol: {{ type: "simple-marker", style: "triangle", color: "darkgray", size: 4, outline: {{ color: "black", width: 1 }} }} }},
            {{ value: "Other", symbol: {{ type: "simple-marker", style: "triangle", color: "orange", size: 4, outline: {{ color: "black", width: 1 }} }} }}
          ],
          defaultSymbol: {{ type: "simple-marker", style: "triangle", color: "orange", size: 4, outline: {{ color: "black", width: 1 }} }}
        }},
        popupTemplate: {{
          title: "Dam",
          content: "Name: {{NAME}}<br>Type: {{PRIMARY_DAM_TYPE}}<br>Height: {{NID_HEIGHT}} ft<br>State: {{STATE}}"
        }}
      }});
      const map = new Map({{
        basemap: "dark-gray-vector",
        layers: [watershedsLayer, riversLayer, damsLayer, gagesLayer]
      }});
      const view = new MapView({{
        container: "viewDiv",
        map: map,
        center: [-98.5795, 39.8283],  // US center, can be adjusted per state
        zoom: 5
      }});
      const legend = new Legend({{
        view: view
      }});
      view.ui.add(legend, "bottom-right");
    }});
  </script>
</body>
</html>"""
    return html_content

if __name__ == "__main__":
    import sys
    if "--http" in sys.argv:
        app.run(transport="http", port=8000)
    else:
        app.run()

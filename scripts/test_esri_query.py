import requests
import json
import urllib.parse

LAYER_MAPPING = {
    "states": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized_Boundaries/FeatureServer/0",
    "usgs-gauges": "https://mapservices.weather.noaa.gov/eventdriven/rest/services/water/riv_gauges/MapServer/0",
    "sample-points": "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Census/MapServer/0" # New sample layer
}

def query_layer(layer_name: str, where: str = "1=1", out_fields: str = "*", return_count_only: bool = False, spatial_filter: str = None) -> dict:
    """
    Queries a feature layer from the Esri Living Atlas.

    :param layer_name: The name of the layer to query. Available layers: states, usgs-gauges, sample-points.
    :param where: The WHERE clause for the query.
    :param out_fields: The fields to return.
    :param return_count_only: Whether to return only the count of features.
    :param spatial_filter: A spatial filter in Esri JSON format.
    :return: The JSON response from the server.
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
    if spatial_filter:
        # Manually form-encode parameters, URL-encode geometry
        encoded_params = {
            "where": params["where"],
            "outFields": params["outFields"],
            "returnCountOnly": params["returnCountOnly"],
            "geometry": urllib.parse.quote(spatial_filter), # URL-encode the JSON string
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects"
        }
        response = requests.post(query_url, data=encoded_params, headers=headers)
    else:
        response = requests.get(query_url, params=params, headers=headers)

    response.raise_for_status()
    return response.json()

def get_state_geometry(state_name: str) -> dict:
    """
    Gets the geometry of a state from the 'states' layer.

    :param state_name: The name of the state (e.g., "Michigan").
    :return: The geometry of the state in Esri JSON format.
    """
    states_layer_url = LAYER_MAPPING["states"]
    where_clause = f"STATE_NAME = '{state_name}'"
    params = {
        "where": where_clause,
        "outFields": "",
        "returnGeometry": "true",
        "f": "json"
    }
    response = requests.get(f"{states_layer_url}/query", params=params)
    response.raise_for_status()
    features = response.json().get("features", [])
    if features:
        return features[0]["geometry"]
    return {"error": f"State '{state_name}' not found or has no geometry."}

if __name__ == "__main__":
    try:
        # Step 1: Get Michigan's geometry
        print("Getting Michigan's geometry...")
        michigan_geometry = get_state_geometry(state_name="Michigan")
        if "error" in michigan_geometry:
            print(f"Error: {michigan_geometry['error']}")
        else:
            print("Michigan geometry retrieved successfully.")
            
            # Step 2: Query sample points within Michigan's geometry
            print("Querying sample points in Michigan...")
            spatial_filter_str = json.dumps(michigan_geometry)
            sample_points_count = query_layer(
                layer_name="sample-points",
                spatial_filter=spatial_filter_str,
                return_count_only=True
            )
            
            if "count" in sample_points_count:
                print(f"Number of sample points in Michigan: {sample_points_count['count']}")
            else:
                print(f"Error or unexpected response from sample points query: {sample_points_count}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

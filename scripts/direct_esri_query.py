import requests
import json
import urllib.parse

# NOAA River Gauges URL
layer_url = "https://mapservices.weather.noaa.gov/eventdriven/rest/services/water/riv_gauges/MapServer/0"

# Michigan bounding box (simplified for testing)
michigan_bbox = {
    "xmin": -90.41,
    "ymin": 41.69,
    "xmax": -82.41,
    "ymax": 48.31,
    "spatialReference": {"wkid": 4326}
}

# Parameters for the query
params = {
    "where": "1=1",
    "outFields": "*",
    "returnCountOnly": "true",
    "geometry": urllib.parse.quote(json.dumps(michigan_bbox)), # URL-encode the JSON string
    "geometryType": "esriGeometryEnvelope", # Explicitly set geometryType
    "spatialRel": "esriSpatialRelIntersects" # Explicitly set spatialRel
}

headers = {"Accept": "application/json"}

# Construct the full URL with f=json
query_url = f"{layer_url}/query?f=json"

print(f"Sending POST request to: {query_url}")
print(f"With parameters: {params}")
print(f"With headers: {headers}")

try:
    response = requests.post(query_url, data=params, headers=headers)
    response.raise_for_status() # Raise an exception for bad status codes
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    print(f"Response JSON: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

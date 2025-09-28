import requests

base_url = "http://localhost:5174/mcp"

# Test query_layer for weather-stations

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "query_layer",
        "arguments": {
            "layer_name": "weather-stations",
            "where": "COUNTRY = 'United States'",
            "return_count_only": True
        }
    }
}

response = requests.post(base_url, json=payload)
print("Weather stations response:", response.text)

# Test raws-stations
payload2 = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "query_layer",
        "arguments": {
            "layer_name": "raws-stations",
            "where": "State = 'Michigan'",
            "return_count_only": True
        }
    }
}

response2 = requests.post(base_url, json=payload2)
print("RAWS stations response:", response2.text)

# Test storm-reports
payload3 = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "query_layer",
        "arguments": {
            "layer_name": "storm-reports",
            "where": "1=1",
            "return_count_only": True
        }
    }
}

response3 = requests.post(base_url, json=payload3)
print("Storm reports response:", response3.text)
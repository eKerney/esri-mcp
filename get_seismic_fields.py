import requests

# Get fields for seismic-stations
url = "http://127.0.0.1:8000/mcp"
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_layer_fields",
        "arguments": {
            "layer_name": "seismic-stations"
        }
    }
}

headers = {"Accept": "application/json, text/event-stream"}
response = requests.post(url, json=payload, headers=headers, stream=True)

buffer = ''
for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            data = decoded[6:]
            result = data
            print("Seismic fields:", result)
            break
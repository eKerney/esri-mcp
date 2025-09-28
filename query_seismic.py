import requests

# Query seismic stations
url = "http://127.0.0.1:8000/mcp"
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "query_layer",
        "arguments": {
            "layer_name": "seismic-stations",
            "where": "1=1",
            "return_count_only": True
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
            print("Seismic stations count:", result)
            break
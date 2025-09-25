# esri-mcp

Experimenting with using gemini to create a POC MCP server to access ESRI Living Atlas Data. 
I would like to send natural langugae queries to the LLM Host and have it answers those questions or create a RestAPI query to retrieve specific features

│ > Great!  I am interested in performing natural language queries of these Living Atlas layers such as:        │
│   "how many USGS stations are in the state of Michigan?" etc...  So I would like to focus on vector           │
│   layers and not raster, and those that have similar features as just mentioned that would be useful to       │
│   query.                                                                                                      │

Gemini is looking for layers that would work for this type of query 
Ok let's try OpenCode! 

```bash
brew install sst/tap/opencode
```

```json
  "mcpServers": {
    "gis-mcp": {
      "command": "/Users/erickerney/dev/ai/.venv/bin/gis-mcp",
      "args": []
    },
    "mcp-server-firecrawl": {
      "command": "npx",
      "args": [
        "-y",
        "firecrawl-mcp"
      ],
      "env": {
        "FIRECRAWL_API_KEY": "fc-1e0ecd9e0788447c8a4b46731fb73541"
      }
    }
  }
```


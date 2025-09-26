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
        "FIRECRAWL_API_KEY": ""
      }
    }
  }
```


I should have taking better notes, tried several differing approaches.  
Currently working with Web LLM in browser LLM to call the esri tools. 
It's not working very good.   
Opencode/Grok is going to try connecting us to a cloud hosted model Gemini which I can use for free.   
Perhaps this will yield better results for tool calling.   
Gemini was NOT doing very  good with the CLI.   

Currently amd running the esri mcp as a local FastMCP server to access via http.   
It works great through the CLI though I am trying to access it via an app now, much more difficult.  
BTW love that opencode automatically copies whenever I highlight with mouse 

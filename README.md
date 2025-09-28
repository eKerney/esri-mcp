# Esri MCP Server

An MCP (Model Context Protocol) server for querying and visualizing data from the Esri Living Atlas, with a focus on water resources and mapping.

## Features

- Query various Esri Living Atlas layers including:
  - Administrative: states, counties
  - Water resources: USGS gages, rivers, dams, watersheds, impaired waters, water quality stations
  - Environmental monitoring: weather stations, RAWS stations, seismic stations, CORS stations, storm reports
- Generate interactive ArcGIS JS Maps SDK applications
- Create comprehensive water context maps with multiple layers
- Support for spatial filters and geometry queries
- Web-based frontend with AI-powered query interface

## Tools

- `query_layer`: Query feature layers with custom filters
- `query_point_layer`: Query point data layers (USGS gages, water quality, weather stations, etc.)
- `get_layer_fields`: Get field information for layers
- `get_state_geometry`: Retrieve state boundaries
- `query_geojson`: Query layers and return GeoJSON
- `save_geojson`: Save GeoJSON to file
- `display_geojson`: Visualize GeoJSON in browser
- `create_arcgis_app`: Generate simple ArcGIS maps
- `create_arcgis_app_with_rivers`: Maps with rivers overlay
- `create_water_map_context`: Full water resource maps
- `create_embeddable_water_map`: Embeddable water maps for states

## Installation

1. Clone the repo
2. Install Python dependencies: `pip install fastmcp requests`
3. Install Node.js dependencies for frontend: `cd frontend && npm install`
4. Run the MCP server: `python main.py --http`
5. In another terminal, run the frontend: `cd frontend && npm run dev`

## Usage

### MCP Server

Start the server: `python main.py --http`

Connect via MCP clients or use the provided scripts in `scripts/`.

### Frontend

Start the frontend: `cd frontend && npm run dev`

Open http://localhost:5174 to access the web interface with AI-powered queries.

### Command-line Client

Use `clients.py` for command-line interaction:

```bash
# List available tools
python clients.py list-tools

# Call a tool
python clients.py call-tool query_layer layer_name usgs-gauges where "state = 'MI'"
```

See `scripts/` for additional example usage.

## Repository Structure

- `main.py`: Main MCP server with Esri Living Atlas tools
- `frontend/`: React frontend with MCP client and AI interface
- `scripts/`: Test and helper scripts for various queries
- `clients.py`: Command-line MCP client
- `.gitignore`: Ignores generated files

## License

MIT
# Esri MCP Server

An MCP (Model Context Protocol) server for querying and visualizing data from the Esri Living Atlas, with a focus on water resources and mapping.

## Features

- Query various Esri Living Atlas layers (states, counties, USGS gages, rivers, dams, watersheds, etc.)
- Generate interactive ArcGIS JS Maps SDK applications
- Create comprehensive water context maps with multiple layers
- Support for spatial filters and geometry queries

## Tools

- `query_layer`: Query feature layers with custom filters
- `get_layer_fields`: Get field information for layers
- `get_state_geometry`: Retrieve state boundaries
- `display_geojson`: Visualize GeoJSON in browser
- `create_arcgis_app`: Generate simple ArcGIS maps
- `create_arcgis_app_with_rivers`: Maps with rivers overlay
- `create_water_map_context`: Full water resource maps

## Installation

1. Clone the repo
2. Install dependencies: `pip install fastmcp requests`
3. Run the server: `python main.py`

## Usage

Start the server and connect via MCP clients. See `scripts/` for example usage.

## Repository Structure

- `main.py`: Main MCP server
- `scripts/`: Test and helper scripts
- `.gitignore`: Ignores generated files

## License

MIT
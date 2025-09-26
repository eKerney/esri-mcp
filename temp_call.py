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
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    full_state = state_abbr_to_name.get(state.upper(), state.upper())

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
        definitionExpression: "State = '{full_state}'",
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

print(create_embeddable_water_map('DC'))
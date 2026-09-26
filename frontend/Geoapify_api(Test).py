import webbrowser # For opening the generated HTML file in a web browser
from functools import partial # For creating partial functions with pre-filled arguments
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer # For serving the generated HTML file locally
from pathlib import Path # For handling file paths and directories

API_KEY = "YOUR_API_KEY" # Geoapify Key from website; replace with your own API key for security purposes
DEFAULT_START = "401 Bridgeboro Street, Riverside Township, NJ 08075, USA" # Example address to test
DEFAULT_END = "100 Main St, Camden, NJ 08103, USA" # Example end to test between 2 counties


def build_map_html() -> str: # Function to make HTML file for the map
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Route Planner</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f5f7;
        }}
        .controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(255,255,255,0.94);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            width: min(360px, calc(100vw - 40px));
        }}
        .controls h2 {{
            margin: 0 0 12px;
            font-size: 20px;
        }}
        label {{
            display: block;
            font-size: 13px;
            margin: 10px 0 6px;
            color: #333;
        }}
        input {{
            width: 100%;
            padding: 10px 12px;
            font-size: 14px;
            border: 1px solid #cfd8dc;
            border-radius: 8px;
        }}
        button {{
            width: 100%;
            margin-top: 14px;
            padding: 11px;
            background: #1f6feb;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: bold;
        }}
        button:hover {{ background: #195cc5; }}
        #status {{
            margin-top: 12px;
            min-height: 20px;
            font-size: 13px;
            color: #333;
        }}
        #map {{
            height: 100vh;
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <h2>Route Planner</h2>
        <label for="startInput">Starting address</label>
        <input id="startInput" type="text" value="{DEFAULT_START}" />

        <label for="endInput">Destination address</label>
        <input id="endInput" type="text" value="{DEFAULT_END}" />

        <button id="routeButton">Show route</button>
        <div id="status"></div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const apiKey = '{API_KEY}';
        const startInput = document.getElementById('startInput');
        const endInput = document.getElementById('endInput');
        const routeButton = document.getElementById('routeButton');
        const statusBox = document.getElementById('status');

        const map = L.map('map').setView([39.95, -75.05], 9);

        const baseTiles = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        }});

        baseTiles.on('tileerror', () => setStatus('Map tiles could not load. Check your internet connection.', true));
        baseTiles.addTo(map);
        map.whenReady(() => setTimeout(() => map.invalidateSize(), 200));

        let routeLayer = null;

        function setStatus(message, isError = false) {{
            statusBox.textContent = message;
            statusBox.style.color = isError ? '#a12727' : '#333';
        }}

        async function fetchGeoapifyJson(url, service) {{
            const response = await fetch(url);
            const data = await response.json().catch(() => ({{}}));

            if (!response.ok) {{
                const detail = typeof data.message === 'string' ? data.message : response.statusText;
                throw new Error(`Geoapify ${{service}} failed (HTTP ${{response.status}}): ${{detail}}. Check the API key and its service permissions.`);
            }}

            return data;
        }}

        async function geocodeAddress(address) {{
            const url = `https://api.geoapify.com/v1/geocode/search?text=${{encodeURIComponent(address)}}&lang=en&limit=1&filter=countrycode:us&bias=proximity:39.95,-75.05&apiKey=${{apiKey}}`;
            const data = await fetchGeoapifyJson(url, 'geocoding');

            if (!data.features || data.features.length === 0) {{
                throw new Error(`No results found for: ${{address}}`);
            }}

            const feature = data.features[0];
            const props = feature.properties;
            return [props.lat, props.lon];
        }}

        async function buildRoute(startAddress, endAddress) {{
            const start = await geocodeAddress(startAddress);
            const end = await geocodeAddress(endAddress);

            const routeUrl = `https://api.geoapify.com/v1/routing?waypoints=${{start[0]}},${{start[1]}}|${{end[0]}},${{end[1]}}&mode=drive&apiKey=${{apiKey}}`;
            const routeData = await fetchGeoapifyJson(routeUrl, 'routing');

            const routeFeature = routeData.features && routeData.features[0];
            if (!routeFeature || !routeFeature.geometry || !routeFeature.geometry.coordinates) {{
                throw new Error('No route was found for those locations.');
            }}

            const routeCoordinates = routeFeature.geometry.type === 'MultiLineString'
                ? routeFeature.geometry.coordinates.flat()
                : routeFeature.geometry.coordinates;
            const coords = routeCoordinates.map(([lon, lat]) => [lat, lon]);

            if (routeLayer) {{
                map.removeLayer(routeLayer);
            }}

            routeLayer = L.polyline(coords, {{ color: 'blue', weight: 5 }}).addTo(map);
            L.marker(start).addTo(map).bindPopup('Start');
            L.marker(end).addTo(map).bindPopup('Destination');
            map.fitBounds(L.latLngBounds(coords).pad(0.2));
        }}

        routeButton.addEventListener('click', async () => {{
            const startAddress = startInput.value.trim();
            const endAddress = endInput.value.trim();

            if (!startAddress || !endAddress) {{
                setStatus('Please enter both addresses.', true);
                return;
            }}

            try {{
                setStatus('Finding route...');
                await buildRoute(startAddress, endAddress);
                setStatus('Route loaded successfully.');
            }} catch (error) {{
                console.error(error);
                setStatus(error.message || 'Unable to load route.', true);
            }}
        }});

        setStatus('Ready to plan a trip.');
    </script>
</body>
</html>
"""


output_path = Path(__file__).with_name("map.html") # Path to save the generated map HTML file
output_path.write_text(build_map_html(), encoding="utf-8") # Write the generated HTML content to the file

print(f"Map saved to: {output_path}") # Print the path where the map HTML file was saved
handler = partial(SimpleHTTPRequestHandler, directory=str(output_path.parent)) # Create a request handler for the local server
server = ThreadingHTTPServer(("127.0.0.1", 0), handler) # Start a threading HTTP server on a random port
map_url = f"http://127.0.0.1:{server.server_port}/map.html" # Construct the URL for the local map server
print(f"Map opened at: {map_url}") # Print the URL where the map can be accessed in a browser
webbrowser.open(map_url) # Open the map in the default web browser
print("Press Ctrl+C to stop the local map server.") # Print instructions to stop the server
server.serve_forever() # Start serving requests indefinitely until interrupted by Ctrl+C
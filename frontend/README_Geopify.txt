Geoapify HTML Test

On the webpage try the default inputs, then try addresses within Burlington or Camden County in this format:
Street address, City, State Zip Code, USA (For specific api requirements for what I used)

Python side:
Make sure webbrowser, functools, http.server, and pathlib libraries are installed or your device has access to them.
If using VSCode, just make sure the environment is set up with the libraries mentioned above

API Key: Geoapify has free access to all api keys, you can go to the website that I used:
	https://www.geoapify.com/routing-api/?gad_source=1&gad_campaignid=20985186672&gclid=CjwKCAjwtp7VBhBjEiwAJfpV-3qEg8GFlEiXh5bT0Dk7Wog6mqVfrTgacbbQA2vwDualPtJXECSMJBoCNGsQAvD_BwE
scroll down to the option "Get API Key" 
Then create a project with whatever name, and it should show a page with its own api key
Double check that the API selected is "Routing API" 
Then replace the variable, API_KEY, on the .py file with the one generated on the site 

Please let me know if and how it works, what needs to be adjusted etc.


What the HTML file wrote on my device:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Route Planner</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f5f7;
        }
        .controls {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(255,255,255,0.94);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            width: min(360px, calc(100vw - 40px));
        }
        .controls h2 {
            margin: 0 0 12px;
            font-size: 20px;
        }
        label {
            display: block;
            font-size: 13px;
            margin: 10px 0 6px;
            color: #333;
        }
        input {
            width: 100%;
            padding: 10px 12px;
            font-size: 14px;
            border: 1px solid #cfd8dc;
            border-radius: 8px;
        }
        button {
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
        }
        button:hover { background: #195cc5; }
        #status {
            margin-top: 12px;
            min-height: 20px;
            font-size: 13px;
            color: #333;
        }
        #map {
            height: 100vh;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="controls">
        <h2>Route Planner</h2>
        <label for="startInput">Starting address</label>
        <input id="startInput" type="text" value="401 Bridgeboro Street, Riverside Township, NJ 08075, USA" />

        <label for="endInput">Destination address</label>
        <input id="endInput" type="text" value="100 Main St, Camden, NJ 08103, USA" />

        <button id="routeButton">Show route</button>
        <div id="status"></div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const apiKey = 'YOUR_API_KEY';
        const startInput = document.getElementById('startInput');
        const endInput = document.getElementById('endInput');
        const routeButton = document.getElementById('routeButton');
        const statusBox = document.getElementById('status');

        const map = L.map('map').setView([39.95, -75.05], 9);

        const baseTiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        });

        baseTiles.on('tileerror', () => setStatus('Map tiles could not load. Check your internet connection.', true));
        baseTiles.addTo(map);
        map.whenReady(() => setTimeout(() => map.invalidateSize(), 200));

        let routeLayer = null;

        function setStatus(message, isError = false) {
            statusBox.textContent = message;
            statusBox.style.color = isError ? '#a12727' : '#333';
        }

        async function fetchGeoapifyJson(url, service) {
            const response = await fetch(url);
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const detail = typeof data.message === 'string' ? data.message : response.statusText;
                throw new Error(`Geoapify ${service} failed (HTTP ${response.status}): ${detail}. Check the API key and its service permissions.`);
            }

            return data;
        }

        async function geocodeAddress(address) {
            const url = `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(address)}&lang=en&limit=1&filter=countrycode:us&bias=proximity:39.95,-75.05&apiKey=${apiKey}`;
            const data = await fetchGeoapifyJson(url, 'geocoding');

            if (!data.features || data.features.length === 0) {
                throw new Error(`No results found for: ${address}`);
            }

            const feature = data.features[0];
            const props = feature.properties;
            return [props.lat, props.lon];
        }

        async function buildRoute(startAddress, endAddress) {
            const start = await geocodeAddress(startAddress);
            const end = await geocodeAddress(endAddress);

            const routeUrl = `https://api.geoapify.com/v1/routing?waypoints=${start[0]},${start[1]}|${end[0]},${end[1]}&mode=drive&apiKey=${apiKey}`;
            const routeData = await fetchGeoapifyJson(routeUrl, 'routing');

            const routeFeature = routeData.features && routeData.features[0];
            if (!routeFeature || !routeFeature.geometry || !routeFeature.geometry.coordinates) {
                throw new Error('No route was found for those locations.');
            }

            const routeCoordinates = routeFeature.geometry.type === 'MultiLineString'
                ? routeFeature.geometry.coordinates.flat()
                : routeFeature.geometry.coordinates;
            const coords = routeCoordinates.map(([lon, lat]) => [lat, lon]);

            if (routeLayer) {
                map.removeLayer(routeLayer);
            }

            routeLayer = L.polyline(coords, { color: 'blue', weight: 5 }).addTo(map);
            L.marker(start).addTo(map).bindPopup('Start');
            L.marker(end).addTo(map).bindPopup('Destination');
            map.fitBounds(L.latLngBounds(coords).pad(0.2));
        }

        routeButton.addEventListener('click', async () => {
            const startAddress = startInput.value.trim();
            const endAddress = endInput.value.trim();

            if (!startAddress || !endAddress) {
                setStatus('Please enter both addresses.', true);
                return;
            }

            try {
                setStatus('Finding route...');
                await buildRoute(startAddress, endAddress);
                setStatus('Route loaded successfully.');
            } catch (error) {
                console.error(error);
                setStatus(error.message || 'Unable to load route.', true);
            }
        });

        setStatus('Ready to plan a trip.');
    </script>
</body>
</html>

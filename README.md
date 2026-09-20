# Product: Navi-Gator, a map GPS web-based application. 
Software Engineering class project. 

Navi-Gator is a web-based map/GPS application that computes driving routes based not only on distance, but on real road and terrain conditions. 

__What makes our navigation app unique?__ Unlike mainstream navigation tools like Google Maps or Waze, which optimize purely for time and distance and will happily route you down a pothole-ridden, beat-up road without warning, Navi-Gator treats road quality as a first-class factor in how it routes you, and shows you which roads are rough, so you're never blindsided.

__How does it works?__ It works by determining the user's location, generating candidate paths between an origin and destination, and overlaying those paths on satellite/aerial imagery, capturing images of the road at regular intervals, and then a convolutional neural network (CNN) classifies each road segment from its image, and that classification is converted into an edge weight in a routing graph. The application recomputes the optimal shortest path from these condition-aware weights and renders the final route, road conditions, and turn-by-turn directions to a web front end, giving drivers a route that avoids bad roads.
_Built by 5 highly motivated CS Students._

# Project Architecture 
```
navi-gator/
├── backend/            # Python, orchestration, ML, and routing
│   ├── requirements.txt
│   └── app/
│       ├── main_file.py     
│       ├── location/      # geocoder (IP) + geopy (your address)  
│       ├── imagery/         
│       ├── capture/         
│       ├── classification/  # CNN road-condition model (train + predict)
│       └── routing/         # HPMS graph, edge weights, shortest path
├── frontend/           # Route map, directions, condition overlay (HTML/CSS)
│   └── src/
├── data/               
├── docs/               # PID, Requirements, Design, DoD, architecture
├── .env.example        
├── .gitignore
└── README.md
```
```
EXTERNAL DATA SOURCES
   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ User loc.  │  │   NJGIN    │  │   MapBox   │  │ FHWA HPMS  │
   │ (IP / addr)│  │  imagery   │  │   tiles    │  │ road data  │
   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
         └───────────────┴───────────────┴───────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   main_file.py    │  ← orchestrator
                        │                  │    location → candidate paths
                        │  geocoder/geopy  │    → imagery → capture →
                        │                  │    classify → weight → route
                        └────────┬─────────┘
                                 │ candidate paths + captured segment images
                                 ▼
                        ┌──────────────────┐
                        │  CNN Classifier   │  ← ML (TensorFlow/PyTorch)
                        │                  │    image → condition class
                        │  road-condition  │    (good … bad) + confidence
                        │  inference       │
                        └────────┬─────────┘
                                 │ condition class per segment
                                 ▼
                        ┌──────────────────┐
                        │  Routing Graph    │  ← NetworkX
                        │                  │    HPMS segments = edges
                        │  weight = length │    weight adjusted by
                        │  × condition     │    condition factor
                        └────────┬─────────┘
                                 │ lowest-cost condition-aware path
                                 ▼
                        ┌──────────────────┐
                        │  Shortest Path    │  ← Dijkstra / A*
                        │                  │    origin → destination
                        └────────┬─────────┘
                                 │ route + directions + conditions
                                 ▼
                        ┌──────────────────┐
                        │  Web Front End    │  ← HTML/CSS + Folium
                        │                  │    route map, color-coded
                        │  Folium/Leaflet  │    road conditions, directions
                        └──────────────────┘
```


## Roles: 

Product Owner: Vyrareth

Scrum Master: Edgar/Don

Developers: Cristofer, Nitin, Vyrareth, Edgar, Don

(Note: Some responsibilities are shared between people, each person will be wearing two "hats" meaning the PO, Scrum masters  will have to contribute to the development of the program due to the lack of team members. 

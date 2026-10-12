# Navi-Gator

A condition-aware navigation web app for New Jersey roads. Unlike mainstream tools
(Google Maps, Waze) that optimize purely for time and distance, Navi-Gator treats **road
quality as a first-class routing factor** — it classifies road condition from aerial
imagery, routes you around bad roads, and *shows* you which roads are rough so you're
never blindsided by potholes and degraded surfaces.

Built by the Navi-Gator team for a Rutgers Software Engineering course project.

## What It Does

* Determines the user's location (IP-based geolocation or manual address entry)
* Generates candidate paths between an origin and destination over the NJ road network
* Pulls aerial/satellite imagery along each candidate path and captures road-segment
  images at regular intervals
* Classifies each road segment's condition with a convolutional neural network (CNN)
* Converts each classification into an edge weight in a routing graph
* Recomputes the shortest *condition-aware* route and renders the route, road conditions,
  and turn-by-turn directions to a web front end

## Architecture

```
navi-gator/
├── backend/            # Python — orchestration, ML, and routing
│   ├── requirements.txt
│   └── app/
│       ├── main_file.py     # orchestrator: location → route pipeline
│       ├── location/        # geocoder (IP) + geopy (address)
│       ├── imagery/         # NJGIN datasets (primary); MapBox tiles (fallback only)
│       ├── capture/         # road-segment screenshots along a path
│       ├── classification/  # CNN road-condition model (train + predict)
│       └── routing/         # HPMS graph, edge weights, shortest path
├── frontend/           # Leaflet + OpenStreetMap route planner (geocoding + map UI)
│   ├── Geoapify_api(Test).py   # prototype: address entry → geocode → baseline route
│   └── src/
├── data/               # HPMS road data, imagery cache, model weights
├── docs/               # PID, Requirements, Design, DoD, architecture
├── .env.example        # Required env vars (e.g. MAPBOX_TOKEN) — no real secrets
├── .gitignore
└── README.md
```

```
EXTERNAL DATA SOURCES
   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ User loc.  │  │   NJGIN    │  │  MapBox    │  │ FHWA HPMS  │
   │ (IP / addr)│  │ (primary)  │  │ (fallback) │  │ road data  │
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
                        │  Web Front End    │  ← Leaflet + OpenStreetMap
                        │                  │    route map, color-coded
                        │  Leaflet/Geoapify│    road conditions, directions
                        └──────────────────┘
```

**Front-end note:** the prototype (`frontend/Geoapify_api(Test).py`) uses **Leaflet +
OpenStreetMap** for the map and **Geoapify** for geocoding and a *baseline* driving route.
Navi-Gator's own **condition-aware route** (from the CNN edge weights) renders on this same
map, and can be shown alongside the baseline route to demonstrate the difference.

## Data model (SQL schema)

Relational schema designed by the team. Hierarchy: **County → Sector → Road → Segments.**

| Table | Key columns | Notes |
|-------|-------------|-------|
| **County** | `CountyID` (PK), `StateID` (FK), `County_Name` | Exists for future expansion. |
| **Sector** | `SectorID` (PK), `CountyID` (FK), `Sector_Name`, `Sector_Uright_Lat/Long`, `Sector_Lleft_Lat/Long` | A sector is a bounding box (upper-right + lower-left corners). |
| **Road** | `RoadID` (PK), `SectorID` (FK), `Road_Name`, `Road_Type` | Roads belong to a sector. |
| **Segments** | `SegmentID` (PK), `RoadID` (FK), `length_miles`, `photo_file` | Spaced pieces of a road; `photo_file` is the captured image fed to the CNN. |

**Query & scoring flow:** the route is predetermined, so intersections are neglected. For
each **Road** along the route, the system pulls its **Segments** (each carrying a
`photo_file`), gathers the photos (e.g., into a CSV), runs them through the **CNN** to
classify condition, computes a **road score**, then reports every road's score back to the
main routing program, which adjusts edge weights and narrows down the best route.

**Runtime concepts (not stored tables):**
* `ConditionClassification` — the CNN's output for a segment photo (label, confidence).
* `RoadScore` — aggregate condition score for a road, derived from its segments.
* `Route` — ordered set of roads with total weight, directions, and condition summary.
```

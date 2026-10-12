# Navi-Gator — Project Proposal (One Page)

**Course:** Software Engineering &nbsp;|&nbsp; **Deliverable:** One-page project proposal (one submission per team)
**Status:** *Pending professor approval*

---

## Project Overview

**Navi-Gator** is a web-based map/GPS application that computes driving routes based not
only on distance but on **real road and terrain conditions**. The system determines the
user's location, generates candidate paths between an origin and destination, overlays
those paths on satellite/aerial imagery, and captures images of the road at regular
intervals. A **convolutional neural network (CNN)** classifies each road segment from its
image, and that classification is converted into an **edge weight** in a routing graph.
The application then recomputes the optimal shortest path from these condition-aware
weights and renders the final route and turn-by-turn directions to a web front end.

## Team Members — Agile Roles & Responsibilities

| Member | Agile Role | Responsibilities |
|---|---|---|
| **Vyrareth** | Product Owner & Developer | Owns product vision and priorities; maintains the PID, Requirements, Product Backlog, and Definition of Done; contributes to development |
| **Edgar** | Scrum Master & Developer | Facilitates Agile ceremonies, removes blockers, tracks sprint progress; contributes to development |
| **Don** | Scrum Master & Developer | Shares Scrum Master duties; authored the initial map-access framework; contributes to development |
| **Cristofer** | Developer | Feature implementation across subsystems |
| **Nitin** | Developer | Feature implementation across subsystems |

*All team members are developers; Scrum Master responsibilities are shared between Edgar and Don.*

## Planned Language of Choice

- **Python** — core application, orchestration, mapping, and ML. The current prototype
  uses `geocoder`, `folium`, and `geopy` (Nominatim).
- **HTML / CSS** — web front end for route display and directions (maps render to HTML
  and open in the browser).

## Planned Infrastructure / Platform

- **Imagery source (primary candidate): NJGIN Open Data statewide imagery**
  (njgin.nj.gov) — free, downloadable aerial imagery by square area, usable offline; can
  double as the road "screenshot" source by navigating the imagery. *Caveat: currency is
  ~2020.*
- **Imagery source (alternative): MapBox** satellite tiles via Folium (free tier:
  700,000 tiles/month) for live rendering. *Decision pending: NJGIN (free, offline,
  older) vs. MapBox (live, quota-limited).*
- **Road network data: FHWA HPMS GeoPackage (2024)** — national/state road segments and
  attributes, extracted with the FHWA HPMS Geospatial Data Extractor; provides the graph
  edges the system weights.
- **Location:** `geocoder` (IP-based) and `geopy`/Nominatim (address-based) geocoding.
- **Machine Learning:** CNN for road/terrain classification *(framework TBD:
  TensorFlow/Keras or PyTorch)*.
- **Graph / routing:** shortest-path over a weighted graph *(library TBD, e.g., NetworkX)*.
- **Project management & collaboration:** GitHub (version control), Trello (Agile board),
  Google Drive / Docs (documentation).
- **Deployment:** web-based; runs locally in-browser during development.

## Other Details (Progress, Methodology, Risks)

- **Methodology:** Agile / Scrum — sprints, product backlog, user stories, shared
  Definition of Done, Trello board.
- **Prototype progress:** a working map now renders in the browser and shows the user's
  location. The user can choose **IP-based location** or **manual address entry**.
- **Known limitation:** Rutgers network IP addresses resolve to New Brunswick/Piscataway,
  so IP-based location is not device-accurate on campus. **Mitigations:** manual address
  entry (works today), or a Windows-only build that reads the device's internal GPS.
- **Primary risks:** imagery currency/coverage (NJGIN ~2020), MapBox tile budget if used,
  and CNN training-data gathering and classification accuracy.
- **Success criterion:** produce condition-aware routes that measurably differ from
  distance-only routing, delivered end-to-end to the front end.

---

*Items marked TBD and the pending imagery decision should be confirmed by the team before
submission. Professor approval is required prior to proceeding.*

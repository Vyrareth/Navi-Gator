# Navi-Gator — Project Hierarchy

A digitized version of the hand-drawn project hierarchy for the Navi-Gator map GPS
web-based application. The diagrams below render automatically on GitHub.

The application computes routes that account for **real road/terrain conditions**:
it pulls satellite imagery for candidate paths, screenshots them, classifies each
segment with a CNN (ML) model, converts that classification into an **edge weight**
in a routing graph, and recalculates the shortest path from those weights.

---

## 1. System Hierarchy

How the pieces of the project relate. `Main_file.py` is the orchestrator that calls
each subsystem. The **Paperwork** branch is owned by the Product Owner and feeds the
build.

```mermaid
flowchart TD
    subgraph PO["Paperwork — Product Owner Artifacts"]
        PID["PIDs / Definition of Done"]
        REQ["Requirements Doc"]
        BACK["Product Backlog"]
    end

    FE["Front End<br/>(HTML, CSS)"]

    MAIN["Main_file.py<br/>(Orchestrator)"]

    subgraph SUB["Core Subsystems"]
        MAP["What Map or<br/>System to Use"]
        LOC["Location<br/>Determination"]
        SAT["Satellite Access"]
        SHOT["Screenshot System"]
        NODE["Mapping Node / Weights"]
        CNN["Read Classification<br/>CNN (ML)"]
    end

    subgraph MLDETAIL["Classification Concerns"]
        TILE["1 Tile"]
        OPT["Optimization"]
        DATA["Data Gathering"]
        METHOD["Method for<br/>Classification"]
    end

    PO --> FE
    MAIN --> FE
    MAIN --> MAP
    MAIN --> LOC
    MAIN --> SAT
    MAIN --> NODE
    MAIN --> SHOT
    MAIN --> CNN
    MAIN -. informs .-> REQ
    MAIN -. informs .-> BACK

    SAT --> SHOT
    SHOT --> CNN
    CNN --> NODE
    CNN --> TILE
    CNN --> OPT
    CNN --> DATA
    CNN --> METHOD
```

---

## 2. Runtime Pipeline

The end-to-end flow when a user requests a route.

```mermaid
flowchart LR
    A["Grab location"] --> B["Find short paths"]
    B --> C["Map pulls onto<br/>satellite"]
    C --> D["Screenshot at<br/>regular intervals"]
    D --> E["Add classification<br/>to road / edge weight"]
    E --> F["Put that edge<br/>into graph"]
    F --> G["Calculate new<br/>shortest route"]
    G --> H["Project to main page<br/>+ directions set"]
    H --> I["Write path into<br/>HTML file → Front End"]
```

---

## 3. Notes & Constraints

- **Map tile source:** MapBox — **700,000 free tiles per month**. This is a real
  budget constraint worth tracking (screenshotting at regular intervals along many
  candidate paths consumes tiles quickly).
- **Orchestrator:** `Main_file.py` coordinates location, satellite access,
  screenshot capture, classification, and graph/weight updates, then hands the final
  path to the front end.
- **ML classification** (CNN) turns a satellite screenshot of a road segment into a
  weight that biases routing away from poor-quality roads.

---

*This document is a digitized reference of the team's hand-drawn hierarchy. Edit the
Mermaid blocks above to keep it in sync as the architecture evolves.*

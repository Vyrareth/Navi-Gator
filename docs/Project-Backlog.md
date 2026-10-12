======================================================================
NAVI-GATOR — PROJECT BACKLOG (ALL SPRINTS)
======================================================================
VERSION NO.:     0.0.1
DATE ISSUED:     9/28/2026
PRODUCT OWNER:   Vyrareth (Vy)

----------------------------------------------------------------------
How this backlog is organized
----------------------------------------------------------------------
The project is broken into WEEKLY SPRINTS. This document is the master
Project Backlog — every task from Week 0 to the final week — grouped by
sprint. Each sprint also has its own detailed sprint backlog (e.g. the
Sprint 0 Backlog). Items are built in dependency order: you cannot
classify roads before capturing images, cannot capture before pulling
imagery, cannot route before the graph exists.

Epics:  E1 Location · E2 Imagery · E3 Capture · E4 Classification (CNN)
        E5 Graph & Routing · E6 Front End · E7 Project Management / Docs

Status: DONE | IN PROGRESS | TODO
NOTE: Sprint count and dates below are a proposed roadmap — adjust to
your actual course end date. Confirm the number of weeks with the team.

======================================================================
SPRINT 0 — Week 0 — FOUNDATION / SETUP
Goal: paperwork, repo, research, and a first location prototype.
======================================================================
| ID    | Item                                   | Epic | Priority | Status      |
|-------|----------------------------------------|------|----------|-------------|
| S0-1  | Project Proposal (approved)            | E7   | P1       | DONE        |
| S0-2  | Project Initiation Document (PID)      | E7   | P1       | DONE        |
| S0-3  | Definition of Done (Sprint 0)          | E7   | P1       | IN PROGRESS |
| S0-4  | Sprint 0 Backlog + this Project Backlog| E7   | P1       | IN PROGRESS |
| S0-5  | Trello board created + invites sent    | E7   | P1       | TODO        |
| S0-6  | Roles & responsibilities assigned      | E7   | P1       | DONE        |
| S0-7  | Architecture / project hierarchy doc   | E7   | P2       | DONE        |
| S0-9  | GitHub repo + backend/frontend/docs    | E7   | P1       | DONE        |
| S0-13 | Location approach research (IP/addr/GPS)| E1  | P1       | DONE        |
| S0-14 | Imagery research: NJGIN vs MapBox      | E2   | P1       | IN PROGRESS |
| S0-15 | Road data research: FHWA HPMS          | E5   | P2       | IN PROGRESS |
| S0-16 | CNN classification approach research   | E4   | P2       | TODO        |
| S0-17 | Location determination prototype       | E1   | P1       | DONE        |
| S0-18 | Frontend routing prototype (Geoapify+Leaflet)| E6| P1     | DONE        |

======================================================================
SPRINT 1 — Week 1 — REQUIREMENTS, DESIGN & LOCATION
Goal: lock requirements/design; harden location; baseline map render.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S1-1  | Requirements document (User/Solution/Compliance)| E7 | P1       | TODO   |
| S1-2  | Design document (architecture, data model)    | E7   | P1       | TODO   |
| S1-3  | Finalize imagery source decision (NJGIN/MapBox)| E2  | P1       | TODO   |
| S1-4  | Harden location module (IP + address, errors) | E1   | P1       | TODO   |
| S1-5  | Baseline map renders to browser (Folium)      | E6   | P2       | TODO   |
| S1-6  | requirements.txt + repo README finalized      | E7   | P2       | TODO   |

======================================================================
SPRINT 2 — Week 2 — IMAGERY ACCESS & ROUTE GRAPH
Goal: pull imagery along a path; build the road graph from HPMS.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S2-1  | Candidate path generation (origin → destination)| E5 | P1       | TODO   |
| S2-2  | Pull aerial/satellite imagery for a path      | E2   | P1       | TODO   |
| S2-3  | Load HPMS road segments into a graph (NetworkX)| E5  | P1       | TODO   |
| S2-4  | Overlay a candidate path on the imagery        | E2   | P2       | TODO   |

======================================================================
SPRINT 3 — Week 3 — SEGMENT CAPTURE
Goal: capture road-segment images at regular intervals along a path.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S3-1  | Screenshot road segments at intervals         | E3   | P1       | TODO   |
| S3-2  | Associate each image with its road segment     | E3   | P1       | TODO   |
| S3-3  | Store/organize captured images (cache)         | E3   | P2       | TODO   |

======================================================================
SPRINT 4 — Week 4 — CNN CLASSIFICATION (BUILD & TRAIN)
Goal: gather/label data and train the road-condition model.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S4-1  | Gather + label road-condition training images | E4   | P1       | TODO   |
| S4-2  | Define CNN model (chosen framework)           | E4   | P1       | TODO   |
| S4-3  | Train initial model + record accuracy         | E4   | P1       | TODO   |

======================================================================
SPRINT 5 — Week 5 — CLASSIFICATION → WEIGHTS → ROUTING
Goal: turn condition into edge weights and compute the smart route.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S5-1  | Run model inference on captured segments      | E4   | P1       | TODO   |
| S5-2  | Convert condition class → edge weight          | E5   | P1       | TODO   |
| S5-3  | Apply weights to graph edges                   | E5   | P1       | TODO   |
| S5-4  | Shortest-path (Dijkstra/A*) on weighted graph | E5   | P1       | TODO   |

======================================================================
SPRINT 6 — Week 6 — FRONT END DISPLAY
Goal: show the route, road conditions, and directions.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S6-1  | Render computed route on the map              | E6   | P1       | TODO   |
| S6-2  | Color-code road conditions (overlay)          | E6   | P1       | TODO   |
| S6-3  | Turn-by-turn directions panel                 | E6   | P2       | TODO   |
| S6-4  | Route preference (fastest vs smoothest)       | E6   | P3       | TODO   |

======================================================================
SPRINT 7 — Week 7 — INTEGRATION & TESTING
Goal: end-to-end condition-aware routing, tested.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S7-1  | End-to-end pipeline via main_file.py          | E5   | P1       | TODO   |
| S7-2  | Unit + integration tests                      | E7   | P1       | TODO   |
| S7-3  | Collect verification evidence                 | E7   | P2       | TODO   |
| S7-4  | Bug fixes / stabilization                     | E7   | P1       | TODO   |

======================================================================
SPRINT 8 — Week 8 — POLISH, ACCEPTANCE & FINAL DEMO
Goal: finalize, get acceptance, present.
======================================================================
| ID    | Item                                          | Epic | Priority | Status |
|-------|-----------------------------------------------|------|----------|--------|
| S8-1  | UI/UX polish                                  | E6   | P2       | TODO   |
| S8-2  | Acceptance Statement (course template)        | E7   | P1       | TODO   |
| S8-3  | Finalize all documentation                    | E7   | P1       | TODO   |
| S8-4  | Final demo / presentation                     | E7   | P1       | TODO   |

----------------------------------------------------------------------
Roadmap notes (confirm with team)
----------------------------------------------------------------------
- Sprints 1–8 are a proposed plan; compress or extend to match your real
  course calendar (final week / demo date).
- Detailed acceptance criteria live in each sprint's own sprint backlog.
- IDs are stable across both docs (S0-* here match the Sprint 0 Backlog).

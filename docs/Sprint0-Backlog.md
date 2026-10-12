======================================================================
NAVI-GATOR — SPRINT 0 BACKLOG
======================================================================
VERSION NO.:     0.0.1
DATE ISSUED:     9/28/2026
SPRINT:          Sprint 0 (Foundation / Setup)
PRODUCT OWNER:   Vyrareth (Vy)

----------------------------------------------------------------------
Purpose
----------------------------------------------------------------------
Sprint 0 is the foundation sprint: project paperwork, repository and
environment setup, data-source research, and a first location prototype.
No production feature code is expected this sprint — the goal is to be
ready to build in Sprint 1. Items are prioritized P1 (highest) to P3.

Legend — Status: DONE | IN PROGRESS | TODO
         Priority: P1 (must finish this sprint) … P3 (nice to have)

----------------------------------------------------------------------
A. Project Management & Documentation
----------------------------------------------------------------------
| ID    | Item                                   | Assignee | Priority | Points | Status      |
|-------|----------------------------------------|----------|----------|--------|-------------|
| S0-1  | Project Proposal (1-page, approved)    | Vy       | P1       | 2      | DONE        |
| S0-2  | Project Initiation Document (PID)      | Vy       | P1       | 3      | DONE        |
| S0-3  | Definition of Done (Sprint 0)          | Vy / Don | P1       | 2      | IN PROGRESS |
| S0-4  | Product Backlog (Sprint 0)             | Vy       | P1       | 2      | IN PROGRESS |
| S0-5  | Trello board created + invites sent    | Vy       | P1       | 1      | TODO        |
| S0-6  | Roles & responsibilities assigned      | Vy       | P1       | 1      | DONE        |
| S0-7  | Architecture / project hierarchy doc   | Vy       | P2       | 2      | DONE        |
| S0-8  | Requirements document (v1 draft)       | Team     | P2       | 3      | TODO (due Oct 4) |

Acceptance criteria:
- S0-1: One-page proposal covering problem, team/roles, language, infrastructure;
  submitted and approved by professor.
- S0-2: PID follows course template; scope, roles, deliverables filled; N/A sections justified.
- S0-3: DoD document completed and signed off by Scrum Master (Don).
- S0-4: This backlog — all Sprint 0 items captured, prioritized, with owners and status.
- S0-5: Trello board exists with To Do / In Progress / Review / Done lists; all 5 members invited.
- S0-6: Product Owner, Scrum Master(s), and Developers named and agreed.
- S0-7: Directory tree, data-flow diagram, and data model documented (architecture.md).
- S0-8: User / Solution / Compliance requirements drafted per course template.

----------------------------------------------------------------------
B. Environment & Repository
----------------------------------------------------------------------
| ID    | Item                                   | Assignee | Priority | Points | Status      |
|-------|----------------------------------------|----------|----------|--------|-------------|
| S0-9  | GitHub repo created (Navi-Gator)       | Vy       | P1       | 1      | DONE        |
| S0-10 | backend / frontend / docs scaffolding  | Vy / Don | P1       | 1      | DONE        |
| S0-11 | .gitignore, .env.example, README       | Vy       | P2       | 1      | IN PROGRESS |
| S0-12 | requirements.txt (Python deps pinned)  | Team     | P2       | 1      | TODO        |

Acceptance criteria:
- S0-9: Repository exists on GitHub and all members can push/pull.
- S0-10: backend/, frontend/, docs/ folders present and committed.
- S0-11: Secrets excluded from git; .env.example lists needed vars (e.g. MAPBOX_TOKEN); README describes the project.
- S0-12: requirements.txt lists folium, geocoder, geopy (and future deps) with versions.

----------------------------------------------------------------------
C. Research / Spikes (time-boxed investigations)
----------------------------------------------------------------------
| ID    | Item                                   | Assignee | Priority | Points | Status      |
|-------|----------------------------------------|----------|----------|--------|-------------|
| S0-13 | Location approach (IP vs address vs GPS)| Don     | P1       | 2      | DONE        |
| S0-14 | Imagery source: NJGIN vs MapBox        | Team     | P1       | 2      | IN PROGRESS |
| S0-15 | Road network data: FHWA HPMS extract   | Team     | P2       | 3      | IN PROGRESS |
| S0-16 | CNN classification approach & framework| Team     | P2       | 3      | TODO        |

Acceptance criteria:
- S0-13: Documented finding — IP geolocation resolves RU network to New Brunswick/Piscataway;
  manual address entry works; Windows-only internal GPS is a possible fallback.
- S0-14: Recommendation written comparing NJGIN (free, offline, ~2020) vs MapBox
  (live tiles, 700k/month free); decision recorded.
- S0-15: HPMS GeoPackage successfully extracted for NJ; confirmed it provides road segments/edges.
- S0-16: Short write-up on CNN approach and chosen framework (TensorFlow/Keras or PyTorch).

----------------------------------------------------------------------
D. Prototype (Spike)
----------------------------------------------------------------------
| ID    | Item                                   | Assignee | Priority | Points | Status      |
|-------|----------------------------------------|----------|----------|--------|-------------|
| S0-17 | Location determination prototype       | Don      | P1       | 3      | DONE        |
|       | (basicTwoLocMap.py)                    |          |          |        |             |
| S0-18 | Frontend routing prototype             | Ice-Shard-blizz | P1 | 3    | DONE        |
|       | (Geoapify + Leaflet)                   | (confirm name)  |    |      |             |

Acceptance criteria:
- S0-17: Running the script renders a map in the browser and shows the user's location;
  user can choose IP-based location or manual address entry; origin + destination markers appear.
- S0-18: Running Geoapify_api(Test).py generates a Leaflet/OpenStreetMap page served locally;
  user enters start + destination addresses, and a driving route (via Geoapify geocoding +
  routing) draws on the map with start/destination markers. NOTE: this uses Geoapify's
  baseline routing; the condition-aware route (CNN weights) is built in later sprints and
  will render on this same map. FOLLOW-UP: revoke the API key committed in
  README_Geoapify.txt and move keys to a git-ignored .env.

----------------------------------------------------------------------
Sprint 0 Summary
----------------------------------------------------------------------
- Total items: 17   |   DONE: 7   |   IN PROGRESS: 5   |   TODO: 5
- Due tonight (P1, In Progress): S0-3 Definition of Done, S0-4 Product Backlog
- Carrying into Sprint 1: Requirements doc (S0-8), imagery/HPMS/CNN research, requirements.txt

----------------------------------------------------------------------
Notes for the team (confirm before finalizing)
----------------------------------------------------------------------
- Assignees on research/setup items are suggestions — Vy to confirm with the team.
- Story points are rough (1 = trivial, 8 = large); adjust in sprint planning.
- Item S0-8 (Requirements) is due Oct 4, listed here for visibility; may formally
  belong to Sprint 1 depending on your sprint boundaries.

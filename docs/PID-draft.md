# Project Initiation Document (PID) — Navi-Gator

> **How to use this draft:** Paste into `01 - PID.docx`, keeping the template's section
> numbering. Text in **[BRACKETS]** is a team decision to fill or confirm. Under each
> section there is a *Section completed by:* line — put your name there for the
> individually-graded portion. Delete these three quote lines before submitting.
>
> **Document version:** 1.0 &nbsp;|&nbsp; **Version date:** [DATE] &nbsp;|&nbsp; **Approvals:** None required

---

## 1. Purpose

This Project Initiation Document defines the SDLC elements necessary to declare the
**Navi-Gator** solution, Version 0.1, fit for its intended use as a Software Engineering
course project. Navi-Gator is a web-based map/GPS application that computes driving routes
weighted by real road and terrain conditions.

*Section completed by: ______________*

## 2. Scope

This project delivers a prototype web application that determines a user's location,
generates candidate routes between an origin and destination within New Jersey, acquires
aerial/satellite imagery along those routes, classifies road-segment condition with a
convolutional neural network (CNN), converts each classification into a graph edge weight,
recomputes the shortest condition-aware route, and renders the route with directions to a
web front end.

Because this is a course project, no production Configuration Items (CMDB IDs) are in
scope. The in-scope solution components are: Location Determination, Imagery Access,
Screenshot/Segment Capture, CNN Classification, Mapping Graph & Weights, Shortest-Path
Routing, and the HTML/CSS Front End, all orchestrated by `Main_file.py`.

*Section completed by: ______________*

### 2.1 Exclusions, Assumptions, and Limitations

- **Exclusions:** real-time traffic data; a native mobile application; coverage beyond New
  Jersey; production hosting, authentication, and long-term data storage.
- **Assumptions:** NJGIN imagery and FHWA HPMS road data remain publicly available; team
  members have a working Python environment; the target route area is within NJ.
- **Limitations:** candidate aerial imagery (NJGIN) currency is approximately 2020;
  Rutgers network IP addresses geolocate to New Brunswick/Piscataway, so IP-based location
  is not device-accurate on campus; free-tier service quotas (e.g., MapBox 700,000
  tiles/month) apply if used.

*Section completed by: ______________*

## 3. Intended Use

**Business process:** a driver wants a route that accounts for road quality, not just
distance. Navi-Gator automates this by classifying road segments from aerial imagery and
biasing route selection away from poor-quality roads.

**High-level architecture:** `Main_file.py` orchestrates the subsystems — Location
Determination (`geocoder`, `geopy`/Nominatim), Imagery Access ([NJGIN imagery **or**
MapBox tiles — decision pending]), Screenshot/Segment Capture, CNN Classification (ML),
Mapping Graph & Weights, Shortest-Path Routing, and the HTML/CSS Front End. Routes are
rendered to an HTML file and opened in the browser.

**Dependencies:** Python and libraries (`folium`, `geocoder`, `geopy`); an imagery source;
FHWA HPMS GeoPackage road data; an ML framework [TensorFlow/Keras or PyTorch — TBD]; a
graph/routing library [e.g., NetworkX — TBD].

*Section completed by: ______________*

## 4. Requirements

Requirements are maintained in a separate document: the **Navi-Gator Requirements
Document** (`02 - Requirements.docx`). Refer to that document for User, Solution, and
Compliance requirements.

*Section completed by: ______________*

## 5. Solution Profile

**Not Applicable.** As a course prototype, Navi-Gator maintains no privacy records of
record, satisfies no business electronic signatures, serves as a System of Record for no
records, and includes no regulated audit trail. User location is used transiently to
center the map and is not persisted.

*Section completed by: ______________*

## 6. Design and Installation Information

Design information is maintained in a separate document: the **Navi-Gator Design
Document** (`03 - Design.docx`). At a high level, installation for the prototype consists
of a local Python environment with the required libraries; the application generates an
HTML map file that opens in a standard web browser.

*Section completed by: ______________*

## 7. Deliverables List

See the Appendix (Element Deliverables and Responsibilities Matrix) for the full list.
Planned deliverables: this PID, the Requirements Document, the Design Document, the
Definition of Done, the Environment Acceptance record, the Acceptance Statement, and the
application source code (GitHub).

*Section completed by: ______________*

## 8. Deployment Strategy

The solution is deployed as a locally-run web application for the duration of the course;
there is no site-specific or production deployment.

### 8.1 Strategic Deployment Approach Overview

1. **Configuration approach:** no local configuration; a single shared codebase.
2. **Deployment model:** single deployment effort; each developer runs the app locally in
   a browser.
3. **Localization approach:** English only.
4. **Additional characteristics:** none.

### 8.2 Training Impact

**Not Applicable.** No end-user or support training is required beyond the project README
for a course prototype.

### 8.3 User Access

Local execution only; no authentication or role-based access is implemented in the
prototype.

### 8.4 Support Approach

The development team maintains the solution via GitHub issues and Trello during the course.
There is no transition to Business-as-Usual (BAU) support.

*Section completed by: ______________*

## 9. Verification Approach

Requirements will be verified through a combination of unit tests (Python), manual
functional testing of each subsystem, and an end-to-end demonstration of route
computation. Evidence (test results, screenshots, demo notes) will be captured in the
GitHub repository under `docs/`.

*Section completed by: ______________*

## 10. Verification Evidence

Verification evidence will be collected during the verification effort and stored in the
GitHub repository (`docs/`) and presented at the project demonstration. *[Currently
pending — populate as verification is performed.]*

*Section completed by: ______________*

## 11. Roles and Responsibilities

| Role | Name(s) | Responsibilities |
|---|---|---|
| Product Owner | Vyrareth | Owns product vision, backlog, requirements, PID, and Definition of Done |
| Scrum Master | Edgar, Don | Facilitate Agile ceremonies, remove blockers, track sprint progress |
| Developers | Cristofer, Nitin, Vyrareth, Edgar, Don | Design, implement, and verify solution components |

*Section completed by: ______________*

## 12. Terms and Definitions

| Term or Acronym | Definition |
|---|---|
| CNN | Convolutional Neural Network — ML model used to classify road-segment images |
| HPMS | Highway Performance Monitoring System (FHWA) — source of road network data |
| NJGIN | New Jersey Geographic Information Network — source of statewide aerial imagery |
| Geocoding | Converting an address into latitude/longitude coordinates |
| Edge weight | A cost assigned to a graph edge (road segment) used in shortest-path routing |
| Shortest path | The minimum-cost route between two nodes in a weighted graph |
| PID | Project Initiation Document |
| DoD | Definition of Done |

*Section completed by: ______________*

## 13. Supporting References

| Identifier | Title |
|---|---|
| REF-1 | NJGIN Open Data Imagery — https://njgin.nj.gov/njgin/edata/imagery/ |
| REF-2 | FHWA Highway Performance Monitoring System — https://www.fhwa.dot.gov/policyinformation/hpms.cfm |
| REF-3 | MapBox (satellite tiles) — https://www.mapbox.com |
| REF-4 | Folium / GeoPy documentation |

*Section completed by: ______________*

## 14. Revision History

| Version | Version Date | Revisions |
|---|---|---|
| 1.0 | [DATE] | Initial Release |

*Section completed by: ______________*

---

## Appendix A: Element Deliverables and Responsibilities Matrix

| SDLC Element | Justification / Comments (Document Name & Location) | Business Unit | IT Technical |
|---|---|---|---|
| Plan (PID) | Create — this document (`01 - PID.docx`) | — | C |
| Requirements | Create — `02 - Requirements.docx` | C | C |
| Design/Installation Information | Create — `03 - Design.docx` | — | C |
| Verification Evidence | Create — GitHub `docs/` | — | C |
| Acceptance Statement | Create/Approve — `11 - Acceptance Statement.docx` | A | C, A |

*C = Create, A = Approve*

---

## Assignment checklist (delete before submitting)

- [ ] Roles & responsibilities with names included (Section 11)
- [ ] Each contributor's name added to the sections they completed
- [ ] **Trello project created and invitations sent** — paste board link: [TRELLO LINK]
- [ ] Version date filled in; blue instructional text removed from the .docx

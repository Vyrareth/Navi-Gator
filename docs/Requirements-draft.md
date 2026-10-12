# Requirements Document — Navi-Gator

> **How to use this draft:** Paste into `02 - Requirements.docx`, keeping the template's
> section numbering and the three requirement tables (User / Solution / Compliance).
> Columns **RCR** (Requirements Criticality Rating), **RC** (Requirements Classification),
> and **RRR** (Requirements Risk Rating) come from the Requirements Risk Assessment — fill
> per your course's process (suggested starter values are in brackets; confirm with the
> professor). **[BRACKETS]** = team decision. Under each section, put your name on the
> *Section completed by* line for the individually-graded portion. Delete this quote block
> before submitting.
>
> **Version:** 1.0 &nbsp;|&nbsp; **Date:** [DATE] &nbsp;|&nbsp; **Approvals:** None required

---

## 1. Purpose

This document records the User, Solution, and Compliance requirements for **Navi-Gator**,
a web-based condition-aware routing application, in accordance with the course's SDLC
process. It is maintained throughout the life of the in-scope solution.

*Section completed by: ______________*

## 2. Scope

This document is limited to the requirements for the Navi-Gator prototype. Because this is
a course project, there are no production Application Master or Deployment Configuration
Item names; the in-scope components are Location Determination, Imagery Access,
Screenshot/Segment Capture, CNN Classification, Mapping Graph & Weights, Shortest-Path
Routing, and the HTML/CSS Front End.

*Section completed by: ______________*

### 2.1 Exclusions, Assumptions, and Limitations

- **Exclusions:** real-time traffic; native mobile app; coverage beyond New Jersey;
  production hosting, authentication, and persistent storage.
- **Assumptions:** NJGIN imagery and FHWA HPMS data remain available; team has a working
  Python environment.
- **Limitations:** NJGIN imagery currency ~2020; Rutgers IPs geolocate to New
  Brunswick/Piscataway; free-tier quotas apply if MapBox is used.

*Section completed by: ______________*

## 3. Requirements

Requirement identifiers are unique. The **Scope** column holds the release in which a
requirement was implemented (or "Out of Scope"). RCR/RC/RRR are populated for testable
requirements per the Requirements Risk Assessment. *(Suggested starter risk values are
shown in brackets — confirm against your course's rating scale.)*

### 3.1 User Requirements

| Req# | Requirement Description | Scope | RCR | RC | RRR |
|---|---|---|---|---|---|
| UR-1 | As a user, I can provide my starting location either by IP-based detection or by entering an address, so routing can begin from my position. | R1 | [High] | [Functional] | [Med] |
| UR-2 | As a user, I can enter a destination address and receive a computed route to it. | R1 | [High] | [Functional] | [High] |
| UR-3 | As a user, I am shown the route on a map with turn-by-turn directions in my browser. | R1 | [High] | [Functional] | [Med] |
| UR-4 | As a user, the suggested route accounts for road/terrain condition, not distance alone. | R1 | [High] | [Functional] | [High] |
| UR-5 | As a user, I am informed when my location cannot be determined accurately (e.g., campus IP limitation) and can enter an address instead. | R1 | [Med] | [Usability] | [Low] |

*Section completed by: ______________*

### 3.2 Solution Requirements

| Req# | Requirement Description | Scope | RCR | RC | RRR |
|---|---|---|---|---|---|
| SR-1 | The system shall determine latitude/longitude via `geocoder` (IP) and `geopy`/Nominatim (address). | R1 | [High] | [Functional] | [Med] |
| SR-2 | The system shall generate one or more candidate paths between origin and destination. | R1 | [High] | [Functional] | [High] |
| SR-3 | The system shall acquire aerial/satellite imagery along candidate paths from [NJGIN imagery **or** MapBox tiles — decision pending]. | R1 | [High] | [Functional] | [High] |
| SR-4 | The system shall capture road-segment images at regular intervals along each candidate path. | R1 | [High] | [Functional] | [High] |
| SR-5 | The system shall classify each road segment's condition using a CNN model. | R1 | [High] | [Functional] | [High] |
| SR-6 | The system shall convert each classification into an edge weight in a routing graph. | R1 | [High] | [Functional] | [High] |
| SR-7 | The system shall compute the shortest condition-aware path over the weighted graph. | R1 | [High] | [Functional] | [High] |
| SR-8 | The system shall load road network segments from the FHWA HPMS GeoPackage (2024). | R1 | [Med] | [Functional] | [Med] |
| SR-9 | The system shall render the final route and directions to an HTML/CSS front end that opens in a browser. | R1 | [High] | [Functional] | [Med] |
| SR-10 | The system shall keep any API keys/tokens out of source control. | R1 | [Med] | [Security] | [Med] |

*Section completed by: ______________*

### 3.3 Compliance Requirements

**Not Applicable.** As a course prototype, Navi-Gator is subject to no regulatory (e.g.,
GMP, HIPAA) compliance requirements. It uses publicly available government/open data
(NJGIN, FHWA HPMS) and third-party services under their standard free-tier terms; the team
will observe those usage terms and licenses.

*Section completed by: ______________*

## 4. Roles and Responsibilities

| Role | Name(s) | Responsibilities |
|---|---|---|
| Product Owner | Vyrareth | Defines and prioritizes requirements; accepts completed items |
| Scrum Master | Edgar, Don | Facilitate process; remove blockers |
| Developers | Cristofer, Nitin, Vyrareth, Edgar, Don | Implement and verify requirements |

*Section completed by: ______________*

## 5. Terms and Definitions

| Term or Acronym | Definition |
|---|---|
| CNN | Convolutional Neural Network used to classify road-segment images |
| HPMS | Highway Performance Monitoring System (FHWA) road network data |
| NJGIN | New Jersey Geographic Information Network aerial imagery |
| Edge weight | Cost assigned to a road segment in the routing graph |
| Geocoding | Converting an address to latitude/longitude |

*Section completed by: ______________*

## 6. Supporting References

| Identifier | Title |
|---|---|
| REF-1 | NJGIN Open Data Imagery — https://njgin.nj.gov/njgin/edata/imagery/ |
| REF-2 | FHWA HPMS — https://www.fhwa.dot.gov/policyinformation/hpms.cfm |
| REF-3 | MapBox — https://www.mapbox.com |

*Section completed by: ______________*

## 7. Revision History

| Version | Version Date | Revisions |
|---|---|---|
| 1.0 | [DATE] | Initial Release |

*Section completed by: ______________*

---

## Non-functional requirements to consider (from the template's appendix — optional)

The template's appendix lists non-functional categories. The ones most relevant to
Navi-Gator, if you want to add a few:

- **Usability:** location entry and route display should be understandable without
  training; clear message on the campus-IP location limitation.
- **Performance:** route computation and render complete in a reasonable time; imagery/tile
  requests stay within free-tier limits.
- **Reliability:** the app degrades gracefully when location cannot be determined (falls
  back to manual address entry).
- **Licensing/Data:** NJGIN and HPMS are public data; MapBox free tier is 700,000
  tiles/month — observe the terms.

## Assignment checklist (delete before submitting)

- [ ] Each contributor's name added to the sections they completed
- [ ] RCR / RC / RRR values confirmed against the course's rating scale
- [ ] Imagery decision resolved in SR-3 (or left as pending if intended)
- [ ] Version date filled in; blue instructional text removed from the .docx

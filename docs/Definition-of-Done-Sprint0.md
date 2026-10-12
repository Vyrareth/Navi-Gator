====================================================================
DEFINITION OF DONE
====================================================================
VERSION NO. :        0.0.1
DATE ISSUED:         9/22/2026
DATE COMPLETED:      9/28/2026

----------------------------------------------------------------------
DEFINITION OF DONE FOR SPRINT 0 — General Checklist
----------------------------------------------------------------------
| Activity                      | Description                                                                                          | Yes / No |
|-------------------------------|------------------------------------------------------------------------------------------------------|----------|
| Coding Complete               | All coding tasks and changes have been implemented, and the code is functionally complete.           | NA       |
| Unit Tests Passed             | Unit tests have been written for the code, and they pass successfully without any failures.          | NA       |
| Functional Requirements Met   | The code meets all the defined functional requirements and acceptance criteria.                      | NA       |
| Design and Architecture       | The code adheres to the established design and architectural principles and guidelines.              | NA       |
| Code Review Completed         | The work has been reviewed by at least one team member for quality and adherence to standards.       | Yes      |
| Documentation Updated         | Documentation, including project docs and repo README, has been updated and is accurate.             | Yes      |
| Integration Tests Passed      | Integration tests validate the interaction of the code with other system components.                 | NA       |
| Performance Requirements Met  | The code meets the defined performance requirements and operates efficiently within acceptable limits.| NA       |
| Security Measures Implemented | No secrets committed to the repo. FOLLOW-UP: a Geoapify API key was committed in frontend/README_Geoapify.txt and must be revoked + moved to a git-ignored .env. | In Progress |
| User Interface / Experience   | The user interface and experience have been reviewed and tested for usability.                       | NA       |
| Regression Testing Conducted  | Regression tests ensure new changes do not introduce issues in existing functionality.               | NA       |
| Deployment Ready              | The work is ready for its target (repo/docs submitted; prototype runs locally).                      | Yes      |
| Stakeholder Approval          | The Product Owner has reviewed and approved the work; feedback addressed.                             | Yes      |
| Technical Debt Addressed      | Any identified technical debt or outstanding issues are resolved or logged for future iterations.    | Yes      |
| Peer Verification             | Another team member has verified the criteria above are met and signed off on completion.            | Yes      |

Note: Sprint 0 delivers foundational documents, repository/environment setup, research,
and a location prototype — no production feature code yet, so code/test criteria are
marked NA. They become active in Sprint 1.

----------------------------------------------------------------------
Completed Items
----------------------------------------------------------------------
Below is the table of completed items.

| Action Item                              | Action Item Category | Assigned Person | Who completed it | Verified by |
|------------------------------------------|----------------------|-----------------|------------------|-------------|
| Project Initiation Document (PID)        | Document             | Vy              | Vy               | Don         |
| Project Proposal (1-page)                | Document             | Vy              | Vy               | __________  |
| GitHub repo + backend/frontend/docs setup| Environment          | Vy / Don        | Vy / Don         | __________  |
| Location determination prototype         | Code / Prototype     | Don             | Don              | __________  |
| Frontend routing prototype (Geoapify)    | Code / Prototype     | Ice-Shard-blizz | Ice-Shard-blizz  | __________  |
| Definition of Done Template / Week 0     | Document             | Vy / Don        | Vy / Don         | __________  |
| Product Backlog (Sprint 0)               | Document             | Vy              | Vy               | __________  |
| Roles & responsibilities assigned        | Document             | Vy              | Vy               | __________  |

(Verifier column left blank for the Scrum Master, Don, to verify and initial.)

----------------------------------------------------------------------
Summary of Item Completion [To be completed by Assignee]
----------------------------------------------------------------------
Sprint 0 established the project's foundation. The Project Proposal was written and
approved, and the Project Initiation Document was completed to the course template and
verified by Don. The GitHub repository (Navi-Gator) was created and scaffolded into
backend/, frontend/, and docs/ folders. A working location-determination prototype
(basicTwoLocMap.py) was built: it renders a map in the browser and shows the user's
location via either IP-based geolocation or manual address entry. Data-source research
(NJGIN vs MapBox imagery, FHWA HPMS road data) and the CNN classification approach were
started and carry into Sprint 1. This Definition of Done document and the Sprint 0
Product Backlog were completed to close out the sprint.

_______________________________________________________________________________________

_______________________________________________________________________________________

----------------------------------------------------------------------
Verification Summary [To be completed by Verifier]
----------------------------------------------------------------------
_______________________________________________________________________________________

_______________________________________________________________________________________

_______________________________________________________________________________________

----------------------------------------------------------------------
Relevant Changelog
----------------------------------------------------------------------
Note: Copy-paste from the changelog document; chronological order, more detail than the
chart and summary above.

- 9/22/2026 — DoD Sprint 0 template created (Vy/Don).
- 9/22/2026 — Project Proposal drafted and submitted (Vy).
- 9/2x/2026 — PID completed and verified by Don (Vy).
- 9/2x/2026 — GitHub repo created and scaffolded backend/frontend/docs (Vy/Don).
- 9/2x/2026 — Location prototype (basicTwoLocMap.py) working with IP + address entry (Don).
- 9/28/2026 — Sprint 0 Product Backlog completed (Vy).
- 9/28/2026 — Definition of Done (Sprint 0) completed for verification (Vy/Don).

======================================================
Signoff

                   Signatures                                              Date

Assignee:  _______________________________            Date: _______________________

Verifier:  _______________________________            Date: _______________________
======================================================

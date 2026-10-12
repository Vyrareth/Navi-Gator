# Definition of Done — Navi-Gator

> **How to use this draft:** Paste into the `Definition-of-Done-Template.xlsx` (sheet
> "User Story"). This is the team's shared agreement for when any user story / work item is
> considered "Done." The **Applies?** column marks whether each criterion is part of
> Navi-Gator's DoD; the **Description (tailored)** column adapts the generic activity to
> this project. Fill the **Section completed by** column with your name for the
> individually-graded portion. Delete this quote block before submitting.
>
> **Version:** 1.0 &nbsp;|&nbsp; **Date:** [DATE]

A work item is **Done** only when every criterion marked *Yes* below is satisfied and
verified.

| # | Activity | Applies? | Description (tailored to Navi-Gator) | Section completed by |
|---|---|---|---|---|
| 1 | Code Complete | Yes | All coding tasks for the story are implemented and functionally complete; committed to the feature branch on GitHub. | |
| 2 | Unit Tests Passed | Yes | Unit tests are written for new logic (e.g., geocoding, weight calculation, path search) and pass without failures. | |
| 3 | Functional Requirements Met | Yes | The item meets its acceptance criteria and the matching requirement in the Requirements Document. | |
| 4 | Design and Architecture | Yes | Code follows the agreed structure — subsystems called by `Main_file.py`, consistent module boundaries. | |
| 5 | Code Review Completed | Yes | At least one other team member reviewed the code (GitHub PR) for quality, readability, and standards. | |
| 6 | Documentation Updated | Yes | Code comments, README, and relevant `docs/` files are updated and accurate. | |
| 7 | Integration Tests Passed | Yes | The item works with adjacent subsystems (e.g., classification output feeds graph weights; route renders to HTML). | |
| 8 | Performance Requirements Met | Yes | The item runs within acceptable limits (e.g., route computes and renders in a reasonable time; imagery/tile use stays within quota). | |
| 9 | Security Measures Implemented | Partial | API keys/tokens (e.g., MapBox) are kept out of source control; no secrets committed. Broader security is out of scope for the prototype. | |
| 10 | User Interface / Experience Checked | Yes | The map, route, and directions display correctly and are readable in the browser front end. | |
| 11 | Regression Testing Conducted | Yes | Existing features (location, map render, routing) still work after the change. | |
| 12 | Deployment Ready | Yes | The app runs locally end-to-end from a clean checkout with dependencies installed. | |
| 13 | Stakeholder Approval | Yes | The Product Owner (Vyrareth) has reviewed and accepted the item against its acceptance criteria. | |
| 14 | Technical Debt Addressed | Yes | Known shortcuts/TODOs are resolved or logged as backlog/Trello items for a future sprint. | |
| 15 | Peer Verification | Yes | A second team member confirms all applicable criteria above are met and signs off. | |

---

## Notes on tailoring

- **Criterion 9 (Security)** is marked *Partial* because full production security
  (authentication, encryption, access control) is out of scope for a course prototype; the
  practical rule the team commits to is **no secrets/keys in the repository**.
- All other criteria apply as the team's standing Definition of Done for every user story.
- The **Yes / No** column in the original template is filled per user story at story
  closure; this document defines *which* criteria must be checked.

## Assignment checklist (delete before submitting)

- [ ] Each contributor's name added in the "Section completed by" column for the rows they authored
- [ ] Version date filled in

# Level of Effort Estimate — Lease Origination Sample Application

This document provides a **level of effort estimate** for fully executing the work-breakdown in **WBS.md**. It is intended to give stakeholders and project managers a clear view of the effort required so they can confirm commitment, adjust scope, or prioritize. The estimate is closely aligned with the work-breakdown: each phase (and where useful, work type within a phase) has an effort value.

**Unit:** Person-days. Assumes a single project lead directing work (e.g. with Cursor or similar AI-powered development); in a traditional team, effort could be distributed across roles (e.g. design, implementation, QA) and the same WBS used for assignment.

**Basis:** The estimates are informed by the actual experience of executing this project. They are indicative rather than contractual; scope changes, learning curve, or tooling differences can affect actual effort. For a from-scratch run following the project’s plans and documentation, these numbers are a reasonable starting point for stakeholder review.

**References:** WBS.md (work-breakdown), REQUIREMENTS.md (phases and scope), SCOPE.md (boundaries).

---

## Summary by Phase

| Phase ID | Phase name | Effort (person-days) | Notes |
|----------|------------|----------------------|------|
| 0 | Project planning | 2–3 | Pitch, scope, requirements, WBS, LOE, stakeholder review |
| 1 | Baseline | 3–4 | Auth, profile, app shell, admin; foundation for all later work |
| 2 | Business domain | 4–5 | Vehicles, Contacts, Deals; three plans, View/Edit split |
| 3 | Images and file assets | 1–2 | Single app, two batches |
| 4 | Data interface | 2–3 | Schema, get_deal_data, viewer, Debug Data |
| 5 | Setup: wkhtmltopdf | 0.5–1 | Environment setup; may be less if already installed |
| 6 | Document templates and document sets | 6–8 | Four plans: static, dynamic, doc set templates, document sets |
| 7 | SIGNiX submit flow | 8–10 | Nine plans; config, signer service, packager, Send for Signature, dashboard |
| 8 | ngrok | 0.5–1 | Tunnel and codebase changes for push |
| 9 | SIGNiX dashboard, sync, and download | 5–7 | Six plans: push model, listener, push URL, Signers column, download, detail page |
| 10 | Reference and template quality | ongoing | Documentation feedback loop across all phases; not a single block |

**Total (phases 0–9, excluding ongoing):** approximately **31–44 person-days**. Phase 10 is continuous and not added as a lump sum.

---

## Effort by Phase and Work Type (Where Applicable)

| Phase | Knowledge | Design | Plan | Implementation | Total (range) |
|-------|-----------|--------|------|-----------------|---------------|
| 0 Project planning | — | — | — | 2–3 (all planning) | 2–3 |
| 1 Baseline | 0.5 | 0.5 | 0.5 | 2–2.5 | 3–4 |
| 2 Business domain | 0.5 | 0.5 | 1 | 2.5–3 | 4–5 |
| 3 Images | 0.25 | 0.25 | 0.25 | 0.5–1 | 1–2 |
| 4 Data interface | 0.25 | 0.5 | 0.5 | 1–1.5 | 2–3 |
| 5 wkhtmltopdf | — | — | 0.25 | 0.25–0.5 | 0.5–1 |
| 6 Document templates/sets | 0.5 | 1 | 1.5 | 3.5–5 | 6–8 |
| 7 SIGNiX submit | 1 | 1 | 2 | 4–6 | 8–10 |
| 8 ngrok | — | — | 0.25 | 0.25–0.5 | 0.5–1 |
| 9 SIGNiX dashboard/sync | 0.5 | 0.5 | 1 | 3–5 | 5–7 |

*Implementation includes code, test, iterate until tests pass, and validate with project lead. Documentation updates (APPROACH §6.6) are assumed within Implementation and Plan work where they occur.*

---

## Assumptions and Risks

- **Single project lead with AI-assisted development:** One person directing work (e.g. with Cursor); implementation and documentation are produced in conversation with the tool. A larger team would redistribute effort and might add coordination overhead.
- **Scope stability:** Effort assumes scope as defined in SCOPE.md and REQUIREMENTS.md. Significant scope creep or new phases would require a revised WBS and LOE.
- **Existing knowledge:** If the team is new to Django, SIGNiX, or document-centric patterns, Knowledge and Implementation effort may increase; the estimates assume the project’s knowledge and design docs are used.
- **Environment:** Assumes development environment (OS, Python, database, SIGNiX test account, ngrok) can be set up without major blockers. Delays in environment setup are not included.
- **Phase 10:** Reference and template quality (documentation feedback loop, gold standard) is ongoing. No separate lump sum is added; it is assumed to be part of the discipline of each phase.

---

## Use for Stakeholder Review

1. **Commitment:** Stakeholders can use the total and per-phase effort to confirm that the project is resourced and prioritized appropriately.
2. **Scope tradeoffs:** If the total effort is too high, scope can be reduced (e.g. defer a phase or simplify a deliverable) and the WBS/LOE updated.
3. **Timeline:** With a known availability (e.g. person-days per week), the WBS and LOE support a high-level timeline or GANTT; PLAN-MASTER and the master plans remain the source for execution order.
4. **Resource assignment:** In a multi-person team, the WBS work packages and this LOE can be used to assign phases or plans to individuals and track progress.

---

*Work-breakdown: **WBS.md**. What the system must do: **REQUIREMENTS.md**. What is in or out of scope: **SCOPE.md**. Implementation order: **PLAN-MASTER.md**.*

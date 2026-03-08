# Work-Breakdown Structure — Lease Origination Sample Application

This document is the **project-level work-breakdown** for the lease origination sample application. It identifies **all work** required to deliver the project: architecture and phase decomposition, knowledge gathering and documentation, design and design documentation, implementation planning and plan documentation, implementation (code, test, iterate until tests pass, validate with the project lead), and documentation updates to keep plans, designs, and knowledge consistent with real-world experience. It is the kind of artifact you would see represented in a GANTT chart, with selectable levels of detail—the highest level serves as a roadmap. Resource needs can be identified and assigned here (e.g. who does what, especially in a traditional development team).

**Purpose and timing:** The work-breakdown is produced **early** in the project, after scope and requirements are stable, in preparation for **stakeholder review** before execution begins. It is distinct from **PLAN-MASTER.md**: the work-breakdown is the **planning and commitment** artifact (what we will do, how it is organized, for review and approval); PLAN-MASTER is the **execution-order** guide used during the project (the sequence in which plans are actually implemented). The two align on phases and plans but serve different roles.

**This repository:** The project has already been executed. This WBS is aligned with actual experience and with the phase/plan structure in REQUIREMENTS.md, SCOPE.md, and PLAN-MASTER.md. For educational use, it is presented as the best-practice artifact that would have been created upfront for stakeholder review. The **level of effort estimate** is in **LOE.md** and is closely tied to this WBS.

**References:** REQUIREMENTS.md (phases and deliverables), SCOPE.md (in/out of scope), PLAN-MASTER.md (implementation order), LOE.md (effort estimates).

---

## Level 1: Roadmap (Phases)

| ID | Phase | Summary |
|----|-------|---------|
| 0 | Project planning | Pitch, scope, requirements, WBS, LOE — stakeholder review and approval |
| 1 | Baseline | Authentication, profile, app shell, admin, initial user setup |
| 2 | Business domain | Vehicles, Contacts, Deals (deal type, View/Edit split) |
| 3 | Images and file assets | Image upload, storage, stable URLs, CRUD |
| 4 | Data interface | Schema, get_deal_data, schema viewer, Debug Data page |
| 5 | Setup: wkhtmltopdf | Install wkhtmltopdf and pdfkit for dynamic document generation |
| 6 | Document templates and document sets | Static templates, dynamic templates, document set templates, document sets (generate/regenerate/view), Send for Signature stub |
| 7 | SIGNiX submit flow | Config, signature transaction model, signer service, Signers table, build body, send and persist, Send for Signature button, dashboard, related transactions on Deal View |
| 8 | ngrok (push enabler) | Tunnel and codebase changes so SIGNiX push notifications can reach the app |
| 9 | SIGNiX dashboard, sync, and download | Push-driven status, push listener, push URL in SubmitDocument, Signers column, download on complete (signed docs, audit trail, certificate), signature transaction detail page |
| 10 | Reference and template quality | Ongoing: documentation feedback loop, cross-references, gold standard (recreate from scratch, use as template) |

---

## Level 2–3: Work Packages by Phase

Within each phase, work follows the order **Knowledge → Design → Plan → Implementation**, with **documentation updates** after each significant aspect (see APPROACH.md §6.5 and §6.6). Below, each phase is broken into work types and, where useful, specific plans or deliverables. Effort estimates are in **LOE.md**.

---

### Phase 0: Project planning

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Project pitch | Secure sponsorship and alignment | PROJECT-PITCH.md |
| Scope | Clarify in/out of scope | SCOPE.md |
| Requirements | What the system must do; break project into phases | REQUIREMENTS.md |
| Work-breakdown | Project-level plan of all work (this document) | WBS.md |
| Level of effort | Estimate to fully execute WBS for stakeholder review | LOE.md |
| Stakeholder review | Review and approve (or agree to proceed) | Sign-off or agreement to proceed |

*No Knowledge/Design/Plan/Implementation in the product sense; this phase is planning only.*

---

### Phase 1: Baseline

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Topic knowledge needed for design and implementation | KNOWLEDGE-APP-FOUNDATION.md |
| Design | Decisions and contracts for baseline | DESIGN-BASELINE.md |
| Implementation planning | Batches, verification steps, tests | PLAN-BASELINE.md |
| Implementation | Code, test, iterate, validate with project lead | Batch 1 (venv, project, users app, model, migrations, setup_initial_user); Batch 2 (auth, base templates, profile, admin) |
| Documentation updates | Align plans, design, knowledge with reality | Per §6.6 |

*Execution order: PLAN-MASTER plan 1.*

---

### Phase 2: Business domain (Vehicles, Contacts, Deals)

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Document-centric pattern; domain (vehicle leasing, jet packs) | KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md, KNOWLEDGE-LEASE-JETPACKS.md |
| Design | Entity relationships, deal-centric workflow, UI conventions | DESIGN-BIZ-DOMAIN.md |
| Implementation planning | Master plan + three plans, each with batches | PLAN-BIZ-DOMAIN-MASTER.md; PLAN-ADD-VEHICLES, PLAN-ADD-CONTACTS, PLAN-ADD-DEALS |
| Implementation | Data layer then UI per plan; Vehicles → Contacts → Deals | Per PLAN-BIZ-DOMAIN-MASTER and individual plans |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: PLAN-MASTER plan 2 (PLAN-BIZ-DOMAIN-MASTER).*

---

### Phase 3: Images and file assets

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | File storage, media, stable URLs | KNOWLEDGE-FILE-ASSETS-MEDIA.md |
| Design | Image model, CRUD, media config | DESIGN-IMAGES.md |
| Implementation planning | Batches and verification | PLAN-ADD-IMAGES.md |
| Implementation | Batch 1 (app, model, media); Batch 2 (forms, views, templates, sidebar) | Per PLAN-ADD-IMAGES |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: PLAN-MASTER plan 3.*

---

### Phase 4: Data interface

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Schema and deal data as single source for documents | KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md (§4) |
| Design | Schema, get_schema, get_paths, get_deal_data, viewer, Debug Data | DESIGN-DATA-INTERFACE.md |
| Implementation planning | Batches and verification | PLAN-DATA-INTERFACE.md |
| Implementation | Batch 1 (app, services); Batch 2 (schema viewer); Batch 3 (Debug Data, JSON modal) | Per PLAN-DATA-INTERFACE |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: PLAN-MASTER plan 4.*

---

### Phase 5: Setup — wkhtmltopdf

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | HTML-to-PDF constraints and usage | KNOWLEDGE-HTML-TO-PDF.md |
| Implementation planning | Install and verify | SETUP-WKHTMLTOPDF.md |
| Implementation | Install wkhtmltopdf; ensure pdfkit in environment; verify | Per SETUP-WKHTMLTOPDF (before Document Features) |
| Documentation updates | As needed | Per §6.6 |

*Execution order: After PLAN-MASTER plans 1–4; before PLAN-DOCS-MASTER.*

---

### Phase 6: Document templates and document sets

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Document flow, mapping, templates (refresher from KNOWLEDGE-DOCUMENT-CENTRIC-APPS) | KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md (§4–5) |
| Design | Static/dynamic/set templates, document sets, generation, tagging | DESIGN-DOCS.md |
| Implementation planning | Master plan + four plans, each with batches | PLAN-DOCS-MASTER.md; PLAN-ADD-STATIC-DOC-TEMPLATES, PLAN-ADD-DYNAMIC-DOC-TEMPLATES, PLAN-ADD-DOC-SET-TEMPLATES, PLAN-ADD-DOCUMENT-SETS |
| Implementation | Static templates → Dynamic templates → Doc set templates → Document sets (Generate/Regenerate/Delete, Documents UI, Send for Signature stub) | Per PLAN-DOCS-MASTER plans 1–4 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: PLAN-DOCS-MASTER plans 1–4 (SIGNiX integration via Phase 7).*

---

### Phase 7: SIGNiX submit flow

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | SIGNiX Flex API, SubmitDocument, GetAccessLink, field notes | KNOWLEDGE-SIGNiX.md |
| Design | Config, signer identification, transaction packager, Send for Signature, dashboard, Deal View table | DESIGN-SIGNiX-SUBMIT.md |
| Implementation planning | Nine plans in sequence | PLAN-SIGNiX-SUBMIT-MASTER.md; PLAN-SIGNiX-CONFIG through PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS |
| Implementation | Config → SignatureTransaction model → Signer service → Signers table → Build body → Send and persist → Send for Signature button → Dashboard → Deal View transactions | Per PLAN-SIGNiX-SUBMIT-MASTER plans 1–9 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: After PLAN-DOCS-MASTER 1–4; PLAN-SIGNiX-SUBMIT-MASTER plans 1–9.*

---

### Phase 8: ngrok (push enabler)

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Implementation planning | Tunnel, domain, codebase changes for app behind tunnel | PLAN-NGROK.md |
| Implementation | Install/claim ngrok; ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, PDF_IMAGE_BASE_URL, health endpoint, launch config, scripts | Per PLAN-NGROK |
| Documentation updates | As needed | Per §6.6 |

*Execution order: When ready to implement push notifications; before Phase 9.*

---

### Phase 9: SIGNiX dashboard, sync, and download

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Push format, DownloadDocument, ConfirmDownload, status values | KNOWLEDGE-SIGNiX.md (extended) |
| Design | Push listener, status/per-signer progress, push URL in SubmitDocument, download on complete, audit trail/certificate storage, transaction detail page | DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md |
| Implementation planning | Six plans in sequence | PLAN-SIGNiX-DASHBOARD-SYNC-MASTER.md; PLAN-SIGNiX-SYNC-MODEL through PLAN-SIGNiX-TRANSACTION-DETAIL |
| Implementation | Sync model → Push listener → Submit push URL → Dashboard Signers column → Download on complete → Transaction detail page | Per PLAN-SIGNiX-DASHBOARD-SYNC-MASTER plans 1–6 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: After PLAN-SIGNiX-SUBMIT-MASTER and PLAN-NGROK; PLAN-SIGNiX-DASHBOARD-SYNC-MASTER plans 1–6.*

---

### Phase 10: Reference and template quality

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Documentation feedback loop | Ongoing: update plans, designs, knowledge to match implementation; maintain cross-references | Per APPROACH.md §6.6 |
| Gold standard | Recreate from scratch and use as template; no critical info only in conversation or project lead’s head | Per APPROACH.md §6.7 |

*This work is continuous across all phases and after delivery.*

---

## Summary: Relationship to Other Documents

| Document | Role |
|----------|------|
| **WBS.md** (this document) | Project-level breakdown of **all work**; planning artifact for stakeholder review; supports GANTT, resources, LOE. |
| **LOE.md** | Level of effort estimate aligned with this WBS; for stakeholders and project managers. |
| **PLAN-MASTER.md** | **Execution** order: which plan to implement when. Used during the project. |
| **Master plans** (e.g. PLAN-BIZ-DOMAIN-MASTER, PLAN-DOCS-MASTER) | Execution order **within** a phase. |
| **Individual plans** (e.g. PLAN-BASELINE, PLAN-ADD-DEALS) | Batches, verification steps, tests for implementation. |

---

*Effort estimates: **LOE.md**. What the system must do: **REQUIREMENTS.md**. What is in or out of scope: **SCOPE.md**. Implementation order: **PLAN-MASTER.md**.*

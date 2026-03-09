# Work-Breakdown Structure — Lease Origination Sample Application

This document is the **project-level work-breakdown** for the lease origination sample application. It identifies **all work** required to deliver the project: architecture and phase decomposition, knowledge gathering and documentation, design and design documentation, implementation planning and plan documentation, implementation (code, test, iterate until tests pass, validate with the project lead), and documentation updates to keep plans, designs, and knowledge consistent with real-world experience. It is the kind of artifact you would see represented in a GANTT chart, with selectable levels of detail—the highest level serves as a roadmap. Resource needs can be identified and assigned here (e.g. who does what, especially in a traditional development team).

**Purpose and timing:** The work-breakdown is produced during the **Design phase**, after requirements are determined, in preparation for **stakeholder review** and approval to proceed to Implementation (see [20-APPROACH.md](20-APPROACH.md) Section 5.5 and 6.4). It is distinct from [70-PLAN-MASTER.md](70-PLAN-MASTER.md): the work-breakdown is the **planning and commitment** artifact (what we will do, how it is organized, for review and approval); [70-PLAN-MASTER.md](70-PLAN-MASTER.md) is the **execution-order** guide used during the project (the sequence in which plans are actually implemented). The two align on phases and plans but serve different roles.

**This repository:** The project has already been executed. This WBS is aligned with actual experience and with the phase/plan structure in [40-REQUIREMENTS.md](40-REQUIREMENTS.md), [30-SCOPE.md](30-SCOPE.md), and [70-PLAN-MASTER.md](70-PLAN-MASTER.md). For educational use, it is presented as the best-practice artifact that would have been created upfront for stakeholder review. The **level of effort estimate** is in [60-LOE.md](60-LOE.md) and is closely tied to this WBS.

**References:** [40-REQUIREMENTS.md](40-REQUIREMENTS.md) (phases and deliverables), [30-SCOPE.md](30-SCOPE.md) (in/out of scope), [70-PLAN-MASTER.md](70-PLAN-MASTER.md) (implementation order), [60-LOE.md](60-LOE.md) (effort estimates).

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

Within each phase, work follows the order **Knowledge → Design → Plan → Implementation**, with **documentation updates** after each significant aspect (see [20-APPROACH.md](20-APPROACH.md) §6.5 and §6.6). Below, each phase is broken into work types and, where useful, specific plans or deliverables. Effort estimates are in [60-LOE.md](60-LOE.md).

---

### Phase 0: Project planning

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Project pitch | Secure sponsorship and alignment | [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) |
| Scope | Clarify in/out of scope | [30-SCOPE.md](30-SCOPE.md) |
| Requirements | What the system must do; break project into phases | [40-REQUIREMENTS.md](40-REQUIREMENTS.md) |
| Work-breakdown | Project-level plan of all work (this document) | [50-WBS.md](50-WBS.md) |
| Level of effort | Estimate to fully execute WBS for stakeholder review | [60-LOE.md](60-LOE.md) |
| Stakeholder review | Review and approve (or agree to proceed) | Sign-off or agreement to proceed |

*No Knowledge/Design/Plan/Implementation in the product sense; this phase is planning only.*

---

### Phase 1: Baseline

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Topic knowledge needed for design and implementation | [GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md](GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md) |
| Design | Decisions and contracts for baseline | [01-BASELINE/DESIGN-BASELINE.md](01-BASELINE/DESIGN-BASELINE.md) |
| Implementation planning | Batches, verification steps, tests | [01-BASELINE/10-PLAN-BASELINE.md](01-BASELINE/10-PLAN-BASELINE.md) |
| Implementation | Code, test, iterate, validate with project lead | Batch 1 (venv, project, users app, model, migrations, setup_initial_user); Batch 2 (auth, base templates, profile, admin) |
| Documentation updates | Align plans, design, knowledge with reality | Per §6.6 |

*Execution order: [70-PLAN-MASTER.md](70-PLAN-MASTER.md) plan 1.*

---

### Phase 2: Business domain (Vehicles, Contacts, Deals)

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Document-centric pattern; domain (vehicle leasing, jet packs) | [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md), [02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md](02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md) |
| Design | Entity relationships, deal-centric workflow, UI conventions | [02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md](02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md) |
| Implementation planning | Master plan + three plans, each with batches | [02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md](02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md); [10-PLAN-ADD-VEHICLES.md](02-BIZ-DOMAIN/10-PLAN-ADD-VEHICLES.md), [20-PLAN-ADD-CONTACTS.md](02-BIZ-DOMAIN/20-PLAN-ADD-CONTACTS.md), [30-PLAN-ADD-DEALS.md](02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md) |
| Implementation | Data layer then UI per plan; Vehicles → Contacts → Deals | Per PHASE-PLANS-BIZ-DOMAIN and individual plans |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: [70-PLAN-MASTER.md](70-PLAN-MASTER.md) plan 2 (PHASE-PLANS-BIZ-DOMAIN).*

---

### Phase 3: Images and file assets

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | File storage, media, stable URLs | [GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md](GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md) |
| Design | Image model, CRUD, media config | [03-IMAGES/DESIGN-IMAGES.md](03-IMAGES/DESIGN-IMAGES.md) |
| Implementation planning | Batches and verification | [03-IMAGES/10-PLAN-ADD-IMAGES.md](03-IMAGES/10-PLAN-ADD-IMAGES.md) |
| Implementation | Batch 1 (app, model, media); Batch 2 (forms, views, templates, sidebar) | Per PLAN-ADD-IMAGES |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: [70-PLAN-MASTER.md](70-PLAN-MASTER.md) plan 3.*

---

### Phase 4: Data interface

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Schema and deal data as single source for documents | [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) (§4) |
| Design | Schema, get_schema, get_paths, get_deal_data, viewer, Debug Data | [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) |
| Implementation planning | Batches and verification | [04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md](04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md) |
| Implementation | Batch 1 (app, services); Batch 2 (schema viewer); Batch 3 (Debug Data, JSON modal) | Per PLAN-DATA-INTERFACE |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: [70-PLAN-MASTER.md](70-PLAN-MASTER.md) plan 4.*

---

### Phase 5: Setup — wkhtmltopdf

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | HTML-to-PDF constraints and usage | [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) |
| Implementation planning | Install and verify | [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md) |
| Implementation | Install wkhtmltopdf; ensure pdfkit in environment; verify | Per SETUP-WKHTMLTOPDF (before Document Features) |
| Documentation updates | As needed | Per §6.6 |

*Execution order: After [70-PLAN-MASTER.md](70-PLAN-MASTER.md) plans 1–4; before PHASE-PLANS-DOCS.*

---

### Phase 6: Document templates and document sets

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Document flow, mapping, templates (refresher from KNOWLEDGE-DOCUMENT-CENTRIC-APPS) | [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) (§4–5) |
| Design | Static/dynamic/set templates, document sets, generation, tagging | [06-DOCS/DESIGN-DOCS.md](06-DOCS/DESIGN-DOCS.md) |
| Implementation planning | Master plan + four plans, each with batches | [06-DOCS/PHASE-PLANS-DOCS.md](06-DOCS/PHASE-PLANS-DOCS.md); [10-PLAN-ADD-STATIC-DOC-TEMPLATES.md](06-DOCS/10-PLAN-ADD-STATIC-DOC-TEMPLATES.md), [20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md](06-DOCS/20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md), [30-PLAN-ADD-DOC-SET-TEMPLATES.md](06-DOCS/30-PLAN-ADD-DOC-SET-TEMPLATES.md), [40-PLAN-ADD-DOCUMENT-SETS.md](06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md) |
| Implementation | Static templates → Dynamic templates → Doc set templates → Document sets (Generate/Regenerate/Delete, Documents UI, Send for Signature stub) | Per PHASE-PLANS-DOCS plans 1–4 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: PHASE-PLANS-DOCS plans 1–4 (SIGNiX integration via Phase 7).*

---

### Phase 7: SIGNiX submit flow

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | SIGNiX Flex API, SubmitDocument, GetAccessLink, field notes | [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) |
| Design | Config, signer identification, transaction packager, Send for Signature, dashboard, Deal View table | [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) |
| Implementation planning | Nine plans in sequence | [07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md); [10-PLAN-SIGNiX-CONFIG.md](07-SIGNiX-SUBMIT/10-PLAN-SIGNiX-CONFIG.md) through [90-PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md](07-SIGNiX-SUBMIT/90-PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md) |
| Implementation | Config → SignatureTransaction model → Signer service → Signers table → Build body → Send and persist → Send for Signature button → Dashboard → Deal View transactions | Per PHASE-PLANS-SIGNiX-SUBMIT plans 1–9 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: After PHASE-PLANS-DOCS 1–4; PHASE-PLANS-SIGNiX-SUBMIT plans 1–9.*

---

### Phase 8: ngrok (push enabler)

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Implementation planning | Tunnel, domain, codebase changes for app behind tunnel | [08-NGROK/10-PLAN-NGROK.md](08-NGROK/10-PLAN-NGROK.md) |
| Implementation | Install/claim ngrok; ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, PDF_IMAGE_BASE_URL, health endpoint, launch config, scripts | Per [08-NGROK/10-PLAN-NGROK.md](08-NGROK/10-PLAN-NGROK.md) |
| Documentation updates | As needed | Per §6.6 |

*Execution order: When ready to implement push notifications; before Phase 9.*

---

### Phase 9: SIGNiX dashboard, sync, and download

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Knowledge identification & documentation | Push format, DownloadDocument, ConfirmDownload, status values | [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) (extended) |
| Design | Push listener, status/per-signer progress, push URL in SubmitDocument, download on complete, audit trail/certificate storage, transaction detail page | [09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md) |
| Implementation planning | Six plans in sequence | [09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md); PLAN-SIGNiX-SYNC-MODEL through PLAN-SIGNiX-TRANSACTION-DETAIL |
| Implementation | Sync model → Push listener → Submit push URL → Dashboard Signers column → Download on complete → Transaction detail page | Per PHASE-PLANS-SIGNiX-DASHBOARD-SYNC plans 1–6 |
| Documentation updates | Plans, design, knowledge | Per §6.6 |

*Execution order: After [07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md) and [08-NGROK/10-PLAN-NGROK.md](08-NGROK/10-PLAN-NGROK.md); [09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md) plans 1–6.*

---

### Phase 10: Reference and template quality

| Work type | Description | Deliverables / notes |
|-----------|-------------|----------------------|
| Documentation feedback loop | Ongoing: update plans, designs, knowledge to match implementation; maintain cross-references | Per [20-APPROACH.md](20-APPROACH.md) §6.6 |
| Gold standard | Recreate from scratch and use as template; no critical info only in conversation or project lead’s head | Per [20-APPROACH.md](20-APPROACH.md) §6.7 |

*This work is continuous across all phases and after delivery.*

---

## Summary: Relationship to Other Documents

| Document | Role |
|----------|------|
| **50-WBS.md** (this document) | Project-level breakdown of **all work**; planning artifact for stakeholder review; supports GANTT, resources, LOE. |
| [60-LOE.md](60-LOE.md) | Level of effort estimate aligned with this WBS; for stakeholders and project managers. |
| [70-PLAN-MASTER.md](70-PLAN-MASTER.md) | **Execution** order: which plan to implement when. Used during the project. |
| **Phase plans** (e.g. [02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md](02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md), [06-DOCS/PHASE-PLANS-DOCS.md](06-DOCS/PHASE-PLANS-DOCS.md)) | Execution order **within** a phase. |
| **Individual plans** (e.g. [01-BASELINE/10-PLAN-BASELINE.md](01-BASELINE/10-PLAN-BASELINE.md), [02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md](02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md)) | Batches, verification steps, tests for implementation. |

---

*Effort estimates: [60-LOE.md](60-LOE.md). What the system must do: [40-REQUIREMENTS.md](40-REQUIREMENTS.md). What is in or out of scope: [30-SCOPE.md](30-SCOPE.md). Implementation order: [70-PLAN-MASTER.md](70-PLAN-MASTER.md).*

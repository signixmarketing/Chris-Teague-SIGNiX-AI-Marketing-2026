# Project Documentation Index

This index lists all project documentation and its location so you can find any document quickly. Paths are relative to the **PROJECT-DOCS** folder. For implementation order, start with [70-PLAN-MASTER.md](70-PLAN-MASTER.md).

---

## Project-level documents (read in order)

| Order | Path | Description |
|-------|------|-------------|
| 10 | [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) | Why we are doing the project; stakeholder alignment |
| 20 | [20-APPROACH.md](20-APPROACH.md) | How we build and document; methodology |
| 30 | [30-SCOPE.md](30-SCOPE.md) | What is in scope and out of scope |
| 40 | [40-REQUIREMENTS.md](40-REQUIREMENTS.md) | What the system must do; phases |
| 50 | [50-WBS.md](50-WBS.md) | Work-breakdown structure |
| 60 | [60-LOE.md](60-LOE.md) | Level of effort estimate |
| 70 | [70-PLAN-MASTER.md](70-PLAN-MASTER.md) | Implementation order (execution map) |

---

## General knowledge (used by multiple phases)

| Path | Description |
|------|-------------|
| [GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md](GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md) | Baseline capabilities; technology-agnostic |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) | Document-centric pattern; data, templates, deals |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md](GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md) | File upload, storage, stable URLs |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) | HTML-to-PDF; wkhtmltopdf, pdfkit |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) | SIGNiX Flex API and integration |

---

## Phase 01: Baseline

| Path | Description |
|------|-------------|
| [01-BASELINE/DESIGN-BASELINE.md](01-BASELINE/DESIGN-BASELINE.md) | Design: auth, profile, app shell, admin |
| [01-BASELINE/10-PLAN-BASELINE.md](01-BASELINE/10-PLAN-BASELINE.md) | Plan: implementation order and batches |

---

## Phase 02: Business domain (Vehicles, Contacts, Deals)

| Path | Description |
|------|-------------|
| [02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md](02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md) | Design: entities, relationships, UI conventions |
| [02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md](02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md) | Phase plans: order of plans |
| [02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md](02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md) | Knowledge: vehicle leasing domain |
| [02-BIZ-DOMAIN/10-PLAN-ADD-VEHICLES.md](02-BIZ-DOMAIN/10-PLAN-ADD-VEHICLES.md) | Plan: Vehicles |
| [02-BIZ-DOMAIN/20-PLAN-ADD-CONTACTS.md](02-BIZ-DOMAIN/20-PLAN-ADD-CONTACTS.md) | Plan: Contacts |
| [02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md](02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md) | Plan: Deals |

---

## Phase 03: Images

| Path | Description |
|------|-------------|
| [03-IMAGES/DESIGN-IMAGES.md](03-IMAGES/DESIGN-IMAGES.md) | Design: image model, CRUD, media |
| [03-IMAGES/10-PLAN-ADD-IMAGES.md](03-IMAGES/10-PLAN-ADD-IMAGES.md) | Plan: Images app |

---

## Phase 04: Data interface

| Path | Description |
|------|-------------|
| [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) | Design: schema, get_deal_data, viewer, Debug Data |
| [04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md](04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md) | Plan: data interface |

---

## Phase 05: Setup — wkhtmltopdf

| Path | Description |
|------|-------------|
| [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md) | Setup: wkhtmltopdf + pdfkit for HTML-to-PDF |

---

## Phase 06: Document templates and document sets

| Path | Description |
|------|-------------|
| [06-DOCS/DESIGN-DOCS.md](06-DOCS/DESIGN-DOCS.md) | Design: templates, document sets, generation |
| [06-DOCS/PHASE-PLANS-DOCS.md](06-DOCS/PHASE-PLANS-DOCS.md) | Phase plans: order of document plans |
| [06-DOCS/10-PLAN-ADD-STATIC-DOC-TEMPLATES.md](06-DOCS/10-PLAN-ADD-STATIC-DOC-TEMPLATES.md) | Plan: static document templates |
| [06-DOCS/20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md](06-DOCS/20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md) | Plan: dynamic document templates |
| [06-DOCS/30-PLAN-ADD-DOC-SET-TEMPLATES.md](06-DOCS/30-PLAN-ADD-DOC-SET-TEMPLATES.md) | Plan: document set templates |
| [06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md](06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md) | Plan: document sets |

---

## Phase 07: SIGNiX submit flow

| Path | Description |
|------|-------------|
| [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) | Design: submit flow, signers, packager, dashboard |
| [07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md) | Phase plans: order of nine plans |
| [07-SIGNiX-SUBMIT/10-PLAN-SIGNiX-CONFIG.md](07-SIGNiX-SUBMIT/10-PLAN-SIGNiX-CONFIG.md) | Plan: SIGNiX configuration |
| [07-SIGNiX-SUBMIT/20-PLAN-SIGNiX-SIGNATURE-TRANSACTION.md](07-SIGNiX-SUBMIT/20-PLAN-SIGNiX-SIGNATURE-TRANSACTION.md) | Plan: SignatureTransaction model |
| [07-SIGNiX-SUBMIT/30-PLAN-SIGNiX-SIGNER-SERVICE.md](07-SIGNiX-SUBMIT/30-PLAN-SIGNiX-SIGNER-SERVICE.md) | Plan: signer service |
| [07-SIGNiX-SUBMIT/40-PLAN-SIGNiX-SIGNERS-TABLE.md](07-SIGNiX-SUBMIT/40-PLAN-SIGNiX-SIGNERS-TABLE.md) | Plan: Signers table |
| [07-SIGNiX-SUBMIT/50-PLAN-SIGNiX-BUILD-BODY.md](07-SIGNiX-SUBMIT/50-PLAN-SIGNiX-BUILD-BODY.md) | Plan: build SubmitDocument body |
| [07-SIGNiX-SUBMIT/60-PLAN-SIGNiX-SEND-AND-PERSIST.md](07-SIGNiX-SUBMIT/60-PLAN-SIGNiX-SEND-AND-PERSIST.md) | Plan: send and persist |
| [07-SIGNiX-SUBMIT/70-PLAN-SIGNiX-SEND-FOR-SIGNATURE.md](07-SIGNiX-SUBMIT/70-PLAN-SIGNiX-SEND-FOR-SIGNATURE.md) | Plan: Send for Signature button |
| [07-SIGNiX-SUBMIT/80-PLAN-SIGNiX-DASHBOARD.md](07-SIGNiX-SUBMIT/80-PLAN-SIGNiX-DASHBOARD.md) | Plan: signature transactions dashboard |
| [07-SIGNiX-SUBMIT/90-PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md](07-SIGNiX-SUBMIT/90-PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md) | Plan: related transactions on Deal View |

---

## Phase 08: ngrok (push enabler)

| Path | Description |
|------|-------------|
| [08-NGROK/10-PLAN-NGROK.md](08-NGROK/10-PLAN-NGROK.md) | Plan: ngrok tunnel and codebase changes |

---

## Phase 09: SIGNiX dashboard, sync, and download

| Path | Description |
|------|-------------|
| [09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md) | Design: push, status, download, transaction detail |
| [09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md) | Phase plans: order of six plans |
| [09-SIGNiX-DASHBOARD-SYNC/10-PLAN-SIGNiX-SYNC-MODEL.md](09-SIGNiX-DASHBOARD-SYNC/10-PLAN-SIGNiX-SYNC-MODEL.md) | Plan: sync model |
| [09-SIGNiX-DASHBOARD-SYNC/20-PLAN-SIGNiX-PUSH-LISTENER.md](09-SIGNiX-DASHBOARD-SYNC/20-PLAN-SIGNiX-PUSH-LISTENER.md) | Plan: push listener |
| [09-SIGNiX-DASHBOARD-SYNC/30-PLAN-SIGNiX-SUBMIT-PUSH-URL.md](09-SIGNiX-DASHBOARD-SYNC/30-PLAN-SIGNiX-SUBMIT-PUSH-URL.md) | Plan: push URL in SubmitDocument |
| [09-SIGNiX-DASHBOARD-SYNC/40-PLAN-SIGNiX-DASHBOARD-SIGNERS.md](09-SIGNiX-DASHBOARD-SYNC/40-PLAN-SIGNiX-DASHBOARD-SIGNERS.md) | Plan: Signers column |
| [09-SIGNiX-DASHBOARD-SYNC/50-PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md](09-SIGNiX-DASHBOARD-SYNC/50-PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md) | Plan: download on complete |
| [09-SIGNiX-DASHBOARD-SYNC/60-PLAN-SIGNiX-TRANSACTION-DETAIL.md](09-SIGNiX-DASHBOARD-SYNC/60-PLAN-SIGNiX-TRANSACTION-DETAIL.md) | Plan: signature transaction detail page |

---

*Start with [70-PLAN-MASTER.md](70-PLAN-MASTER.md) for implementation order. For methodology and document order, read [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) through [60-LOE.md](60-LOE.md) as in the table above.*

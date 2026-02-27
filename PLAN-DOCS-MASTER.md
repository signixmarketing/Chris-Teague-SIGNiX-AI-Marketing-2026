# Plan Docs Master — Document Features Implementation Order

This document defines the order in which to implement the document-related features from **DESIGN-DOCS.md**. These plans build on the existing app (PLAN-MASTER plans 1–5: Baseline, Vehicles, Contacts, Deals, Images). Implement the document plans in the sequence below.

**Usage:** Implement each plan below in order. Within each plan, follow its Implementation Order and Batches/Verification. Do not skip ahead—later plans depend on earlier ones.

**Source of truth:** DESIGN-DOCS.md. Refer to it for concepts, data structures, and decisions.

---

## Design Decisions Summary

| Topic | Decision |
|-------|----------|
| **ref_id** | Unique across both Static and Dynamic templates (enforce in form `clean_ref_id`) |
| **Static formset** | `extra=3`; three default empty rows |
| **Static conditional fields** | Always show date_signed_field_name/date_signed_format; require in form `clean()` when `field_type == "signature"` (no JS show/hide) |
| **Dynamic mapping UI** | Table layout — one row per variable (Variable, Source, Transform) |
| **Dynamic item_map** | Supported in v1; one row per parsed `item.*` variable; map each to Vehicle field dropdown |
| **Dynamic variable mapping** | All parsed variables must be mapped (validation on add and edit) |
| **Identify Fields** | Fetch/AJAX; no page reload (file input preserved) |
| **Sidebar order** | Static Templates → Dynamic Templates → Images |

---

## Prerequisites

- Plans 1–5 from PLAN-MASTER.md must be implemented (Baseline, Vehicles, Contacts, Deals, Images).
- DESIGN-DOCS.md describes the full design; these plans focus on implementation steps.

---

## 1. PLAN-ADD-STATIC-DOC-TEMPLATES.md

**Purpose:** Static document templates—reusable PDFs with form fields (e.g., safety advisory). Upload PDF, store metadata (ref_id, description), and configure form field definitions (tagging_data) for SIGNiX. CRUD, sidebar link, same UI pattern as Deals/Vehicles/Contacts.

**Implement:** Batch 1 (app, model, migrations), Batch 2 (forms including tagging_data formset), Batch 3 (views, URLs, templates, sidebar). See PLAN-ADD-STATIC-DOC-TEMPLATES.md Section 7 and Section 7a.

---

## 2. PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md

**Purpose:** Dynamic document templates—HTML files with DTL. Upload HTML, configure text tagging (signature/date fields for SIGNiX) and mapping (template variables → deal data). DTL parsing, model introspection, mapping UI.

**Implement:** Batch 1 (model, migrations), Batch 2 (CRUD + text tagging), Batch 3 (DTL parsing), Batch 4 (mapping UI). See PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md Section 7 and Section 7a.

---

## 3. PLAN-ADD-DEAL-TYPE.md

**Purpose:** Add Deal Type to the Deal model. Initial release: one type "Lease - Single Signer", default for all deals. DealType model and FK on Deal. Must be implemented before Document Set Templates (which associate with Deal Type).

**Implement:** Batch 1 (DealType model, migrations, seed, Deal.deal_type, data migration), Batch 2 (Deal.save default, deal add view, optional admin). See PLAN-ADD-DEAL-TYPE.md Section 7 and Section 7a.

---

## 4. PLAN-ADD-DOC-SET-TEMPLATES.md

**Purpose:** Document Set Templates—define ordered list of Static/Dynamic templates, associate with Deal Type. UI to configure (select templates, order with up/down, associate with Deal Type). Depends on Deal Type.

**Implement:** Batch 1 (models, migrations, URL routing), Batch 2 (forms, formset, conversion helpers), Batch 3 (views, templates, sidebar). See PLAN-ADD-DOC-SET-TEMPLATES.md Section 7 and Section 7a.

---

## 5. PLAN-ADD-DOCUMENT-SETS.md

**Purpose:** Document Sets, Document Instances, Document Instance Versions. Generate Documents flow (create documents from templates), Regenerate Documents, Delete Document Set. Document viewing UI (table on Deal page, View latest, View all versions, in-browser PDF viewer). Deal detail page. Send for Signature stub.

**Implement:** Batch 1 (models, migrations, Deal detail), Batch 2 (Generate for Static), Batch 3 (Generate for Dynamic, Regenerate, Delete), Batch 4 (Documents UI, version page, View/Download, Send stub). See PLAN-ADD-DOCUMENT-SETS.md Section 7 and Section 7a.

---

## 6. PLAN-ADD-SIGNIX-INTEGRATION.md *(to be created, after SIGNiX design)*

**Purpose:** Send for Signature—package documents and send to SIGNiX. Handle completion notification, download signed documents, create Final Document Instance Versions. Depends on SIGNiX integration design in DESIGN-DOCS or a separate design document.

---

## Summary Table

| Order | Plan                              | Key deliverables                                    |
|-------|-----------------------------------|-----------------------------------------------------|
| 1     | PLAN-ADD-STATIC-DOC-TEMPLATES.md  | Static PDF templates, ref_id, description, tagging_data |
| 2     | PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md | Dynamic HTML templates, mapping, text tagging       |
| 3     | PLAN-ADD-DEAL-TYPE.md             | Deal Type model, "Lease - Single Signer" default    |
| 4     | PLAN-ADD-DOC-SET-TEMPLATES.md     | Document Set Templates, ordered template list       |
| 5     | PLAN-ADD-DOCUMENT-SETS.md         | Document Sets, generation, viewing UI               |
| 6     | PLAN-ADD-SIGNIX-INTEGRATION.md    | Send for Signature, completion handling             |

---

## Outstanding Questions / Design Decisions (Future Plans)

Items to resolve when creating the corresponding plans:

| Plan | Topic | Notes |
|------|-------|-------|
| Doc Set Templates | Template ordering UI | **Decided:** Up/down buttons for v1 (see PLAN-ADD-DOC-SET-TEMPLATES.md). |
| Dynamic (v1) | `concat` transform | Concatenation needs multiple source fields (e.g. first_name + last_name). Mapping UI for selecting fields—defer to v1 or add simple multi-select? |
| Document Sets | HTML-to-PDF | pdfkit/wkhtmltopdf per DESIGN-DOCS; see PLAN-ADD-DOCUMENT-SETS Section 12 for image URL handling. |
| SIGNiX | Integration design | Deferred; PLAN-ADD-SIGNIX-INTEGRATION created after SIGNiX design is documented. |

**Implementation order:** Deal Type (plan 3) must be implemented before Document Set Templates (plan 4), since Doc Set Templates associate with Deal Type. Summary table above reflects this order.

---

*To implement document features: complete PLAN-MASTER plans 1–5 first, then implement PLAN-DOCS-MASTER plans 1–6 in order.*

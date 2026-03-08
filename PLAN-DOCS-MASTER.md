# Plan Docs Master — Document Features Implementation Order

This document defines the order in which to implement the document-related features from **DESIGN-DOCS.md**. These plans build on the existing app (PLAN-MASTER plans 1–4: Baseline, Biz Domain Master, Images, Data Interface). Implement the document plans in the sequence below.

**Usage:** Implement each plan below in order. Within each plan, follow its Implementation Order and Batches/Verification. Do not skip ahead—later plans depend on earlier ones.

**Design:** DESIGN-DOCS.md. **Knowledge:** KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md (document flow in §4–5).

**Source of truth:** DESIGN-DOCS.md. Refer to it for concepts, data structures, and decisions.

---

## Design Decisions Summary

| Topic | Decision |
|-------|----------|
| **ref_id** | Unique across both Static and Dynamic templates (enforce in form `clean_ref_id`) |
| **Static formset** | `extra=3`; three default empty rows |
| **Static conditional fields** | Always show date_signed_field_name/date_signed_format; require in form `clean()` when `field_type == "signature"` (no JS show/hide) |
| **Dynamic mapping UI** | Template structure summary (Primary data source, Lists with items, Scalar properties, Image variables) above mapping table. Table: one row per variable; list items show parent list (e.g. `item.sku (data.jet_pack_list)`); type badges (data source, list, list item, image, scalar); Source optgroups (schema paths + Images from Image model); Transform. Mapping stores `var_type` per entry; image variables use source `image:<uuid>`. |
| **Dynamic item_map** | Supported in v1; one row per parsed `item.*` variable; map each to Vehicle field dropdown |
| **Dynamic variable mapping** | All parsed variables must be mapped (validation on add and edit) |
| **Identify Fields** | Fetch/AJAX; no page reload (file input preserved) |
| **Sidebar order** | Static Templates → Dynamic Templates → Document Set Templates → Images |
| **Data interface** | Dynamic templates use `apps.schema.services.get_paths_grouped_for_mapping()` for deal paths and append Images optgroup from Image model; context builder uses `get_deal_data()` for deal data and resolves `image:<uuid>` via Image model—no model traversal for deal paths (DESIGN-DATA-INTERFACE) |

---

## Prerequisites

- Plans 1–4 from PLAN-MASTER.md are implemented and in place (Baseline, Biz Domain Master [Vehicles, Contacts, Deals], Images, Data Interface). Deals includes Deal Type; the deal detail page has the View/Edit split (list links to detail, Edit and Delete on detail). Data Interface (apps.schema) provides get_schema(), get_paths(), get_deal_data(deal) used by Dynamic templates and the context builder.
- DESIGN-DOCS.md describes the full design; these plans focus on implementation steps.

---

## 1. PLAN-ADD-STATIC-DOC-TEMPLATES.md

**Purpose:** Static document templates—reusable PDFs with form fields (e.g., safety advisory). Upload PDF, store metadata (ref_id, description), and configure form field definitions (tagging_data) for SIGNiX. CRUD, sidebar link, same UI pattern as Deals/Vehicles/Contacts.

**Implement:** Batch 1 (app, model, migrations), Batch 2 (forms including tagging_data formset), Batch 3 (views, URLs, templates, sidebar). See PLAN-ADD-STATIC-DOC-TEMPLATES.md Section 7 and Section 7a.

---

## 2. PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md

**Purpose:** Dynamic document templates—HTML files with DTL. Upload HTML, configure text tagging (signature/date fields for SIGNiX) and mapping (template variables → deal data or Images). DTL parsing with list and image variable detection; mapping UI with Source optgroups (schema paths + Images) and type badges; apps.schema for deal paths.

**Implement:** Batch 1 (model, migrations), Batch 2 (CRUD + text tagging), Batch 3 (DTL parsing), Batch 4 (mapping UI). See PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md Section 7 and Section 7a.

---

## 3. PLAN-ADD-DOC-SET-TEMPLATES.md

**Purpose:** Document Set Templates—define ordered list of Static/Dynamic templates, associate with Deal Type. UI to configure (select templates, order with up/down, associate with Deal Type). Deals (with Deal Type) is already implemented per PLAN-ADD-DEALS.

**Implement:** Batch 1 (models, migrations, URL routing), Batch 2 (forms, formset, conversion helpers), Batch 3 (views, templates, sidebar). See PLAN-ADD-DOC-SET-TEMPLATES.md Section 7 and Section 7a.

---

## 4. PLAN-ADD-DOCUMENT-SETS.md

**Purpose:** Document Sets, Document Instances, Document Instance Versions. Generate Documents flow (create documents from templates), Regenerate Documents, Delete Document Set. Document viewing UI (table on Deal page, View latest, View all versions, in-browser PDF viewer). Extends the **Deal detail page** (View/Edit split implemented in PLAN-ADD-DEALS) with the Documents section. Send for Signature stub.

**Implement:** Batch 1 (models, migrations, Deal detail), Batch 2 (Generate for Static), Batch 3 (Generate for Dynamic, Regenerate, Delete), Batch 4 (Documents UI, version page, View/Download, Send stub). See PLAN-ADD-DOCUMENT-SETS.md Section 7 and Section 7a.

---

## 5. SIGNiX integration — see PLAN-SIGNiX-SUBMIT-MASTER.md

**Purpose:** Send for Signature, completion handling, and related SIGNiX features are **not** implemented as a single plan under PLAN-DOCS-MASTER. They are implemented via **PLAN-SIGNiX-SUBMIT-MASTER.md**, which follows PLAN-DOCS-MASTER plans 1–4 in the overall implementation order (see PLAN-MASTER.md). Plan 5 here is superseded by that master plan and its nine sub-plans.

---

## Summary Table

| Order | Plan                              | Key deliverables                                    |
|-------|-----------------------------------|-----------------------------------------------------|
| 1     | PLAN-ADD-STATIC-DOC-TEMPLATES.md  | Static PDF templates, ref_id, description, tagging_data |
| 2     | PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md | Dynamic HTML templates, mapping, text tagging       |
| 3     | PLAN-ADD-DOC-SET-TEMPLATES.md     | Document Set Templates, ordered template list       |
| 4     | PLAN-ADD-DOCUMENT-SETS.md         | Document Sets, generation, viewing UI               |
| 5     | *(superseded)* → PLAN-SIGNiX-SUBMIT-MASTER.md | SIGNiX submit flow; see PLAN-MASTER.md next steps |

---

## Outstanding Questions / Design Decisions (Future Plans)

Items to resolve when creating the corresponding plans:

| Plan | Topic | Notes |
|------|-------|-------|
| Doc Set Templates | Template ordering UI | **Decided:** Up/down buttons for v1 (see PLAN-ADD-DOC-SET-TEMPLATES.md). |
| Document Sets | Deal detail / View–Edit split | **Decided:** Implemented in PLAN-ADD-DEALS (deal_detail, View primary from list, Edit/Delete on detail). Document Sets adds Documents section to the existing detail page. |
| Document Sets | HTML-to-PDF | pdfkit/wkhtmltopdf per DESIGN-DOCS; see PLAN-ADD-DOCUMENT-SETS Section 12 for image URL handling. |
| SIGNiX | Integration design | **Resolved:** Implemented via PLAN-SIGNiX-SUBMIT-MASTER.md (see PLAN-MASTER.md). |

**Implementation order:** Deal Type is already implemented as part of PLAN-ADD-DEALS (PLAN-MASTER plan 2, PLAN-BIZ-DOMAIN-MASTER); Document Set Templates depend on it. Summary table above reflects the document-feature order.

---

*To implement document features: PLAN-MASTER plans 1–4 must be complete (they are the current platform; Deals includes Deal Type and the View/Edit split; Data Interface provides schema and deal data for Dynamic templates). Then implement PLAN-DOCS-MASTER plans 1–4 in order. For the SIGNiX submit flow, implement the plans in PLAN-SIGNiX-SUBMIT-MASTER.md per PLAN-MASTER.md.*

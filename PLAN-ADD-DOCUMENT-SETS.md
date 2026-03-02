# Plan: Add Document Sets

This document outlines how to add **Document Sets**, **Document Instances**, and **Document Instance Versions** to the Django lease application. A Document Set is attached to a Deal and contains the documents generated from templates (lease agreement, safety advisory, etc.). Users generate documents from the Deal page, view them, regenerate when data changes, and delete the document set when needed.

**Design reference:** DESIGN-DOCS.md — Document Sets, Document Instances, Document Instance Versions, Creation Flow, Re-generation Flow, Status Flow, User Experience, and Decisions Log. DESIGN-DATA-INTERFACE.md — `get_deal_data(deal)` and no-circumvention requirement for the context builder.

**Prerequisites:** PLAN-ADD-STATIC-DOC-TEMPLATES, PLAN-ADD-DYNAMIC-DOC-TEMPLATES, PLAN-ADD-DOC-SET-TEMPLATES, and PLAN-ADD-DEALS must be implemented. PLAN-MASTER plans 1–6 are implemented, including PLAN-DATA-INTERFACE (apps.schema provides `get_deal_data(deal)` for the context builder). Deal Type is in place; the deal detail page (View/Edit split) exists with Back, Edit, and Delete—list links to detail via View.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Models:** `DocumentSet`, `DocumentInstance`, `DocumentInstanceVersion`.
- **Flows:** Generate Documents (create from templates), Regenerate Documents (add new versions), Delete Document Set.
- **UI:** Deal detail page with Documents section (table, Generate/Regenerate/Delete buttons, View latest, View all versions). Document Instance page (version history, View/Download PDF). "Send for Signature" button present but stub until SIGNiX plan.
- **Access:** Authenticated users only (`@login_required`).

---

## 2. Model and Storage

- **App:** New app `apps.documents`.
- **Persistence:** SQLite for metadata; PDF files under `MEDIA_ROOT/documents/`.
- **Dependencies:** `apps.deals`, `apps.doctemplates`, `apps.schema`, `apps.vehicles`, `apps.contacts`, `apps.images`.
- **Python package:** `pdfkit` (add to `requirements.txt`). Assumes `wkhtmltopdf` is installed on the system (not a Python package).

### DocumentSet

- `deal` — `ForeignKey(Deal, on_delete=models.CASCADE, related_name='document_sets')`
- `document_set_template` — `ForeignKey(DocumentSetTemplate, on_delete=models.SET_NULL, null=True)` — template used to create; SET_NULL if template is deleted
- Conventions: `__str__`, `Meta` verbose names, `ordering = ['-id']` or by deal

### DocumentInstance

- `document_set` — `ForeignKey(DocumentSet, on_delete=models.CASCADE, related_name='instances')`
- `order` — `PositiveIntegerField` — order within the set (1-based)
- `content_type` — `ForeignKey(ContentType, on_delete=models.PROTECT)`
- `object_id` — `PositiveIntegerField`
- `source_template` — `GenericForeignKey('content_type', 'object_id')` — Static or Dynamic template
- `template_type` — `CharField(max_length=20)` — `"static"` or `"dynamic"` (denormalized for display)
- Conventions: `Meta` with `ordering = ['order']`, `UniqueConstraint` on (document_set, order)

### DocumentInstanceVersion

- `document_instance` — `ForeignKey(DocumentInstance, on_delete=models.CASCADE, related_name='versions')`
- `version_number` — `PositiveIntegerField` — sequential (1, 2, 3, …)
- `created_at` — `DateTimeField(auto_now_add=True)`
- `status` — `CharField(max_length=50)` — `"Draft"`, `"Submitted to SIGNiX"`, `"Final"`
- `file` — `FileField(upload_to="documents/%Y/%m/")`
- Conventions: `Meta` with `ordering = ['-version_number']`, `UniqueConstraint` on (document_instance, version_number)

---

## 3. Deal Detail Page

**Decision:** The View / Edit split is implemented in **PLAN-ADD-DEALS** and is in place. The deal detail page exists with "View" as the primary link from the list; Edit and Delete are on the detail page. This plan extends the deal detail page with the Documents section.

PLAN-ADD-DEALS provides: `deal_detail` view and template at `/deals/<pk>/`, list links to detail (View primary, no Edit on list), Back and Edit and Delete buttons on detail. This plan adds the Documents section below the deal summary.

- **URL:** `/deals/<pk>/` (name `deal_detail`) — already exists.
- **Content:** Deal summary (read-only) including deal type, lease officer, dates, payment, vehicles, contacts; Back, Edit, Delete buttons. This plan adds: Generate Documents (or Regenerate / Delete Document Set when set exists) and the Documents table.
- **Navigation:** No changes to list or detail navigation—already correct. Flow: List → View (detail) → Edit or Delete from there.

---

## 4. Sufficient Data Check

A Deal has **sufficient data** for document generation when:
- All Deal fields have values (no blank required fields)
- At least one vehicle
- At least one contact
- Lease officer (user) is set

Helper: `deal_has_sufficient_data(deal)` returns bool.

**Document Set Template check:** `can_generate` requires (1) sufficient data and (2) a Document Set Template exists for the deal's Deal Type. If no template exists, disable Generate and show: "No document set template configured for this deal type."

---

## 5. Generation Flow

### Generate Documents (initial)

1. Validate deal has sufficient data; validate Document Set Template exists for deal's Deal Type.
2. Create `DocumentSet` (deal, document_set_template).
3. For each `DocumentSetTemplateItem` (in order):
   - Get template (Static or Dynamic via `item.template`).
   - **Static:** Copy PDF file from template to new `DocumentInstanceVersion`; create `DocumentInstance`; add version with status "Draft".
   - **Dynamic:** Build context from deal + mapping; render HTML with DTL; convert to PDF (pdfkit/wkhtmltopdf); store in new `DocumentInstanceVersion`; create `DocumentInstance`; add version with status "Draft".

### Regenerate Documents

Same as Generate, but: use existing `DocumentSet` and `DocumentInstance`s; create *new* `DocumentInstanceVersion` records (version_number = next) instead of replacing. Do not delete previous versions.

### Atomicity

Wrap creation in `transaction.atomic()`. On any failure, roll back. Log errors with context.

---

## 6. Dynamic Template Rendering

1. **Context builder:** `build_document_context(deal, mapping)` — call `get_deal_data(deal)` from `apps.schema.services` to obtain the deal-centric structure; do not traverse Django models or QuerySets directly. Apply mapping and transforms to build the template context (e.g. `data.payment_amount` → nested `{"data": {"payment_amount": ...}}`). Resolve sources from the dict returned by `get_deal_data()`; apply transforms (date_day, concat, count, etc.). Per DESIGN-DATA-INTERFACE and DESIGN-DOCS no-circumvention requirement.
2. **Render:** `Template(html_string).render(Context(context))`.
3. **HTML-to-PDF:** Use `pdfkit` with `wkhtmltopdf`. wkhtmltopdf requires absolute URLs for images (e.g. `http://localhost:8000/media/...`).
4. **Image URLs — decided:** Generation runs from a view (POST to generate); pass `request` to the generation service. Use `request.build_absolute_uri()` for the base URL when rendering—Django's `{% static %}` and media URLs in the template will resolve relative to the request's host. For the HTML string passed to pdfkit, ensure `RequestContext` or a custom context includes a base URL (e.g. `base_url = request.build_absolute_uri('/')`); templates can use it to build absolute image URLs. Alternatively, post-process the rendered HTML to convert relative `/media/` and `/static/` URLs to absolute using `request.build_absolute_uri()`. Add optional `SITE_URL` in settings as fallback for any future generation outside request context (e.g. management command).

---

## 7. Pages and Behavior

### 7.1 Deal Detail (Documents section)

- **Before Document Set exists:** "Generate Documents" button (enabled when sufficient data). "Send for Signature" — inactive/disabled.
- **After Document Set exists:** "Regenerate Documents", "Delete Document Set", "Send for Signature" (active; stub — shows "SIGNiX integration coming soon" or similar). Documents table: Document name, Latest version (number, status, date), "View latest", "View all versions".

### 7.2 Document Instance (Version history)

- **URL:** `/deals/<deal_pk>/documents/<instance_pk>/` or `/documents/<instance_pk>/versions/`
- **Content:** Table of versions (latest first). Columns: Version, Status, Created; actions: View, Download.
- **View:** Open PDF in new tab (inline or new window).
- **Download:** `Content-Disposition: attachment`.

---

## 8. Implementation Order (Checklist)

### Batch 1 — Data layer and Deal detail (steps 1–4)

1. **Create `apps.documents` app**
   - Add app with models, urls, views, forms (minimal).
   - Add to `INSTALLED_APPS`.

2. **Models**
   - `DocumentSet`, `DocumentInstance`, `DocumentInstanceVersion` as in Section 2.

3. **Migrations**
   - Run `makemigrations` and `migrate`.

4. **Deal detail — Documents section**
   - The deal detail page (View/Edit split) is implemented in PLAN-ADD-DEALS. This step adds the **Documents** section to the existing deal detail template. Replace the placeholder with the Documents UI (Generate button, Documents table, etc.).
   - No changes to deal list or deal_detail view/URL — they already exist per PLAN-ADD-DEALS.

Batch 1 complete when models exist and deal detail loads.

### Batch 2 — Generation (Static only) (steps 5–7)

5. **Sufficient data and can_generate helpers**
   - `deal_has_sufficient_data(deal)` — returns bool.
   - `can_generate_documents(deal)` — returns bool (sufficient data and DocumentSetTemplate exists for deal.deal_type). Used to enable/disable Generate button and determine message when disabled.

6. **Generate Documents — Static templates**
   - View or service: given deal, get DocumentSetTemplate for deal_type; create DocumentSet; for each Static template item, copy PDF and create DocumentInstance + DocumentInstanceVersion. Use `transaction.atomic()`.

7. **Integrate on Deal detail**
   - Pass `deal`, `document_set` (or None), `can_generate` to template. When `can_generate` is False, disable button and show reason: "Create at least one vehicle and contact" (insufficient data) or "No document set template configured for this deal type" (no template).

Batch 2 complete when Generate works for Static-only Document Set Templates.

### Batch 3 — Generation (Dynamic) (steps 8–11)

8. **Add pdfkit dependency**
   - Add `pdfkit` to `requirements.txt` (e.g. `pdfkit>=1.0`). Run `pip install pdfkit`. Assumes `wkhtmltopdf` is already installed on the system.

9. **Context builder**
   - `build_document_context(deal, mapping)` — call `get_deal_data(deal)` from `apps.schema.services` to obtain deal data; resolve sources from that dict, apply transforms via `apply_transform()`. For list variables, pass list through; `item_map` optional when names match. Do not traverse models directly. See DESIGN-DOCS mapping types and DESIGN-DATA-INTERFACE.

10. **Dynamic render and HTML-to-PDF**
    - Read Dynamic template HTML; build context; render with `Template().render(Context())`; convert to PDF with pdfkit. Store PDF in `DocumentInstanceVersion.file`. Ensure image URLs are absolute for wkhtmltopdf.

11. **Regenerate and Delete Document Set**
    - Regenerate: same logic as Generate, but append new versions to existing DocumentInstances. Delete: remove DocumentSet (cascade deletes instances and versions); optionally delete PDF files from disk.

Batch 3 complete when Generate and Regenerate work for both Static and Dynamic templates.

### Batch 4 — UI (steps 12–15)

12. **Documents table on Deal detail**
    - Render table: document name (from source_template.ref_id or description), latest version info, "View latest", "View all versions" links.

13. **View latest / Document Instance page**
    - View for serving PDF (inline) and download. URL e.g. `/documents/versions/<pk>/view/` and `/documents/versions/<pk>/download/`.
    - Document Instance page: `/documents/instances/<pk>/` — list versions, View and Download per version.

14. **Send for Signature stub**
    - Button visible when document set exists. Click → message "SIGNiX integration will be available in a future release." or redirect to placeholder page. No status change.

15. **File cleanup**
    - On Delete Document Set, remove PDF files from storage.

Batch 4 complete when full UI works and PDFs view/download correctly.

---

## 7a. Implementation Batches and Verification

### Batch 1 — Data layer and Deal detail

**How to test after Batch 1:**

1. `python manage.py check` — no issues.
2. `python manage.py migrate` — `documents_documentset`, `documents_documentinstance`, `documents_documentinstanceversion` tables exist.
3. Shell — create DocumentSet, DocumentInstance, DocumentInstanceVersion with a test PDF:
   ```python
   from django.contrib.contenttypes.models import ContentType
   from apps.deals.models import Deal
   from apps.documents.models import DocumentSet, DocumentInstance, DocumentInstanceVersion
   from apps.doctemplates.models import DocumentSetTemplate, StaticDocumentTemplate
   from django.core.files.base import ContentFile

   deal = Deal.objects.first()
   dst = DocumentSetTemplate.objects.first()
   ds = DocumentSet.objects.create(deal=deal, document_set_template=dst)
   static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
   static_t = StaticDocumentTemplate.objects.first()
   di = DocumentInstance.objects.create(document_set=ds, order=1, content_type=static_ct, object_id=static_t.pk, template_type="static")
   div = DocumentInstanceVersion.objects.create(document_instance=di, version_number=1, status="Draft")
   div.file.save("test.pdf", ContentFile(b"%PDF-1.4 minimal"), save=True)
   assert DocumentSet.objects.filter(deal=deal).exists()
   ```
4. Visit `/deals/<deal_pk>/`; deal detail loads. Documents section shows placeholder or the created document.

### Batch 2 — Generation (Static)

**How to test after Batch 2:**

1. Create a Document Set Template with one Static template. Create a Deal with full data (vehicles, contacts, lease officer).
2. Visit deal detail; "Generate Documents" enabled. Click it. Redirect to deal detail; Document Set created.
3. Shell: `ds = DocumentSet.objects.get(deal_id=...); assert ds.instances.count() == 1; v = ds.instances.first().versions.first(); assert v.status == "Draft"; assert v.file`.
4. "View latest" link works; PDF displays in browser.

### Batch 3 — Generation (Dynamic)

**How to test after Batch 3:**

1. Add a Dynamic template (with mapping) to Document Set Template. Generate Documents for a Deal. Assert two DocumentInstances (Static + Dynamic); both have Draft versions with PDFs.
2. Regenerate Documents. Assert version_number 2 exists on each instance; version 1 still present.
3. Delete Document Set. Assert DocumentSet, instances, versions gone; PDF files removed from disk (if cleanup implemented).

### Batch 4 — UI

**How to test after Batch 4:**

1. Deal detail: Documents table shows document names, versions, View latest, View all versions.
2. View latest: PDF opens in browser.
3. View all versions: Document Instance page lists versions; View and Download work.
4. Send for Signature: click shows stub message.
5. Insufficient data / no template: Generate disabled when deal lacks data or when no Document Set Template exists for deal type; appropriate message shown.

---

## 9. File and URL Summary

| Item    | Value |
|---------|-------|
| App     | `apps.documents` |
| Models  | DocumentSet, DocumentInstance, DocumentInstanceVersion |
| Deal detail | `/deals/<pk>/` |
| Generate | POST to `/deals/<pk>/documents/generate/` (or similar) |
| Regenerate | POST `/deals/<pk>/documents/regenerate/` |
| Delete set | POST `/deals/<pk>/documents/delete/` |
| Document Instance | `/documents/instances/<pk>/` |
| View PDF | `/documents/versions/<pk>/view/` |
| Download PDF | `/documents/versions/<pk>/download/` |
| Storage | `MEDIA_ROOT/documents/` |

---

## 10. Out of Scope (This Phase)

- SIGNiX integration (plan 6) — Send for Signature is a stub.
- Edit UI for Document Instances or Versions (view-only per design).
- Pagination on version list.
- HTML-to-PDF alternatives (pdfkit/wkhtmltopdf per DESIGN-DOCS).

---

## 11. Implementation Notes

- **pdfkit:** Add `pdfkit` to `requirements.txt` (step 8). Assumes `wkhtmltopdf` is installed on the system. Use `pdfkit.from_string(html, False, options={'base': base_url})` with `base_url = request.build_absolute_uri('/')` so relative URLs in the HTML resolve. Add optional `SITE_URL` in settings for future use when generation runs without a request.
- **Context builder:** Call `get_deal_data(deal)` from `apps.schema.services` to obtain deal data—do not traverse models directly. Work from the returned dict; mapping keys use dot notation (e.g. `data.payment_amount`). Build nested context: `{"data": {"payment_amount": value}}`. For list variables (e.g. `data.jet_pack_list` → `deal.vehicles`), pass list through; when template item field names match schema, no `item_map` needed. For "first contact" or "first vehicle", use index 0: `deal_data["deal"]["contacts"][0]`, `deal_data["deal"]["vehicles"][0]`.
- **Transforms (v1):** Use `apps.doctemplates.utils.apply_transform(value, transform_name)` for date transforms and others. Implemented: `date_day`, `date_month`, `date_year`, `date_month_day` (outputs "September 1" from ISO date), `number_to_word` (0–99), `plural_suffix` ("" if count==1 else "s"), `concat` (join with single space), `count`. Other transforms per DESIGN-DOCS.
- **Atomicity:** Use `with transaction.atomic():` around entire Generate/Regenerate flow. On exception, rollback and re-raise or return error to user.
- **Logging:** Log each step (template lookup, context build, render, PDF conversion, file save) with deal id, template ref_id. On error, log exception with context.

---

## 12. Open Questions / Significant Implementation Decisions

| # | Topic | Notes |
|---|-------|-------|
| 1 | **Deal detail vs Edit** | **Decided and implemented in PLAN-ADD-DEALS:** deal_detail view, View primary from list, Edit and Delete on detail. This plan extends the detail page with Documents. See Section 3. |
| 2 | **Image URLs for wkhtmltopdf** | **Decided:** Pass `request` to generation; use `request.build_absolute_uri('/')` as base for pdfkit. Add optional `SITE_URL` in settings as fallback. See Section 6 and Implementation Notes. |
| 3 | **Transform implementations** | **Decided:** Use `apps.doctemplates.utils.apply_transform()`. Date transforms (date_day, date_month, date_year, date_month_day) handle ISO strings; `date_month_day` outputs "September 1". `number_to_word` 0–99; `plural_suffix` "" if count==1 else "s"; `concat` join with single space. See Implementation Notes. |
| 4 | **First contact / first vehicle** | **Decided:** Resolve from `get_deal_data(deal)` output: `deal_data["deal"]["contacts"][0]`, `deal_data["deal"]["vehicles"][0]`. Vehicles and contacts are ordered by id in `get_deal_data()` per DESIGN-DATA-INTERFACE. See Implementation Notes. |
| 5 | **Document Set Template missing** | **Decided:** If Deal's Deal Type has no Document Set Template, disable Generate and show "No document set template configured for this deal type." See Section 4 and Batch 2. |

---

*End of plan. Proceed to implementation only after review.*

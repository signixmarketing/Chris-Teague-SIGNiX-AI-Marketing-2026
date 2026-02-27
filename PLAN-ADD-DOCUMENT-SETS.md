# Plan: Add Document Sets

This document outlines how to add **Document Sets**, **Document Instances**, and **Document Instance Versions** to the Django lease application. A Document Set is attached to a Deal and contains the documents generated from templates (lease agreement, safety advisory, etc.). Users generate documents from the Deal page, view them, regenerate when data changes, and delete the document set when needed.

**Design reference:** DESIGN-DOCS.md — Document Sets, Document Instances, Document Instance Versions, Creation Flow, Re-generation Flow, Status Flow, User Experience, and Decisions Log.

**Prerequisites:** PLAN-ADD-STATIC-DOC-TEMPLATES, PLAN-ADD-DYNAMIC-DOC-TEMPLATES, PLAN-ADD-DEAL-TYPE, and PLAN-ADD-DOC-SET-TEMPLATES must be implemented.

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
- **Dependencies:** `apps.deals`, `apps.doctemplates`, `apps.vehicles`, `apps.contacts`, `apps.images`.
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

**Decision:** Add a dedicated Deal detail page and make "View" the primary entry point from the list. Edit and Delete become actions on the detail page.

The current deals app has list, add, edit, delete but no detail view. Add `deal_detail` view and template.

- **URL:** `/deals/<pk>/` (name `deal_detail`).
- **Content:** Display deal summary (read-only) and **Documents** section at bottom. Action buttons: Edit, Delete, Generate Documents (or Regenerate / Delete Document Set when set exists).
- **Navigation:** Update deal list — make "View" the primary link (replace or add alongside Edit). Each row links to deal_detail. On the detail page, show Edit and Delete buttons. Users flow: List → View (detail) → Edit or Delete from there.

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

1. **Context builder:** `build_document_context(deal, mapping)` — produces dict matching template variable structure (e.g. `data.payment_amount` → nested `{"data": {"payment_amount": ...}}`). Resolve sources (deal.payment_amount, deal.vehicles, etc.); apply transforms (date_day, concat, count, etc.).
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

4. **Deal detail view**
   - Add `deal_detail` view and template. Show deal summary; action buttons Edit, Delete; placeholder for Documents section.
   - Update deal list: make "View" the primary link (link row or first column to deal_detail). Keep Edit and Delete as secondary links, or remove them from list (they become buttons on the detail page).
   - Add `path("<int:pk>/", ...)` for deal_detail in deals URLs (before `<int:pk>/edit/` to avoid conflict).

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
   - `build_document_context(deal, mapping)` — resolve sources, apply transforms. Handle `deal.vehicles`, `deal.contacts`, `item_map` for list variables. See DESIGN-DOCS mapping types.

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
- **Context builder:** Mapping keys use dot notation (e.g. `data.payment_amount`). Build nested dict: `{"data": {"payment_amount": value}}`. For list variables, build list of dicts from `deal.vehicles` with `item_map` field mapping. For "first contact" or "first vehicle" (e.g. `deal.contacts[0]`), use `deal.contacts.order_by('id').first()` and `deal.vehicles.order_by('id').first()`.
- **Transforms (v1):** `number_to_word`: support 0–99; return "zero"–"ninety-nine"; outside range fallback to str(n). `plural_suffix`: "" if count==1 else "s". `concat`: join with single space by default; no configurable delimiter in v1. Other transforms per DESIGN-DOCS (date_day, date_month, date_year, count).
- **Atomicity:** Use `with transaction.atomic():` around entire Generate/Regenerate flow. On exception, rollback and re-raise or return error to user.
- **Logging:** Log each step (template lookup, context build, render, PDF conversion, file save) with deal id, template ref_id. On error, log exception with context.

---

## 12. Open Questions / Significant Implementation Decisions

| # | Topic | Notes |
|---|-------|-------|
| 1 | **Deal detail vs Edit** | **Decided:** Add dedicated deal_detail view. Make "View" the primary link from the list; Edit and Delete are buttons on the detail page. See Section 3. |
| 2 | **Image URLs for wkhtmltopdf** | **Decided:** Pass `request` to generation; use `request.build_absolute_uri('/')` as base for pdfkit. Add optional `SITE_URL` in settings as fallback. See Section 6 and Implementation Notes. |
| 3 | **Transform implementations** | **Decided:** `number_to_word` 0–99, fallback to str outside range; `plural_suffix` "" if count==1 else "s"; `concat` join with single space. See Implementation Notes. |
| 4 | **First contact / first vehicle** | **Decided:** Use `deal.contacts.order_by('id').first()` and `deal.vehicles.order_by('id').first()` for stable ordering. See Implementation Notes. |
| 5 | **Document Set Template missing** | **Decided:** If Deal's Deal Type has no Document Set Template, disable Generate and show "No document set template configured for this deal type." See Section 4 and Batch 2. |

---

*End of plan. Proceed to implementation only after review.*

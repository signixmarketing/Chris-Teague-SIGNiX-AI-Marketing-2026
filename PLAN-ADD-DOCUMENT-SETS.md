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
- `source_document_template` — `GenericForeignKey('content_type', 'object_id')` — Static or Dynamic template this instance was created from
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

**Document Set Template check:** `can_generate` requires (1) sufficient data and (2) a Document Set Template exists for the deal's Deal Type. Document Set Templates are configured per Deal Type (one template per type, per PLAN-ADD-DOC-SET-TEMPLATES). Look up the template by deal type, e.g. `DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).first()`. If none exists, disable Generate and show: "No document set template configured for this deal type."

---

## 5. Generation Flow

### Generate Documents (initial)

1. Validate deal has sufficient data; validate Document Set Template exists for deal's Deal Type (lookup by `deal.deal_type` as above).
2. Create `DocumentSet` (deal, document_set_template).
3. For each item in the template's ordered list (e.g. `document_set_template.items.all()`, which is ordered by `order` per apps.doctemplates):
   - Get the template (Static or Dynamic) from the item (e.g. `item.template` GenericForeignKey).
   - **Static:** Copy PDF file from template to new `DocumentInstanceVersion`; create `DocumentInstance`; add version with status "Draft".
   - **Dynamic:** Build context from deal + mapping; render HTML with DTL; convert to PDF (pdfkit/wkhtmltopdf); store in new `DocumentInstanceVersion`; create `DocumentInstance`; add version with status "Draft".

### Regenerate Documents

Same as Generate, but: use existing `DocumentSet` and `DocumentInstance`s; create *new* `DocumentInstanceVersion` records (version_number = next) instead of replacing. Do not delete previous versions.

### Atomicity

Wrap creation in `transaction.atomic()`. On any failure, roll back. Log errors with context.

---

## 6. Dynamic Template Rendering

The context builder (implemented in `apps.documents`) produces the template context from the deal, the template's mapping, and an optional request. Deal data and image URLs are resolved as follows.

1. **Deal data:** Call `get_deal_data(deal)` from `apps.schema.services`; do not traverse Django models or QuerySets for deal paths. Resolve each mapping entry's source from the returned dict. Apply transforms via `apps.doctemplates.utils.apply_transform()` (date_day, date_month_day, count, number_to_word, plural_suffix, etc.). Build nested context (e.g. `data.payment_amount` → `{"data": {"payment_amount": ...}}`). Per DESIGN-DATA-INTERFACE and DESIGN-DOCS.
2. **Image variables:** For mapping entries whose `source` starts with `image:`, parse the UUID and resolve via `Image.objects.get(uuid=...)` (apps.images.models). If the Image does not exist, raise a clear error so generation fails with an actionable message. Set the context value to the image file URL. When building for PDF, the URL must be absolute so wkhtmltopdf can load it: use `request.build_absolute_uri(image.file.url)` when request is provided; when request is None (e.g. management command), use `settings.SITE_URL` + relative path when SITE_URL is set (otherwise relative URLs may cause wkhtmltopdf to fail).
3. **Render:** `Template(html_string).render(Context(context))`.
4. **HTML-to-PDF:** Use `pdfkit` with `wkhtmltopdf`. Pass a base URL (e.g. `request.build_absolute_uri('/')` or `SITE_URL`) so relative URLs in the rendered HTML resolve. Image URLs injected by the context builder are already absolute when request is present; when generation runs without a request, set `SITE_URL` in settings for correct image loading.

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
   - In `apps.documents` (e.g. `services.py`), implement `build_document_context(deal, mapping, request=None)` per Section 6: resolve deal data from `get_deal_data(deal)` and apply transforms; resolve image sources via the Image model and raise a clear error if an Image is missing; supply absolute image URLs (using request when present, else `SITE_URL`). Use `apps.doctemplates.utils.apply_transform()` for transforms. Do not traverse models for deal paths.

10. **Dynamic render and HTML-to-PDF**
    - Read Dynamic template HTML; build context; render with `Template().render(Context())`; convert to PDF with pdfkit. Store PDF in `DocumentInstanceVersion.file`. Ensure image URLs are absolute for wkhtmltopdf.

11. **Regenerate and Delete Document Set**
    - Regenerate: same logic as Generate, but append new versions to existing DocumentInstances. Delete: remove DocumentSet (cascade deletes instances and versions); optionally delete PDF files from disk.

Batch 3 complete when Generate and Regenerate work for both Static and Dynamic templates.

### Batch 4 — UI (steps 12–15)

12. **Documents table on Deal detail**
    - Render table: document name (from source_document_template.ref_id or description), latest version info, "View latest", "View all versions" links.

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

- **pdfkit:** Add `pdfkit` to `requirements.txt` (step 8). Assumes `wkhtmltopdf` is installed. Use `pdfkit.from_string(html, False, options={'base': base_url})` with `base_url = request.build_absolute_uri('/')` when request is present, or `settings.SITE_URL` when generation runs without a request (e.g. management command).
- **Context builder:** Implement in `apps.documents` (e.g. `services.py`). Resolve deal data from `get_deal_data(deal)`; build nested context from mapping and apply transforms via `apply_transform()`. For list variables, pass lists through; for "first contact" or "first vehicle", use index 0 on the deal data structure. Resolve image sources (`source` starting with `image:`) via the Image model; raise a clear error if the Image does not exist. Use `request.build_absolute_uri(image.file.url)` for image URLs when request is present; when request is None, use `settings.SITE_URL` + relative path (unset SITE_URL may cause wkhtmltopdf to fail on images).
- **Transforms (v1):** Use `apps.doctemplates.utils.apply_transform(value, transform_name)` for date transforms and others. Implemented: `date_day`, `date_month`, `date_year`, `date_month_day` (outputs "September 1" from ISO date), `count`, `number_to_word` (0–99), `plural_suffix` ("" if count==1 else "s"). Other transforms per DESIGN-DOCS.
- **Atomicity:** Use `with transaction.atomic():` around entire Generate/Regenerate flow. On exception, rollback and re-raise or return error to user.
- **Logging:** Log each step (template lookup, context build, render, PDF conversion, file save) with deal id, template ref_id. On error, log exception with context.

---

## 12. Implementation Decisions

The following are fixed for this plan so that implementation is consistent.

| # | Topic | Decision |
|---|-------|----------|
| 1 | **Deal detail** | Deal detail page (View primary from list, Edit/Delete on detail) is implemented in PLAN-ADD-DEALS. This plan adds the Documents section to that page. See Section 3. |
| 2 | **Image URLs for PDF** | Pass `request` to generation; use `request.build_absolute_uri('/')` as base for pdfkit. Use `SITE_URL` in settings when generation runs without a request (e.g. management command). See Section 6. |
| 3 | **Transforms** | Use `apps.doctemplates.utils.apply_transform()`. Supported: date_day, date_month, date_year, date_month_day, count, number_to_word, plural_suffix. See Implementation Notes. |
| 4 | **First contact / first vehicle** | Resolve from `get_deal_data(deal)` output at index 0; ordering is by id per DESIGN-DATA-INTERFACE. |
| 5 | **No Document Set Template** | If the deal's Deal Type has no Document Set Template, disable Generate and show "No document set template configured for this deal type." See Section 4. |
| 6 | **Image resolution** | Mapping entries with source `image:<uuid>` are resolved via the Image model; context value is the image file URL (absolute when building for PDF). See Section 6 and DESIGN-DOCS "Image references in dynamic templates." |
| 7 | **Context builder location** | Implement `build_document_context` in `apps.documents` (e.g. `services.py`). Used only at generation time. |
| 8 | **Missing Image at generation** | If an Image referenced by mapping no longer exists, raise a clear error; do not substitute empty string. |
| 9 | **Generation without request** | When `request` is None, use `SITE_URL` + relative path for image URLs. If SITE_URL is unset, image loading in wkhtmltopdf may fail—document as a limitation. |

---

*End of plan. Proceed to implementation only after review.*

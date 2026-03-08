# Plan: Add Document Sets

This document outlines how to add **Document Sets**, **Document Instances**, and **Document Instance Versions** to the Django lease application. A Document Set is attached to a Deal and contains the documents generated from templates (lease agreement, safety advisory, etc.). Users generate documents from the Deal page, view them, regenerate when data changes, and delete the document set when needed.

**Design reference:** DESIGN-DOCS.md — Document Sets, Document Instances, Document Instance Versions, Creation Flow, Re-generation Flow, Status Flow, User Experience, and Decisions Log. DESIGN-DATA-INTERFACE.md — `get_deal_data(deal)` and no-circumvention requirement for the context builder.

**Prerequisites:** PLAN-ADD-STATIC-DOC-TEMPLATES, PLAN-ADD-DYNAMIC-DOC-TEMPLATES, PLAN-ADD-DOC-SET-TEMPLATES, and PLAN-ADD-DEALS must be implemented. PLAN-MASTER plans 1–4 are implemented, including PLAN-DATA-INTERFACE (apps.schema provides `get_deal_data(deal)` for the context builder). Deal Type is in place; the deal detail page (View/Edit split) exists with Back, Edit, and Delete—list links to detail via View.

**Review this plan before implementation.** Implementation order is in **Section 8**; **Section 7a** defines batches and verification. **All four batches are implemented**; the plan is kept as the single source of truth for behavior and future changes.

---

## 1. Goals and Scope

- **Models:** `DocumentSet`, `DocumentInstance`, `DocumentInstanceVersion`.
- **Flows:** Generate Documents (create from templates), Regenerate Documents (add new versions), Delete Document Set.
- **UI:** Deal detail page with Documents section (table, Generate/Regenerate/Delete buttons, View latest, Download latest, View all versions). Document Instance page (version history, View and Download PDF per version). "Send for Signature" button (implemented in PLAN-SIGNiX-SEND-FOR-SIGNATURE, Plan 7; was a stub until then).
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
- `file` — `FileField(upload_to="documents/%Y/%m/")` — allow `blank=True` so a version can be created before the PDF is written (generation creates the version then saves the file).
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

### Service layer and contract

Generation is implemented in a **service layer** in `apps.documents` (e.g. `services.py`). Views do not contain generation logic; they call the service and handle success or caught exception.

**Orchestration entry points**

- **`generate_documents_for_deal(deal, request=None)`** — Initial generation. **Inputs:** `deal` (Deal instance), `request` (HttpRequest or None; used for absolute URLs when building Dynamic context). **Returns:** The created `DocumentSet` on success. **On failure:** Raises `DocumentGenerationError` (or equivalent) with a user-facing message; the view catches it, sets `messages.error`, and does not redirect to success. Failure cases include insufficient data, no Document Set Template for the deal's Deal Type, and any error during template render or PDF creation.
- **`regenerate_documents(document_set, request=None)`** — Add new versions to an existing set. **Inputs:** `document_set` (existing DocumentSet), `request` (optional). **Returns:** The same `DocumentSet` on success. **On failure:** Same exception; view handles similarly.

**Dynamic rendering (internal to the service)**

- **`render_dynamic_template_to_pdf(deal, dynamic_template, request=None)`** — **Inputs:** `deal`, `dynamic_template` (DynamicDocumentTemplate), `request` (optional). **Returns:** PDF content as `bytes`. The orchestrator creates the DocumentInstance and DocumentInstanceVersion and saves the returned bytes to the version's file. **On failure:** Raises (e.g. missing image, render error, pdfkit failure); orchestrator wraps or re-raises as `DocumentGenerationError`.

**Static path:** No separate service function; the orchestrator (or a small private helper in the same module) copies the static template file and creates DocumentInstance + DocumentInstanceVersion for each Static item.

---

## 6. Dynamic Template Rendering

The **context builder** and **Dynamic render-to-PDF** logic live in the same service module as the orchestration (Section 5). The context builder produces the template context from the deal, the template's mapping, and an optional request. Deal data and image URLs are resolved as follows.

1. **Deal data:** Call `get_deal_data(deal)` from `apps.schema.services`; do not traverse Django models or QuerySets for deal paths. Resolve each mapping entry's source from the returned dict. Apply transforms via `apps.doctemplates.utils.apply_transform()` (date_day, date_month_day, count, number_to_word, plural_suffix, etc.). Build nested context (e.g. `data.payment_amount` → `{"data": {"payment_amount": ...}}`). Per DESIGN-DATA-INTERFACE and DESIGN-DOCS.
2. **Image variables:** For mapping entries whose `source` starts with `image:`, parse the UUID and resolve via `Image.objects.get(uuid=...)` (apps.images.models). If the Image does not exist, raise a clear error so generation fails with an actionable message. Set the context value to the image file URL. When building for PDF, the URL must be absolute so wkhtmltopdf can load it: use `request.build_absolute_uri(image.file.url)` when request is provided; when request is None (e.g. management command), use `settings.SITE_URL` + relative path when SITE_URL is set (otherwise relative URLs may cause wkhtmltopdf to fail).
3. **Render:** `Template(html_string).render(Context(context))`.
4. **HTML-to-PDF:** Use `pdfkit` with `wkhtmltopdf`. Many system builds of wkhtmltopdf (e.g. 0.12.6) do **not** support `--base-url`; do not pass it or pdfkit will fail with "Unknown long argument --base-url". Image URLs injected by the context builder are already absolute when request is present; rely on that for image loading. When generation runs without a request, set `SITE_URL` in settings for correct image loading.

---

## 7. Pages and Behavior

### 7.1 Deal Detail (Documents section)

- **Before Document Set exists:** "Generate Documents" button (enabled when sufficient data). "Send for Signature" — inactive/disabled.
- **After Document Set exists:** "Regenerate Documents", "Delete Document Set", "Send for Signature" (active; implemented in Plan 7 — calls SIGNiX orchestrator, opens first signer URL in new window; see PLAN-SIGNiX-SEND-FOR-SIGNATURE). Documents table: Document name, Latest version (number, status, date), "View latest", "Download latest", "View all versions".

### 7.2 Document Instance (Version history)

- **URL:** `/documents/instances/<pk>/` (name `document_instance_detail`). Config includes `path("documents/", include("apps.documents.urls"))`.
- **Content:** Table of versions (latest first). Columns: Version, Status, Created; actions: View (opens PDF inline), Download (attachment). "Back to Deal #&lt;id&gt;" link to deal detail.
- **View:** Serve PDF with `Content-Disposition: inline` so the browser displays it (e.g. in a new tab). URL `/documents/versions/<pk>/view/`.
- **Download:** Serve PDF with `Content-Disposition: attachment`. URL `/documents/versions/<pk>/download/`. Return 404 if the version has no file.

---

## 8. Implementation Order (Checklist)

### Batch 1 — Data layer and Deal detail (steps 1–4)

1. **Create `apps.documents` app**
   - Add app with models, urls, views (minimal); forms optional for Batch 1.
   - Add to `INSTALLED_APPS`.

2. **Models**
   - `DocumentSet`, `DocumentInstance`, `DocumentInstanceVersion` as in Section 2.

3. **Migrations**
   - Run `makemigrations` and `migrate`.

4. **Deal detail — Documents section**
   - The deal detail page (View/Edit split) is implemented in PLAN-ADD-DEALS. This step adds the **Documents** section to the existing deal detail template. Replace the placeholder with the Documents UI (Generate button, Documents table, etc.).
   - Update the deal_detail view to prefetch `document_sets__instances__versions` and pass `document_set = deal.document_sets.first()` so the template can render the Documents section (and, when a set exists, the instances table) without N+1 queries. No changes to deal list or deal_detail URL.

Batch 1 complete when models exist and deal detail loads.

### Batch 2 — Generation (Static only) (steps 5–7)

5. **Sufficient data and can_generate helpers**
   - `deal_has_sufficient_data(deal)` — returns bool.
   - `can_generate_documents(deal)` — returns bool (sufficient data and DocumentSetTemplate exists for deal.deal_type). Used to enable/disable Generate button and determine message when disabled.
   - `get_cannot_generate_reason(deal)` — returns a user-facing reason string (or None if generation is allowed); used by the view/template when `can_generate` is False.

6. **Generation service — orchestration and Static path**
   - In `apps.documents` (e.g. `services.py`), implement `generate_documents_for_deal(deal, request=None)` per Section 5 and the service contract: validate sufficient data and template existence; create DocumentSet; for each template item, handle **Static** only (copy PDF, create DocumentInstance + DocumentInstanceVersion); skip or ignore Dynamic items until Batch 3. If the template has no Static items, still create the DocumentSet (with zero instances). Use `transaction.atomic()`. On any failure, raise `DocumentGenerationError` with a user-facing message.
   - Define `DocumentGenerationError` (e.g. in the same module or `apps.documents.exceptions`) so the view can catch it.

7. **Integrate on Deal detail**
   - View (e.g. POST handler for Generate): call `generate_documents_for_deal(deal, request)`; on success, set success message and redirect to deal detail; on `DocumentGenerationError`, set `messages.error` with the exception message and re-render deal detail. Pass `deal`, `document_set` (or None), `can_generate`, and when `can_generate` is False pass a **reason** (e.g. from `get_cannot_generate_reason(deal)`) so the template can show why Generate is disabled. When `can_generate` is False, disable button and show reason: "Create at least one vehicle and contact" (insufficient data) or "No document set template configured for this deal type" (no template).

Batch 2 complete when Generate works for Static-only Document Set Templates.

**Status: Implemented.** View passes `can_generate` and `cannot_generate_reason` (from `get_cannot_generate_reason(deal)`). Generate is a POST form to `/deals/<pk>/documents/generate/`. Regenerate and Delete Document Set are wired in Batch 3. "View latest" / "View all versions" are not wired until Batch 4.

### Batch 3 — Generation (Dynamic) (steps 8–11)

8. **Add pdfkit dependency**
   - Add `pdfkit>=1.0` to `requirements.txt`. As part of implementation: run `pip install -r requirements.txt` or `.venv/bin/pip install "pdfkit>=1.0"` so the Python package is installed. Verify system dependency: run `wkhtmltopdf --version` (e.g. 0.12.6); if missing, install via package manager (e.g. `apt install wkhtmltopdf`, `brew install wkhtmltopdf`).

9. **Context builder**
   - In the same service module, implement `build_document_context(deal, mapping, request=None)` per Section 6: resolve deal data from `get_deal_data(deal)` and apply transforms; resolve image sources via the Image model and raise a clear error if an Image is missing; supply absolute image URLs (using request when present, else `SITE_URL`). Use `apps.doctemplates.utils.apply_transform()` for transforms. Do not traverse models for deal paths.

10. **Dynamic render and HTML-to-PDF**
    - In the same module, implement `render_dynamic_template_to_pdf(deal, dynamic_template, request=None)` per the service contract: read Dynamic template HTML; call `build_document_context(deal, template.mapping, request)`; render with `Template().render(Context())`; convert to PDF with pdfkit; **return PDF as `bytes`**. The orchestrator (in `generate_documents_for_deal` / `regenerate_documents`) creates DocumentInstance and DocumentInstanceVersion and saves the returned bytes to the version's file. Ensure image URLs are absolute for wkhtmltopdf. **Do not pass `--base-url` to wkhtmltopdf** — many builds (e.g. 0.12.6) do not support it and will fail with "Unknown long argument --base-url". On failure, raise; orchestrator wraps or re-raises as `DocumentGenerationError`. Before calling pdfkit, check that wkhtmltopdf is available (see wkhtmltopdf check below) and raise `DocumentGenerationError` with install instructions if not.

11. **Regenerate and Delete Document Set**
    - Implement `regenerate_documents(document_set, request=None)` per the service contract; call it from the Regenerate POST view. Delete: remove DocumentSet (cascade deletes instances and versions); delete PDF files from disk in the same flow (see step 15). View for Delete calls the same pattern (success message or caught exception if added later).

Batch 3 complete when Generate and Regenerate work for both Static and Dynamic templates.

**Status: Implemented.** Generate processes both Static and Dynamic template items. Regenerate and Delete are wired: POST to `/deals/<pk>/documents/regenerate/` and `/deals/<pk>/documents/delete/`. File cleanup on delete is implemented. The app includes a wkhtmltopdf availability check: before PDF conversion, `_require_wkhtmltopdf()` raises `DocumentGenerationError` if wkhtmltopdf is not on PATH; a Django system check (`documents.W001`) warns when wkhtmltopdf is missing so `manage.py check` reports it. pdfkit options omit `--base-url` for compatibility with wkhtmltopdf 0.12.6. "View latest" / "View all versions" remain disabled until Batch 4.

### Batch 4 — UI (steps 12–15)

12. **Documents table on Deal detail**
    - Render table: document name (from source_document_template.ref_id or description), latest version info, "View latest" (inline PDF), "Download latest" (attachment), "View all versions" (link to instance detail page).

13. **View latest / Document Instance page**
    - View for serving PDF (inline) and download. URL e.g. `/documents/versions/<pk>/view/` and `/documents/versions/<pk>/download/`.
    - Document Instance page: `/documents/instances/<pk>/` — list versions, View and Download per version.

14. **Send for Signature**
    - Button visible when document set exists. POST to `/deals/<pk>/documents/send-for-signature/` — implemented in Plan 7 (PLAN-SIGNiX-SEND-FOR-SIGNATURE): calls orchestrator; on success opens first signer URL in new window; on validation/API error shows message and stays on deal detail.

15. **File cleanup**
    - On Delete Document Set, remove PDF files from storage. (Implemented in Batch 3 as part of `delete_document_set`.)

Batch 4 complete when full UI works and PDFs view/download correctly.

**Status: Implemented.** Documents table has "View latest" (inline PDF), "Download latest", and "View all versions" (instance detail page with version list and View/Download per version). URLs: `/documents/versions/<pk>/view/`, `/documents/versions/<pk>/download/`, `/documents/instances/<pk>/`. Send for Signature: implemented in Plan 7 (PLAN-SIGNiX-SEND-FOR-SIGNATURE); POST to `/deals/<pk>/documents/send-for-signature/` calls orchestrator, opens first signer URL in new window on success. File cleanup was implemented in Batch 3.

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
   # If no DocumentSetTemplate exists, create one (e.g. for default DealType) or use a fixture.
   if not dst:
       from apps.deals.models import DealType
       dst = DocumentSetTemplate.objects.create(deal_type=DealType.get_default(), name="Test")
   ds = DocumentSet.objects.create(deal=deal, document_set_template=dst)
   static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
   static_t = StaticDocumentTemplate.objects.first()
   if static_t:
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
4. Documents section shows the document set and table (document name, latest version). "View latest" and "View all versions" remain disabled until Batch 4.

### Batch 3 — Generation (Dynamic)

**How to test after Batch 3:**

1. Verify wkhtmltopdf: run `wkhtmltopdf --version`. Install pdfkit: `pip install -r requirements.txt` (or `.venv/bin/pip install "pdfkit>=1.0"`).
2. Add a Dynamic template (with mapping) to Document Set Template. Generate Documents for a Deal. Assert two DocumentInstances (Static + Dynamic); both have Draft versions with PDFs.
3. Regenerate Documents (button now active). Assert version_number 2 exists on each instance; version 1 still present.
4. Delete Document Set (button now active). Assert DocumentSet, instances, versions gone; PDF files removed from disk. After delete, "Generate Documents" form is shown again; generate again to confirm full cycle.
5. "View latest" and "View all versions" remain disabled until Batch 4.
6. Optional: run `python manage.py check` — if wkhtmltopdf is missing, a warning (documents.W001) is shown.

### Batch 4 — UI

**How to test after Batch 4:**

1. Deal detail: Documents table shows document names, latest version, View latest, Download latest, View all versions (all active).
2. View latest: PDF opens in browser (inline). Download latest: PDF downloads.
3. View all versions: Document Instance page (`/documents/instances/<pk>/`) lists versions (latest first); View and Download per version work.
4. Send for Signature: button POSTs; calls SIGNiX (Plan 7); on success opens signing URL in new window; on error shows message.
5. Insufficient data / no template: Generate disabled when deal lacks data or when no Document Set Template exists for deal type; appropriate message shown.

---

## 9. File and URL Summary

| Item    | Value |
|---------|-------|
| App     | `apps.documents` |
| Models  | DocumentSet, DocumentInstance, DocumentInstanceVersion |
| Deal detail | `/deals/<pk>/` |
| Generate | POST to `/deals/<pk>/documents/generate/` |
| Regenerate | POST `/deals/<pk>/documents/regenerate/` |
| Delete set | POST `/deals/<pk>/documents/delete/` |
| Send for Signature | POST `/deals/<pk>/documents/send-for-signature/` |
| Document Instance | `/documents/instances/<pk>/` |
| View PDF (inline) | `/documents/versions/<pk>/view/` |
| Download PDF | `/documents/versions/<pk>/download/` |
| Storage | `MEDIA_ROOT/documents/` |

**App ownership:** Deal-scoped document actions (Generate, Regenerate, Delete Document Set, Send for Signature) are implemented in **apps.deals** and live under `/deals/<pk>/documents/...`. Document viewing—instance detail page and version view/download—is implemented in **apps.documents** and lives under `/documents/...`. The deal detail view renders the Documents section and passes `document_set`, `can_generate`, and `cannot_generate_reason`; it does not contain generation logic (that is in the documents service layer).

---

## 10. Out of Scope (This Phase)

- SIGNiX integration — Send for Signature is implemented (Plan 7, PLAN-SIGNiX-SEND-FOR-SIGNATURE). Dashboard and Deal View transaction list are Plan 8–9.
- Edit UI for Document Instances or Versions (view-only per design).
- Pagination on version list.
- HTML-to-PDF alternatives (pdfkit/wkhtmltopdf per DESIGN-DOCS).

---

## 11. Implementation Notes

- **pdfkit:** Add `pdfkit>=1.0` to `requirements.txt` (step 8). Run `pip install -r requirements.txt` or `.venv/bin/pip install "pdfkit>=1.0"`. Verify wkhtmltopdf with `wkhtmltopdf --version`. **Do not pass `--base-url` to pdfkit/wkhtmltopdf** — common builds (e.g. wkhtmltopdf 0.12.6) do not support it and exit with "Unknown long argument --base-url". Image URLs in the context are built absolute when request is present; that is sufficient for images. Use `pdfkit.from_string(html, False, options={...})` with only supported options (e.g. `enable-local-file-access` if needed); omit base-url.
- **wkhtmltopdf check:** Implement `check_wkhtmltopdf_available()` (e.g. `shutil.which("wkhtmltopdf")` plus `subprocess.run([path, "--version"], ...)`). Call it before PDF conversion and raise `DocumentGenerationError` with install instructions if missing. Register a Django system check (e.g. `documents.W001`) that warns when wkhtmltopdf is not available so `manage.py check` reports it.
- **Context builder:** Implement in `apps.documents` (e.g. `services.py`). Resolve deal data from `get_deal_data(deal)`; build nested context from mapping and apply transforms via `apply_transform()`. For list variables, pass lists through; for "first contact" or "first vehicle", use index 0 on the deal data structure. Resolve image sources (`source` starting with `image:`) via the Image model; raise a clear error if the Image does not exist. Use `request.build_absolute_uri(image.file.url)` for image URLs when request is present; when request is None, use `settings.SITE_URL` + relative path (unset SITE_URL may cause wkhtmltopdf to fail on images).
- **Transforms (v1):** Use `apps.doctemplates.utils.apply_transform(value, transform_name)` for date transforms and others. Implemented: `date_day`, `date_month`, `date_year`, `date_month_day` (outputs "September 1" from ISO date), `count`, `number_to_word` (0–99), `plural_suffix` ("" if count==1 else "s"). Other transforms per DESIGN-DOCS.
- **Atomicity:** Use `with transaction.atomic():` around entire Generate/Regenerate flow. On exception, rollback and re-raise as `DocumentGenerationError` so the view can catch and display the message.
- **Service and views:** Views do not implement generation logic; they call `generate_documents_for_deal` or `regenerate_documents` and handle return (success) or caught `DocumentGenerationError` (set messages and re-render).
- **Logging:** Log each step (template lookup, context build, render, PDF conversion, file save) with deal id, template ref_id. On error, log exception with context.
- **Serving PDFs (Batch 4):** Use `FileResponse(version.file.open("rb"), content_type="application/pdf", ...)` with `as_attachment=False` for inline view and `as_attachment=True` (and filename) for download. Return 404 if the version has no file. All document views (version view/download, instance detail) use `@login_required`.

---

## 12. Implementation Decisions

The following are fixed for this plan so that implementation is consistent.

| # | Topic | Decision |
|---|-------|----------|
| 1 | **Deal detail** | Deal detail page (View primary from list, Edit/Delete on detail) is implemented in PLAN-ADD-DEALS. This plan adds the Documents section to that page. See Section 3. |
| 2 | **Image URLs for PDF** | Pass `request` to generation; build image URLs with `request.build_absolute_uri(image.file.url)` when request is present so wkhtmltopdf can load them. When request is None, use `SITE_URL` + relative path (e.g. management command). Do **not** pass `--base-url` to wkhtmltopdf; many builds (0.12.6) do not support it. See Section 6 and Implementation Notes. |
| 3 | **Transforms** | Use `apps.doctemplates.utils.apply_transform()`. Supported: date_day, date_month, date_year, date_month_day, count, number_to_word, plural_suffix. See Implementation Notes. |
| 4 | **First contact / first vehicle** | Resolve from `get_deal_data(deal)` output at index 0; ordering is by id per DESIGN-DATA-INTERFACE. |
| 5 | **No Document Set Template** | If the deal's Deal Type has no Document Set Template, disable Generate and show "No document set template configured for this deal type." See Section 4. |
| 6 | **Image resolution** | Mapping entries with source `image:<uuid>` are resolved via the Image model; context value is the image file URL (absolute when building for PDF). See Section 6 and DESIGN-DOCS "Image references in dynamic templates." |
| 7 | **Context builder location** | Implement `build_document_context` in `apps.documents` (e.g. `services.py`). Used only at generation time. |
| 8 | **Missing Image at generation** | If an Image referenced by mapping no longer exists, raise a clear error; do not substitute empty string. |
| 9 | **Generation without request** | When `request` is None, use `SITE_URL` + relative path for image URLs. If SITE_URL is unset, image loading in wkhtmltopdf may fail—document as a limitation. |
| 10 | **Service contract** | Generation is implemented in a service layer (Section 5). Entry points: `generate_documents_for_deal(deal, request=None)` and `regenerate_documents(document_set, request=None)` return the DocumentSet on success; on failure they raise `DocumentGenerationError` with a user-facing message. Dynamic path: `render_dynamic_template_to_pdf(deal, dynamic_template, request=None)` returns PDF `bytes`; orchestrator creates instance/version and saves. Views call the service and handle success or caught exception. |

---

*End of plan. Proceed to implementation only after review.*

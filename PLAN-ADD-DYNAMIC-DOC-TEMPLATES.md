# Plan: Add Dynamic Document Templates

This document outlines how to add **Dynamic Document Templates** to the Django lease application. Dynamic templates are HTML files with Django Template Language (DTL) that produce populated documents when combined with deal data. Users upload HTML, configure text tagging (signature/date fields for SIGNiX), and configure the mapping of template variables to deal data.

**Design reference:** DESIGN-DOCS.md — Dynamic Document Templates and Template-to-Data Mapping sections. DESIGN-DATA-INTERFACE.md — schema, `get_paths()`, `get_deal_data(deal)`, and no-circumvention requirement.

**Prerequisites:** PLAN-ADD-STATIC-DOC-TEMPLATES.md must be implemented (apps.doctemplates exists). PLAN-MASTER plans 1–6 are implemented, including **PLAN-DATA-INTERFACE.md** (apps.schema provides `get_schema()`, `get_paths()`, `get_deal_data(deal)`). The mapping UI uses `get_paths()` and the context builder uses `get_deal_data(deal)`—no ad-hoc model introspection.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** `DynamicDocumentTemplate` with `ref_id`, `description`, `file` (HTML), `tagging_data` (text tagging for SIGNiX), and `mapping` (template variables → deal data).
- **Data:** No seed data; list starts empty.
- **UI:** List, Add, Edit, Delete — same pattern as Static templates. Add: upload HTML, ref_id, description, text tagging config. Edit: same, plus **mapping** configuration (requires file to be present so DTL can be parsed).
- **Access:** Authenticated users only (`@login_required`).

---

## 2. Model and Storage

- **App:** Add to existing `apps.doctemplates`.
- **Persistence:** HTML files under `MEDIA_ROOT/document_templates/dynamic/`.
- **Model:** `DynamicDocumentTemplate`
  - `ref_id` — `CharField`, unique, max_length=100. Must be unique across both Static and Dynamic templates (enforce in form clean by checking StaticDocumentTemplate and DynamicDocumentTemplate).
  - `description` — `CharField` or `TextField`
  - `file` — `FileField`, `upload_to="document_templates/dynamic"`. Accept HTML; validate extension (`.html`, `.htm`) or content-type in form.
  - `tagging_type` — `CharField`, default `"text_tagging"`, max_length=50
  - `tagging_data` — `JSONField`, default=list. Array of text-tagging field definitions (see Section 4).
  - `mapping` — `JSONField`, default=dict. Maps template variable names to `{source, transform?, ...}` per DESIGN-DOCS.

**Conventions:** Docstrings, `__str__`, `Meta` verbose names.

---

## 3. No Seed Data

List starts empty. Users add templates via the UI.

---

## 4. Text Tagging (tagging_data)

Structure per DESIGN-DOCS:

```json
[
  {
    "tag_name": "LesseeDate",
    "field_type": "date_signed",
    "is_required": "yes",
    "anchor_text": "Date:",
    "bounding_box": {"x_offset": 30, "y_offset": 0, "width": 90, "height": 12}
  },
  {
    "tag_name": "Lessee",
    "field_type": "signature",
    "is_required": "yes",
    "anchor_text": "LESSEE:",
    "bounding_box": {"x_offset": 45, "y_offset": 6, "width": 120, "height": 24},
    "member_info_number": 2,
    "date_signed_field_name": "LesseeDate",
    "date_signed_format": "MM/dd/yy"
  }
]
```

- `field_type`: `"signature"` or `"date_signed"`
- For `signature`: include `member_info_number`, `date_signed_field_name`, `date_signed_format`
- `bounding_box`: `x_offset`, `y_offset`, `width`, `height` (integers)

---

## 5. Mapping (mapping field)

Structure per DESIGN-DOCS (refinable in implementation):

```json
{
  "data.payment_amount": {"source": "deal.payment_amount"},
  "data.entered_day": {"source": "deal.date_entered", "transform": "date_day"},
  "data.jet_pack_list": {"source": "deal.vehicles", "item_map": {"sku": "sku", "year": "year", "jpin": "jpin"}}
}
```

Transforms: `date_day`, `date_month`, `date_year`, `concat`, `count`, `number_to_word`, `plural_suffix`. See DESIGN-DOCS for full list and schema.

---

## 6. Pages and Behavior

### 6.1 List page

- **URL:** `/document-templates/dynamic/` (name `dynamic_doctemplate_list`).
- **Content:** Table with Ref ID, Description, File, Actions (Edit, Delete).
- **Header:** "Dynamic Document Templates"; button "Add dynamic template" → add URL.
- **Empty state:** "No dynamic templates yet. Add one to get started."
- **Layout:** Use `base.html`. Add separate "Dynamic Templates" sidebar link. Sidebar order: Static Templates, Dynamic Templates, Images (insert both template links before Images).

### 6.2 Add template

- **URL:** `/document-templates/dynamic/add/`
- **Form:** ref_id, description, file (HTML, required), text tagging formset, mapping section.
- **"Identify Fields" button:** Enabled when a file is selected. On click, uses fetch/AJAX to POST the file to the parse endpoint (e.g. `/document-templates/dynamic/parse/`); no page reload (file stays in form input). Endpoint returns JSON with parsed variables. JavaScript displays the mapping section and parsed variables so the user can configure mapping before submitting.
- **On submit:** Create template with metadata, tagging_data, and mapping. All parsed variables must be mapped; form validation enforces this. Redirect to list.

### 6.3 Edit template

- **URL:** `/document-templates/dynamic/<id>/edit/`
- **Form:** ref_id, description, file (optional; show current filename), text tagging formset, **mapping section** (only shown when template has a file). Mapping section: parse template file, display extracted variables, provide UI to map each to data source + optional transform. Save mapping to `mapping` field.
- **On submit:** Update template; if new file, replace; update tagging_data and mapping. All parsed variables must be mapped; form validation enforces this.

### 6.4 Delete template

- POST required. Dedicated confirmation page; on POST, delete record and file.

---

## 7. Implementation Order (Checklist)

### Batch 1 — Model and migrations (steps 1–2)

1. **DynamicDocumentTemplate model**
   - In `apps/doctemplates/models.py`, add `DynamicDocumentTemplate` with ref_id, description, file, tagging_type, tagging_data, mapping.
   - Run `makemigrations` and `migrate`.

2. **URL routing**
   - In `apps/doctemplates/urls.py`, add `path("dynamic/", ...)` with a minimal list view placeholder.
   - Ensure `path("dynamic/add/", ...)`, `path("dynamic/<int:pk>/edit/", ...)`, `path("dynamic/<int:pk>/delete/", ...)` are stubbed or return 404 until Batch 2.

Batch 1 complete when the model exists, migrations apply, and `/document-templates/dynamic/` loads.

### Batch 2 — CRUD and text tagging (steps 3–8)

3. **Metadata form**
   - `DynamicDocumentTemplateForm`: ref_id, description, file. Validate file is HTML. File required on add, optional on edit. In `clean_ref_id`, ensure ref_id does not exist in `StaticDocumentTemplate` (uniqueness across both template types).

4. **Text tagging formset**
   - `DynamicTaggingFieldForm` with: tag_name, field_type (signature, date_signed), is_required, anchor_text, x_offset, y_offset, width, height, member_info_number (for signature), date_signed_field_name (for signature), date_signed_format (for signature).
   - Formset; conversion helpers `tagging_data_to_formset_initial` / `formset_cleaned_to_tagging_data`.

5. **Views**
   - List, add, edit, delete (add/edit include metadata + text tagging formset).

6. **Templates**
   - List, form (add/edit), confirm delete. Form includes metadata fields and formset for tagging.

7. **Sidebar**
   - Add "Dynamic Templates" link → `doctemplates:dynamic_doctemplate_list`, active when on dynamic templates. Insert after Static Templates, before Images. Order: Static Templates, Dynamic Templates, Images.

8. **File cleanup**
   - On delete and on file replace, remove old file from disk.

Batch 2 complete when full CRUD works with metadata and text tagging.

### Batch 3 — DTL parsing (steps 10–11)

10. **DTL parsing utility**
   - Create `apps/doctemplates/utils.py` (or similar) with `parse_dtl_variables(html_string)` that returns a list of variable paths (e.g. `["data.payment_amount", "data.jet_pack_list", "item.sku"]`). Walk Django's `Template(html_string).nodelist` to collect variable references and loop iterables. Handle single-level `{% for item in list %}`.
   - Unit test or shell verification.

11. **Expose parsed variables on edit**
    - In the edit view, when template has a file: read file content, call parser, pass `parsed_variables` to template context. Display "Template expects: ..." in the mapping section (even if mapping UI is minimal in Batch 3).

12. **Parse endpoint (for "Identify Fields" on add)**
    - Add view `dynamic_doctemplate_parse` (e.g. POST `/document-templates/dynamic/parse/`) that accepts a file in the request, reads content, calls `parse_dtl_variables`, returns `JsonResponse({"variables": [...]})`. `@login_required`.

Batch 3 complete when parsing works, parse endpoint returns JSON, and edit page shows parsed variables.

### Batch 4 — Mapping UI (steps 13–16)

13. **Data paths for mapping UI**
    - Use `apps.schema.services.get_paths()` for available data paths. Import from `apps.schema.services`; do not implement separate model introspection. Paths include `deal.payment_amount`, `deal.date_entered`, `deal.lease_start_date`, `deal.lease_officer`, `deal.vehicles`, `deal.contacts`, `deal.vehicles.item.sku`, etc. Per DESIGN-DATA-INTERFACE and no-circumvention requirement.

14. **Mapping form**
    - Layout: **Table** — one row per variable, columns: Variable (read-only), Source (dropdown), Transform (dropdown). For list variables with `item.*` (e.g. `data.jet_pack_list` + `item.sku`, `item.year`), support `item_map`: one row per parsed `item.*` variable, each maps to a Vehicle field dropdown. Store as JSON per DESIGN-DOCS schema.

15. **Save mapping**
    - On add/edit POST, parse mapping form data, validate. **All parsed variables must be mapped.** Save to `instance.mapping`.

16. **Mapping section on add and edit**
    - On edit: show parsed variables and mapping form (table layout). If no file, hide mapping section or show "Upload a template file to configure mapping."
    - On add: "Identify Fields" button (enabled when file selected) uses fetch to call parse endpoint; no page reload. JavaScript displays mapping section with parsed variables; user configures mapping before submit.

Batch 4 complete when mapping can be configured on both add and edit, and "Identify Fields" works on add.

---

## 7a. Implementation Batches and Verification

### Batch 1 — Model and migrations

**How to test after Batch 1:**

1. `python manage.py check` — no issues.
2. `python manage.py migrate` — `doctemplates_dynamicdocumenttemplate` table exists.
3. **Shell:**
   ```python
   from django.core.files.uploadedfile import SimpleUploadedFile
   from apps.doctemplates.models import DynamicDocumentTemplate

   html = SimpleUploadedFile("t.html", b"<html>{{ data.x }}</html>", content_type="text/html")
   t = DynamicDocumentTemplate(ref_id="D1", description="Test", file=html, tagging_data=[], mapping={})
   t.save()
   assert DynamicDocumentTemplate.objects.count() == 1
   assert t.tagging_data == []
   assert t.mapping == {}
   ```
4. Visit `/document-templates/dynamic/` — no 404.

### Batch 2 — CRUD and text tagging

**How to test after Batch 2:**

1. **List:** Navigate to Dynamic Templates; empty list, "Add dynamic template" button.
2. **Add:** Add template with ref_id, description, HTML file, and one text tagging field (e.g. date_signed, anchor_text "Date:", bounding box 30,0,90,12). Save. List shows new row.
3. **Edit:** Edit; add a second tagging field (signature with member_info_number 2, date_signed_field_name, etc.). Save. Changes persist.
4. **Delete:** Delete via confirmation page; template removed.
5. **File validation:** Attempt add with non-HTML file (e.g. .txt); expect form error.
6. **Sidebar:** "Dynamic Templates" appears and is active when on dynamic templates.

### Batch 3 — DTL parsing

**How to test after Batch 3:**

1. **Shell:**
   ```python
   from apps.doctemplates.utils import parse_dtl_variables

   html = "<html>{{ data.payment_amount }}</html>"
   vars = parse_dtl_variables(html)
   assert "data.payment_amount" in vars

   html2 = "{% for item in data.jet_pack_list %}{{ item.sku }}{% endfor %}"
   vars2 = parse_dtl_variables(html2)
   assert "data.jet_pack_list" in vars2
   assert "item.sku" in vars2
   ```
2. **Edit page:** Edit a template with an HTML file; mapping section shows "Template expects: ..." with parsed variables.
3. **Parse endpoint:** POST a file to the parse endpoint (e.g. with curl or browser dev tools); response is JSON with `{"variables": [...]}`.

### Batch 4 — Mapping UI

**How to test after Batch 4:**

1. **Edit page:** With template that has file and parsed variables, configure mapping for at least one variable (e.g. data.payment_amount → deal.payment_amount). Save.
2. **Shell:** Reload template; `instance.mapping` contains the saved mapping.
3. **Data paths:** Verify dropdown or list of data paths (from `get_paths()`) includes deal fields (e.g. deal.payment_amount, deal.vehicles).
4. **Transform:** Map a date field with date_day transform; save and verify mapping JSON structure.
5. **Add page — Identify Fields:** On Add, select an HTML file, click "Identify Fields" (fetch, no page reload); parsed variables appear; configure mapping (all required); submit. Template is created with mapping saved.
6. **ref_id uniqueness:** Create a Static template with ref_id "X". Attempt to create a Dynamic template with ref_id "X"; expect validation error. (And vice versa.)

---

## 8. File and URL Summary

| Item   | Value |
|--------|-------|
| App    | `apps.doctemplates` |
| Model  | `DynamicDocumentTemplate(ref_id, description, file, tagging_type, tagging_data, mapping)` |
| List   | `/document-templates/dynamic/` |
| Add    | `/document-templates/dynamic/add/` |
| Edit   | `/document-templates/dynamic/<id>/edit/` |
| Delete | GET confirm, POST delete at `/document-templates/dynamic/<id>/delete/` |
| Nav    | Sidebar: "Dynamic Templates" → list |
| Storage| `MEDIA_ROOT/document_templates/dynamic/` |

---

## 9. Out of Scope (This Phase)

- Actual rendering of templates with deal data (document generation — separate plan).
- HTML-to-PDF conversion (document generation plan).
- Nested loops, `{% include %}`, custom template tags in DTL parsing.
- PDF form field auto-detection (static templates only).

---

## 10. Implementation Notes

- **ref_id uniqueness:** Enforce uniqueness across both Static and Dynamic templates. In `DynamicDocumentTemplateForm.clean_ref_id` (and in `StaticDocumentTemplateForm.clean_ref_id` in the Static plan), check that the ref_id does not exist in the other template model.
- **Mapping UI layout:** Table — one row per variable; columns: Variable, Source, Transform. For list variables, one row per parsed `item.*` variable; each maps to a Vehicle field dropdown (item_map).
- **List variable item_map:** Supported in v1. Simple UI: one row per parsed `item.*` variable; user selects which Vehicle field each maps to.
- **Data interface dependency:** Use `apps.schema.services.get_paths()` for mapping source options. Do not introspect models directly. PLAN-DATA-INTERFACE ensures apps.schema is in INSTALLED_APPS and provides paths conforming to the schema (e.g. `deal.lease_start_date`).

---

*End of plan. Proceed to implementation only after review.*

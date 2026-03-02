# Plan: Add Dynamic Document Templates

This document outlines how to add **Dynamic Document Templates** to the Django lease application. Dynamic templates are HTML files with Django Template Language (DTL) that produce populated documents when combined with deal data and Images. Users upload HTML, configure text tagging (signature/date fields for SIGNiX), and configure the mapping of template variables to deal data or Images.

**Design reference:** DESIGN-DOCS.md — Dynamic Document Templates and Template-to-Data Mapping sections. DESIGN-DATA-INTERFACE.md — schema, `get_paths_grouped_for_mapping()`, `get_deal_data(deal)`, and no-circumvention requirement.

**Prerequisites:** PLAN-ADD-STATIC-DOC-TEMPLATES.md must be implemented (apps.doctemplates exists). PLAN-MASTER plans 1–6 are implemented, including **PLAN-ADD-IMAGES** (Image model for image mapping) and **PLAN-DATA-INTERFACE** (apps.schema: `get_paths_grouped_for_mapping()`, `get_deal_data(deal)`). The mapping UI uses schema paths plus an Images optgroup; the context builder uses `get_deal_data(deal)` for deal data and resolves `image:<uuid>` via the Image model.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** `DynamicDocumentTemplate` with `ref_id`, `description`, `file` (HTML), `tagging_data` (text tagging for SIGNiX), and `mapping` (template variables → deal data or Images).
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
  "data": {"source": "deal", "var_type": "data_source"},
  "data.payment_amount": {"source": "deal.payment_amount", "var_type": "scalar"},
  "lease_image_url": {"source": "image:50f77aee-ae17-469b-b869-6178012ecbf9", "var_type": "image"},
  "data.entered_day": {"source": "deal.date_entered", "transform": "date_day", "var_type": "scalar"},
  "data.lease_start_day_month": {"source": "deal.lease_start_date", "transform": "date_month_day", "var_type": "scalar"},
  "data.lease_end_day_month": {"source": "deal.lease_end_date", "transform": "date_month_day", "var_type": "scalar"},
  "data.lessee_name": {"source": "deal.contacts.item.full_name", "var_type": "scalar"},
  "data.jet_pack_list": {"source": "deal.vehicles", "var_type": "list"},
  "data.number_of_items_number": {"source": "deal.vehicles_count", "var_type": "scalar"},
  "data.number_of_items_text": {"source": "deal.vehicles_count", "transform": "number_to_word", "var_type": "scalar"},
  "data.number_of_items_inflection": {"source": "deal.vehicles_count", "transform": "plural_suffix", "var_type": "scalar"},
  "item.sku": {"source": "deal.vehicles.item.sku", "var_type": "list_item"}
}
```

Each mapping entry includes `var_type` (`data_source`, `list`, `list_item`, `image`, `scalar`) for context builder and future use. Parsing infers roots (e.g. `data`) from dotted variable prefixes; list-item variables are those referenced inside a `{% for %}` loop; image variables are detected by naming convention (`_image_url`, `_image`, `_logo_url`, `_logo`); scalars are the remainder.

Transforms: `date_day`, `date_month`, `date_year`, `date_month_day`, `count`, `number_to_word`, `plural_suffix`. See DESIGN-DOCS for full list and schema.

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
- **When Document Set Templates exist (PLAN-ADD-DOC-SET-TEMPLATES):** If this Dynamic template is referenced by any Document Set Template, POST does not delete; re-render the confirmation page with an error (e.g. "This template cannot be deleted because it is used in a Document Set Template.").

---

## 7. Implementation Order (Checklist)

### Batch 1 — Model and migrations (steps 1–2)

1. **DynamicDocumentTemplate model**
   - In `apps/doctemplates/models.py`, add `DynamicDocumentTemplate` with ref_id, description, file, tagging_type, tagging_data, mapping.
   - Run `makemigrations` and `migrate`.

2. **URL routing**
   - In `apps/doctemplates/urls.py`, add `path("dynamic/", ...)` with a minimal list view placeholder.
   - Ensure `path("dynamic/add/", ...)`, `path("dynamic/<int:pk>/edit/", ...)`, `path("dynamic/<int:pk>/delete/", ...)` are stubbed or return 404 until Batch 2.

**Critical:** Run `makemigrations doctemplates` and `migrate`—otherwise `OperationalError: no such table` when the list view is implemented in Batch 2.

Batch 1 complete when the model exists, migrations apply, and `/document-templates/dynamic/` loads.

### Batch 2 — CRUD and text tagging (steps 3–8)

3. **Metadata form**
   - `DynamicDocumentTemplateForm`: ref_id, description, file. Validate file is HTML. File required on add, optional on edit. In `clean_ref_id`, ensure ref_id does not exist in `StaticDocumentTemplate` (uniqueness across both template types).

4. **Text tagging formset**
   - `DynamicTaggingFieldForm` with: tag_name, field_type (signature, date_signed), is_required, anchor_text, x_offset, y_offset, width, height, member_info_number (for signature), date_signed_field_name (for signature), date_signed_format (for signature).
   - Formset with **prefix** (e.g. `"dynamic_tagging"`) to avoid collision with metadata form fields.
   - Conversion helpers: `dynamic_tagging_data_to_formset_initial` / `dynamic_formset_cleaned_to_tagging_data`.

5. **Views**
   - List, add, edit, delete (add/edit include metadata + text tagging formset).
   - Edit: if no new file uploaded, preserve existing file (set `instance.file = template_obj.file` before save).

6. **Templates**
   - List, form (add/edit), confirm delete. Form includes metadata fields, formset for tagging, and mapping section placeholder (Batch 3 adds parsed variables; Batch 4 adds mapping form).

7. **Sidebar**
   - Add "Dynamic Templates" link → `doctemplates:dynamic_doctemplate_list`, active when on dynamic templates. Insert after Static Templates, before Images. Order: Static Templates, Dynamic Templates, Images.

8. **File cleanup**
   - On delete and on file replace, remove old file from disk.

Batch 2 complete when full CRUD works with metadata and text tagging.

### Batch 3 — DTL parsing (steps 10–11)

10. **DTL parsing utility**
   - Create `apps/doctemplates/utils.py` with `parse_dtl_variables(html_string)` that returns variable paths. Provide `parse_dtl_variables_with_metadata(html_string)` returning `(variables, list_variables, list_item_variables, data_source_variables, list_item_to_list, image_variables)`:
     - `variables`: all paths plus inferred data-source roots (e.g. `data`) prepended
     - `list_variables`: paths found as `ForNode` sequence (e.g. `data.jet_pack_list`)
     - `list_item_variables`: paths like `item.sku` found inside a for loop referencing the loop var
     - `data_source_variables`: inferred root names (e.g. `data`) from dotted variable prefixes, excluding loop var names
     - `list_item_to_list`: dict mapping list_item_var → list_var (e.g. `{"item.sku": "data.jet_pack_list"}`) so the UI can show which list each item belongs to
     - `image_variables`: frozenset of variable names matching `_image_url`, `_image`, `_logo_url`, or `_logo` (case-insensitive) for image variable detection
   - Walk `Template(html_string).nodelist`: for `VariableNode`, collect path; for `ForNode`, add `sequence.var`, track loop vars, recurse into `nodelist_loop` recording list_item_to_list; for other nodes, recurse `child_nodelists`. Filters stripped. After collection, detect image variables by suffix.
   - Provide `get_image_sources_for_mapping()` returning `[(f"image:{img.uuid}", img.name), ...]` from Image model for the Images optgroup.
   - Raises `TemplateSyntaxError` on invalid DTL. Returns empty list/frozensets/dict if html_string is empty/None.
   - Unit test or shell verification.

11. **Expose parsed variables on edit**
    - In the edit view, when template has a file: read file content, call `parse_dtl_variables_with_metadata`, pass `parsed_variables`, metadata (including `image_variables`), and `template_structure` (structured summary) to template context. On file read error or empty content, pass empty collections.
    - Mapping section displays **Template structure** when `parsed_variables` is non-empty: Primary data source, Lists (each with its items), Scalar properties, Image variables. Then the mapping table with variables annotated by type (data source, list, list item, image, scalar); for list items, show the parent list name (e.g. `item.sku (data.jet_pack_list)`). Exclude image variables from scalar properties. Fallbacks: if parse returned empty but file exists, show "Could not parse template variables"; if no file, "Upload a template file"; on add, "After adding, use Edit to see parsed variables."
    - Add view always passes `parsed_variables=[]` (Batch 4 adds "Identify Fields" for add).

12. **Parse endpoint (for "Identify Fields" on add)**
    - Add view `dynamic_doctemplate_parse` at POST `/document-templates/dynamic/parse/`. Accepts file, calls `parse_dtl_variables_with_metadata`, returns `JsonResponse` with `variables`, `list_variables`, `list_item_variables`, `data_source_variables`, `list_item_to_list` (dict mapping list item to list), and `image_variables` (list of image variable names). JavaScript builds the structured Template structure summary (including Image variables) and mapping table with type badges (data source, list, list item, image, scalar). `@login_required`.
    - URL: `path("dynamic/parse/", views.dynamic_doctemplate_parse)` — place before `dynamic/<int:pk>/` routes so "parse" is not matched as pk.
    - Error responses: 405 if not POST; 400 if no file; 400 with `{"error": "Template syntax error: ..."}` on `TemplateSyntaxError`.

Batch 3 complete when parsing works, parse endpoint returns JSON, and edit page shows "Template expects: ..." with parsed variables in the mapping section. Add page shows mapping section with "After adding the template, use Edit to see parsed variables."

### Batch 4 — Mapping UI (steps 13–16)

13. **Data paths for mapping UI**
    - Use `apps.schema.services.get_paths_grouped_for_mapping()` for the Source dropdown, then append an **Images** optgroup from `get_image_sources_for_mapping()` (doctemplates utils), which returns `[(f"image:{img.uuid}", img.name), ...]` from the Image model. The combined list yields optgroups: **Data Source** (root paths like `deal`), **List sources**, **Scalar / item paths**, and **Images**. Import schema paths from `apps.schema.services`; do not introspect models for deal paths. Per DESIGN-DATA-INTERFACE and no-circumvention requirement.

14. **Mapping form**
    - Above the table: **Template structure** summary — Primary data source, Lists (each with items), Scalar properties, Image variables. Then the mapping table.
    - Table layout: one row per variable; columns Variable (read-only, with type badge), Source, Transform. For list items, the Variable column shows the parent list (e.g. `item.sku (data.jet_pack_list)`). Badges: "data source", "list", "list item", "image", "scalar" (scalars may have no badge). Image variables map to the Images optgroup; transform is typically not used for images. Store as JSON per DESIGN-DOCS schema.

15. **Save mapping**
    - On add/edit POST, parse mapping form data, validate. **All parsed variables must be mapped.** Augment each entry with `var_type` (data_source, list, list_item, image, scalar) from parsing metadata via `augment_mapping_with_var_type()` before saving. Save to `instance.mapping`.

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
   from apps.doctemplates.utils import parse_dtl_variables, parse_dtl_variables_with_metadata

   html = "<html>{{ data.payment_amount }}</html>"
   vars = parse_dtl_variables(html)
   assert "data.payment_amount" in vars

   html2 = "{% for item in data.jet_pack_list %}{{ item.sku }}{% endfor %}"
   vars2, list2, list_item2, data_src2, item_to_list2, image_vars2 = parse_dtl_variables_with_metadata(html2)
   assert "data" in vars2  # inferred root
   assert "data.jet_pack_list" in vars2
   assert "item.sku" in vars2
   assert "data.jet_pack_list" in list2
   assert "item.sku" in list_item2
   assert "data" in data_src2
   assert item_to_list2.get("item.sku") == "data.jet_pack_list"
   ```
2. **Edit page:** Edit a template with an HTML file; mapping section shows Template structure (Primary data source, Lists with items, Scalar properties) and mapping table with badges; list items show parent list (e.g. `item.sku (data.jet_pack_list)`).
3. **Parse endpoint:** POST a file; response is JSON with `variables`, `list_variables`, `list_item_variables`, `data_source_variables`, `list_item_to_list`, `image_variables`.

### Batch 4 — Mapping UI

**How to test after Batch 4:**

1. **Edit page:** With template that has file and parsed variables, configure mapping (including data source root e.g. `data` → `deal` when applicable). Save.
2. **Shell:** Reload template; `instance.mapping` contains entries with `source`, optional `transform`, and `var_type` (data_source, list, list_item, image, scalar).
3. **Data paths:** Verify Source dropdown uses grouped paths (Data Source: deal; List sources: deal.vehicles, deal.contacts; Scalar / item paths: deal.payment_amount, etc.) and an Images optgroup when images exist.
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
| Parse  | POST `/document-templates/dynamic/parse/` — accepts file, returns `variables`, `list_variables`, `list_item_variables`, `data_source_variables`, `list_item_to_list`, `image_variables` |
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

- **ref_id uniqueness:** Enforce uniqueness across both Static and Dynamic templates. Both `DynamicDocumentTemplateForm.clean_ref_id` and `StaticDocumentTemplateForm.clean_ref_id` (PLAN-ADD-STATIC-DOC-TEMPLATES) must check both models. Use shared helpers (e.g. `_ref_id_exists_in_static`, `_ref_id_exists_in_dynamic`) to avoid duplication.
- **Mapping UI layout:** Above table, show Template structure (Primary data source, Lists with items, Scalar properties, Image variables). Table: one row per variable; Variable column shows name and for list items the parent list (e.g. `item.sku (data.jet_pack_list)`); type badges (data source, list, list item, image, scalar). Use `augment_mapping_with_var_type()` with `image_variables` before save. Use `_build_template_structure_summary()` and `_build_mapping_rows()` with `image_variables`; combine `get_paths_grouped_for_mapping()` with `get_image_sources_for_mapping()` for the Source dropdown optgroups.
- **Data interface dependency:** Use `apps.schema.services.get_paths_grouped_for_mapping()` for the Source dropdown. This provides paths in optgroups (Data Source, List sources, Scalar / item paths) for clearer mapping UI. Do not introspect models directly. PLAN-DATA-INTERFACE ensures apps.schema is in INSTALLED_APPS and provides paths conforming to the schema (e.g. `deal.lease_start_date`).

- **Migrations:** Batch 1 requires `makemigrations doctemplates` and `migrate`. Without migrations, the list view will raise `OperationalError: no such table`.

- **HTML file validation:** Accept `.html`, `.htm` or content-type `text/html`, `application/xhtml+xml`.

---

*End of plan. Proceed to implementation only after review.*

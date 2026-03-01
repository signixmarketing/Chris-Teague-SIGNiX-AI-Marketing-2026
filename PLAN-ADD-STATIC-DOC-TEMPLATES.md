# Plan: Add Static Document Templates

This document outlines how to add **Static Document Templates** to the Django lease application. Static templates are reusable PDFs with form fields (e.g., safety advisory, disclosures) that become "required documents" in a document set. Users upload a PDF and configure metadata (ref_id, description) and form field definitions (tagging_data) for SIGNiX.

**Design reference:** DESIGN-DOCS.md — Static Document Templates section.

**Prerequisites:** PLAN-MASTER plans 1–6 are implemented (Baseline, Vehicles, Contacts, Deals, Images, Data Interface). MEDIA_ROOT/MEDIA_URL are configured from Images. Same UI patterns (list, add, edit, delete with confirmation) are in use.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** `StaticDocumentTemplate` with `ref_id`, `description`, `file` (PDF), and `tagging_data` (JSONField) for form field definitions.
- **Data:** No seed data; the list starts empty. Users add templates via the UI.
- **UI:** List, Add, Edit, Delete — same pattern as Deals, Vehicles, Contacts, and Images. Add: upload PDF, enter ref_id and description, configure form fields (tag_name, field_type, member_info_number; for signature: date_signed_field_name, date_signed_format). Edit: same, with optional PDF replacement.
- **Access:** Authenticated users only (`@login_required`).

---

## 2. Model and Storage

- **App:** New app `apps.doctemplates` (or `apps.static_doctemplates`). Use `apps.doctemplates` so Dynamic templates can be added to the same app later.
- **Persistence:** Metadata in SQLite; PDF files under `MEDIA_ROOT/document_templates/static/`.
- **Model:** `StaticDocumentTemplate`
  - `ref_id` — `CharField`, unique, max_length=100. Identifier for the template (e.g., "ZoomJetPackSafetyAdvisory"). Must be unique across both Static and Dynamic templates (enforce in form `clean_ref_id` by checking `DynamicDocumentTemplate`).
  - `description` — `CharField` or `TextField`, human-readable (e.g., "Zoom Jet Pack Safety Advisory").
  - `file` — `FileField`, `upload_to="document_templates/static"`. Accept PDFs only; validate in form.
  - `tagging_type` — `CharField`, default `"pdf_fields"`, max_length=50. Indicates PDF form fields.
  - `tagging_data` — `JSONField`, default=list. Array of form-field definitions. Each item:
    - `tag_name` (str) — PDF form field name
    - `field_type` (str) — `"signature"`, `"date"`, or `"text"`
    - `member_info_number` (int) — 1 = user/lease officer, 2 = contact
    - `date_signed_field_name` (str, optional) — for signature fields: PDF field name for date
    - `date_signed_format` (str, optional) — for signature fields: e.g. `"MM/dd/yy"`

**Conventions:** Docstrings, `__str__` (return `description` or `ref_id`), `verbose_name` / `verbose_name_plural` in `Meta`. MEDIA_ROOT/MEDIA_URL are already configured (from Images); ensure PDFs are served via the same media URL pattern.

---

## 3. No Seed Data

The list starts empty. No management command or fixture. Users add templates via the UI.

---

## 4. Pages and Behavior

### 4.1 List page

- **URL:** `/document-templates/static/` (name `static_doctemplate_list`).
- **Content:** Table with columns **Ref ID**, **Description**, **File** (filename or link), **Actions** (Edit, Delete).
- **Header:** Title "Static Document Templates"; button **Add static template** → `/document-templates/static/add/`.
- **Empty state:** "No static templates yet. Add one to get started." Single Add button in header only.
- **Layout:** Use `base.html`. Add sidebar link "Static Templates" → list. Sidebar order: Static Templates, Dynamic Templates, Images (insert Static and Dynamic before Images).

### 4.2 Add template

- **URL:** `/document-templates/static/add/` (name `static_doctemplate_add`).
- **Form:**
  - **ref_id** (text, required)
  - **description** (text, required)
  - **file** (file upload, required, PDF only)
  - **Form field configuration** — One or more rows. Each row: tag_name, field_type (dropdown: signature, date, text), member_info_number (dropdown: "User (lease officer)" / "Contact" mapping to 1/2). When field_type = signature: also date_signed_field_name and date_signed_format. Use an inline formset or dynamic "Add field" blocks.
- **Enctype:** `multipart/form-data`.
- **On submit:** Create template, save PDF, save tagging_data from form fields; redirect to list with "Static template added."

### 4.3 Edit template

- **URL:** `/document-templates/static/<id>/edit/` (name `static_doctemplate_edit`).
- **Form:** Same as add. File is optional on edit (leave blank to keep current). Show current PDF filename. Allow adding/removing form field rows. Pre-fill tagging_data into the formset/dynamic rows.
- **On submit:** Update template; if new file provided, replace PDF; update tagging_data; redirect to list with "Static template updated."

### 4.4 Delete template

- **POST required.** Dedicated confirmation page: GET shows "Are you sure you want to delete this template?" (show ref_id/description); POST deletes record and file; redirect to list with "Static template deleted."

---

## 5. Form Field Configuration UI

The `tagging_data` structure (per DESIGN-DOCS):

```json
[
  {
    "tag_name": "SignatureField",
    "field_type": "signature",
    "member_info_number": 2,
    "date_signed_field_name": "DateField",
    "date_signed_format": "MM/dd/yy"
  }
]
```

**Implementation options:**

1. **Django formset** — Create a `Form` with fields: tag_name, field_type, member_info_number, date_signed_field_name, date_signed_format. Use `formset_factory` (no model). On save: convert formset cleaned_data to list of dicts, assign to `tagging_data`. On edit: build formset from `instance.tagging_data`.
2. **Dynamic JavaScript** — A container with "Add field" button; each block has the fields. Submit as `tagging_data_0_tag_name`, etc., or as JSON in a hidden input. Parse on the backend.

**Recommendation:** Option 1 (formset) — standard Django, no custom JS required. Use `extra=3` to show three default empty rows (typical templates have 1–3 fields; users can add more if needed).

**Conditional fields:** Always show `date_signed_field_name` and `date_signed_format`; require them in form `clean()` only when `field_type` is `signature`. No JavaScript show/hide — simpler and works without JS.

**member_info_number labels:** Dropdown choices: `(1, "User (lease officer)")`, `(2, "Contact")` per DESIGN-DOCS Decisions Log.

---

## 6. Navigation and Integration

- **Sidebar:** Add "Static Templates" link (e.g., after Images, before Admin). Text "Static Templates", URL `{% url 'doctemplates:static_doctemplate_list' %}`, icon e.g. `bi bi-file-pdf`. Active when `request.resolver_match.app_name == 'doctemplates'` and URL name starts with `static_`.
- **Config:** `path("document-templates/", include("apps.doctemplates.urls"))`. Add `"apps.doctemplates"` to `INSTALLED_APPS`.
- **Jazzmin:** Optional custom link "Static Templates" → `/document-templates/static/`.

---

## 7. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–3)

1. **Create `apps.doctemplates` app**
   - Create `apps/doctemplates/` with `__init__.py`, `apps.py` (`name = "apps.doctemplates"`), `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `migrations/__init__.py`.
   - Add `"apps.doctemplates"` to `INSTALLED_APPS`.

2. **StaticDocumentTemplate model**
   - Define `StaticDocumentTemplate` with `ref_id` (unique), `description`, `file` (FileField, `upload_to="document_templates/static"`), `tagging_type` (default `"pdf_fields"`), `tagging_data` (JSONField, default=list).
   - Add `__str__` and `Meta` verbose names.
   - Run `python manage.py makemigrations doctemplates` and `python manage.py migrate`.

3. **URL routing**
   - In `apps/doctemplates/urls.py`: `app_name = "doctemplates"`; include `path("static/", ...)` with a minimal list view (e.g., `lambda: HttpResponse("Static templates")` or a simple template) so `/document-templates/static/` does not 404. Full list view will be replaced in Batch 3.
   - In `config/urls.py`: `path("document-templates/", include("apps.doctemplates.urls"))`.

Batch 1 complete when the app is installed, the model exists, migrations apply, and `/document-templates/static/` loads without error. No full CRUD UI yet.

### Batch 2 — Forms (steps 4–5)

4. **Template metadata form**
   - `StaticDocumentTemplateForm` (ModelForm): fields `ref_id`, `description`, `file`. File required on add, optional on edit. Validate file is PDF (extension `.pdf` or content-type). In `clean_ref_id`, ensure ref_id does not exist in `DynamicDocumentTemplate` (uniqueness across both template types). Note: If Static templates are implemented before Dynamic, the Dynamic check can be added when Dynamic templates are implemented.

5. **Form field formset**
   - `TaggingFieldForm` with: tag_name, field_type (ChoiceField: signature, date, text), member_info_number (ChoiceField: 1, 2 with labels "User (lease officer)", "Contact"), date_signed_field_name (optional), date_signed_format (optional).
   - Clean: when field_type is `signature`, require date_signed_field_name and date_signed_format.
   - `TaggingFieldFormSet = formset_factory(TaggingFieldForm, extra=3, min_num=0)` — three default empty rows; allow zero filled fields (empty list).
   - Helper: `tagging_data_to_formset_data(tagging_data)` and `formset_data_to_tagging_data(cleaned_data)` to convert between JSON and formset.

### Batch 3 — Views and templates (steps 6–9)

6. **Views**
   - `static_doctemplate_list` — List all `StaticDocumentTemplate`; pass to template.
   - `static_doctemplate_add` — GET: form + formset (empty or 1 empty row); POST: validate both; save model with file and tagging_data from formset; redirect to list.
   - `static_doctemplate_edit` — GET: form with instance, formset from `instance.tagging_data`; POST: update; if new file, replace.
   - `static_doctemplate_delete_confirm` — GET: confirmation page; POST: delete (and remove file from disk if desired).
   - All views: `@login_required`.

7. **URLs**
   - `""` → redirect or list at `static/`
   - `static/` → list
   - `static/add/` → add
   - `static/<int:pk>/edit/` → edit
   - `static/<int:pk>/delete/` → delete confirm
   - Names: `static_doctemplate_list`, `static_doctemplate_add`, `static_doctemplate_edit`, `static_doctemplate_delete_confirm`

8. **Templates**
   - `templates/doctemplates/static_doctemplate_list.html` — table (Ref ID, Description, File, Actions), Add button, empty state.
   - `templates/doctemplates/static_doctemplate_form.html` — used for add and edit. Form for ref_id, description, file. Formset for tagging fields (extra=3). Use `{{ formset.management_form }}`. Each formset form: tag_name, field_type, member_info_number, date_signed_field_name, date_signed_format — always show all fields; formset clean requires date_signed_* when field_type is signature. Include "Add another field" via formset extra or a small JS snippet to clone a row.
   - `templates/doctemplates/static_doctemplate_confirm_delete.html` — confirmation message, POST form (Cancel → list, Delete → submit).

9. **Sidebar**
   - Update `templates/base.html`: add "Static Templates" nav item → `doctemplates:static_doctemplate_list`, active when on static doctemplates. Insert before Images. Order: Static Templates, Dynamic Templates, Images.

10. **Optional**
    - Register `StaticDocumentTemplate` in admin.
    - Add Jazzmin custom link.

11. **Verification**
    - Full CRUD via UI; add template with one signature field; edit and add another field; delete. Confirm PDF is stored and served.

---

## 7a. Implementation Batches and Verification

Implement in **three batches**. After each batch, run the verification steps.

### Batch 1 — Data layer (steps 1–3)

**Includes:** Create `apps.doctemplates`, add to `INSTALLED_APPS`, define `StaticDocumentTemplate` model, run migrations, wire URLs.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrations:** `python manage.py migrate` — doctemplates migration applied; table exists.
3. **Shell:** Create a template with a minimal PDF file:
   ```python
   from django.core.files.uploadedfile import SimpleUploadedFile
   from apps.doctemplates.models import StaticDocumentTemplate

   pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4 minimal", content_type="application/pdf")
   t = StaticDocumentTemplate(
       ref_id="Test1",
       description="Test",
       file=pdf_file,
       tagging_data=[
           {"tag_name": "Sig1", "field_type": "signature", "member_info_number": 2,
            "date_signed_field_name": "Date1", "date_signed_format": "MM/dd/yy"}
       ]
   )
   t.save()
   assert StaticDocumentTemplate.objects.count() == 1
   assert t.tagging_data[0]["tag_name"] == "Sig1"
   ```
4. **URLs:** Visit `/document-templates/static/` — should not 404; minimal placeholder view is acceptable.

Batch 1 complete when the above pass.

### Batch 2 — Forms (steps 4–5)

**Includes:** StaticDocumentTemplateForm, TaggingFieldForm, formset, conversion helpers.

**How to test after Batch 2:**

1. **Shell — valid metadata form:**
   ```python
   from apps.doctemplates.forms import StaticDocumentTemplateForm
   from django.core.files.uploadedfile import SimpleUploadedFile

   pdf = SimpleUploadedFile("x.pdf", b"%PDF", content_type="application/pdf")
   form = StaticDocumentTemplateForm(data={"ref_id": "T1", "description": "Desc"}, files={"file": pdf})
   assert form.is_valid(), form.errors
   ```
2. **Shell — invalid metadata form (missing ref_id):**
   ```python
   form = StaticDocumentTemplateForm(data={"ref_id": "", "description": "Desc"})
   assert not form.is_valid()
   assert "ref_id" in form.errors
   ```
3. **Shell — invalid file type (non-PDF):**
   ```python
   txt = SimpleUploadedFile("x.txt", b"not a pdf", content_type="text/plain")
   form = StaticDocumentTemplateForm(data={"ref_id": "T1", "description": "Desc"}, files={"file": txt})
   assert not form.is_valid()
   assert "file" in form.errors
   ```
4. **Shell — formset from tagging_data, then convert back:**
   ```python
   from apps.doctemplates.forms import TaggingFieldFormSet, formset_data_to_tagging_data

   tagging_data = [{"tag_name": "Sig1", "field_type": "signature", "member_info_number": 2,
                    "date_signed_field_name": "Date1", "date_signed_format": "MM/dd/yy"}]
   formset_data = {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0", "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
                   "form-0-tag_name": "Sig1", "form-0-field_type": "signature", "form-0-member_info_number": "2",
                   "form-0-date_signed_field_name": "Date1", "form-0-date_signed_format": "MM/dd/yy"}
   formset = TaggingFieldFormSet(formset_data)
   assert formset.is_valid(), formset.errors
   result = formset_data_to_tagging_data(formset.cleaned_data)
   assert result[0]["tag_name"] == "Sig1"
   ```
5. **Shell — formset with signature but missing date_signed_field_name:**
   ```python
   invalid_data = {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0", "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
                   "form-0-tag_name": "Sig1", "form-0-field_type": "signature", "form-0-member_info_number": "2",
                   "form-0-date_signed_field_name": "", "form-0-date_signed_format": "MM/dd/yy"}
   formset = TaggingFieldFormSet(invalid_data)
   assert not formset.is_valid()
   ```
   (Adjust formset prefix and field names if your formset uses different names.)

Batch 2 complete when all of the above pass.

### Batch 3 — Views and templates (steps 6–11)

**Includes:** List, add, edit, delete views; templates; sidebar; optional admin.

**How to test after Batch 3:**

1. **List:** Navigate to Static Templates; see empty list and "Add static template" button.
2. **Add:** Add a template with ref_id, description, PDF file, and one form field (signature, member 2, date field "Date1", format "MM/dd/yy"). Submit. Redirect to list; new row appears.
3. **Edit:** Edit the template; add a second form field; optionally replace the PDF. Save. List and edit reflect changes.
4. **Delete:** Click Delete; see confirmation; POST to delete. Template removed.
5. **PDF access:** After add, the stored PDF should be reachable at `/media/document_templates/static/<filename>` (or similar). Open in browser; PDF displays.
6. **Sidebar:** "Static Templates" appears; active when on the static templates list/edit/add.
7. **Conditional validation:** On add/edit, date_signed_field_name and date_signed_format are always visible; formset clean requires them only when field_type is "signature".

Batch 3 complete when all of the above pass.

---

## 8. File and URL Summary

| Item   | Value |
|--------|-------|
| App    | `apps.doctemplates` |
| Model  | `StaticDocumentTemplate(ref_id, description, file, tagging_type, tagging_data)` |
| List   | `/document-templates/static/` |
| Add    | `/document-templates/static/add/` |
| Edit   | `/document-templates/static/<id>/edit/` |
| Delete | GET confirm, POST delete at `/document-templates/static/<id>/delete/` |
| Nav    | Sidebar: "Static Templates" → list |
| Storage| `MEDIA_ROOT/document_templates/static/` |
| Seed   | None |

---

## 9. Out of Scope (This Phase)

- Dynamic document templates (separate plan).
- Document Set Templates (separate plan).
- Actual use of templates in document generation (separate plan).
- PDF form field auto-detection (future enhancement per DESIGN-DOCS).
- Pagination or search on the list.

---

*End of plan. Proceed to implementation only after review.*

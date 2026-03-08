# Plan: Add Document Set Templates

This document outlines how to add **Document Set Templates** to the Django lease application. A Document Set Template defines an ordered list of Document Templates (Static and/or Dynamic) and is associated with a Deal Type. When documents are generated for a Deal, the system uses the Deal's Deal Type to look up the appropriate Document Set Template and instantiates the listed templates in order.

**Design reference:** DESIGN-DOCS.md — Document Set Templates section.

**Prerequisites:** 10-PLAN-ADD-STATIC-DOC-TEMPLATES.md, 20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md must be implemented (apps.doctemplates with Static and Dynamic templates). Dynamic templates may include image variable mapping (Images optgroup, source format `image:<uuid>` per DESIGN-DOCS); Document Set Templates reference templates by type only and do not depend on mapping contents. ../70-PLAN-MASTER.md plans 1–4 are implemented, including ../02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md (DealType and Deal with deal_type exist; Deal Type "Lease - Single Signer" is the default).

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Models:** `DocumentSetTemplate` (deal_type, name) and `DocumentSetTemplateItem` (ordered references to Static or Dynamic templates).
- **Data:** No seed data; list starts empty. Users add via UI.
- **UI:** List, Add, Edit, Delete — same pattern as Deals and Vehicles. Add: select Deal Type, add templates in order. Edit: change templates and reorder (up/down buttons). All templates in a Document Set Template are required.
- **Access:** Authenticated users only (`@login_required`).

---

## 2. Model and Storage

- **App:** Add to existing `apps.doctemplates`.
- **Persistence:** SQLite (existing database).
- **Dependency:** `apps.deals` must be in `INSTALLED_APPS` (for DealType FK).

### DocumentSetTemplate

- `deal_type` — `OneToOneField(DealType, on_delete=models.PROTECT)`. One Document Set Template per Deal Type. (Django recommends OneToOneField over ForeignKey(unique=True); both enforce uniqueness.) Import `DealType` from `apps.deals.models`.
- `name` — `CharField`, max_length=200, optional (blank=True). Display name; if blank, use `str(deal_type)`.
- Conventions: Docstrings, `__str__` (return `name or str(self.deal_type)`), `verbose_name` / `verbose_name_plural` in `Meta`, `ordering = ['deal_type__name']`.

### DocumentSetTemplateItem

- `document_set_template` — `ForeignKey(DocumentSetTemplate, on_delete=models.CASCADE, related_name='items')`
- `order` — `PositiveIntegerField`. 1-based; items displayed in ascending order.
- `content_type` — `ForeignKey(ContentType, on_delete=models.CASCADE)`
- `object_id` — `PositiveIntegerField`
- `template` — `GenericForeignKey('content_type', 'object_id')` — references either `StaticDocumentTemplate` or `DynamicDocumentTemplate`

- Conventions: Docstrings, `Meta` with `unique_together = [['document_set_template', 'order']]` or `UniqueConstraint` on (document_set_template, order), `ordering = ['order']`.

**Note:** Use Django's `ContentType` framework. Limit `content_type` choices to `StaticDocumentTemplate` and `DynamicDocumentTemplate` in the form.

---

## 3. No Seed Data

List starts empty. Users create Document Set Templates via the UI. The platform has one Deal Type ("Lease - Single Signer") implemented; users create one Document Set Template for it.

---

## 4. Pages and Behavior

### 4.1 List page

- **URL:** `/document-templates/doc-set-templates/` (name `docsettemplate_list`).
- **Content:** Table with columns **Name** (or Deal Type), **Deal Type**, **Templates** (count or summary), **Actions** (Edit, Delete).
- **Header:** "Document Set Templates"; button **Add document set template** → add URL. When no Deal Type is available (all have Document Set Templates), hide or disable the Add button.
- **Empty state:** "No document set templates yet. Add one to get started."
- **Layout:** Use `base.html`. Add sidebar link "Document Set Templates" → list. Place after Dynamic Templates, before Images. Order: Static Templates, Dynamic Templates, Document Set Templates, Images.

### 4.2 Add template

- **URL:** `/document-templates/doc-set-templates/add/` (name `docsettemplate_add`).
- **Form:** deal_type (dropdown of Deal Types that do not yet have a Document Set Template), name (optional). Template list: formset of rows; each row has template (dropdown of Static + Dynamic templates, formatted as "ref_id (Static)" or "ref_id (Dynamic)") and order (implicit from row position).
- **When no Static or Dynamic templates exist:** Redirect to list or show Add form with error message: "Create at least one Static or Dynamic template first." Do not allow submitting until at least one template exists.
- **When no Deal Type is available** (all have Document Set Templates): Redirect to list with message "Every deal type already has a document set template.", or do not show Add link.
- **Validation:** At least one template required. No duplicate templates in the same Document Set Template.
- **On submit:** Create DocumentSetTemplate and DocumentSetTemplateItem records; redirect to list with "Document set template added."

### 4.3 Edit template

- **URL:** `/document-templates/doc-set-templates/<id>/edit/` (name `docsettemplate_edit`).
- **Form:** Same as add; pre-fill deal_type, name, and items from instance. On edit, deal_type is read-only (disabled) and the template submits it via a hidden input so the form validates; only name and items are updated on save.
- **Reordering:** Up/down buttons per row for **existing** items only (saved DocumentSetTemplateItem rows). Each button is a small form POSTing to the move-up or move-down URL; new/empty formset rows do not show move buttons. Implement as: `POST /document-templates/doc-set-templates/<pk>/items/<item_id>/move-up/` and `.../move-down/` views; on POST, adjust `order` values and redirect to edit page.
- **On submit:** Update DocumentSetTemplate and replace items (delete existing, create from formset).

### 4.4 Delete template

- **POST required.** Dedicated confirmation page: GET shows "Are you sure you want to delete this document set template?" (show name/deal type); POST deletes record and related items; redirect to list with "Document set template deleted."

---

## 5. Template Selection UI

**Dropdown choices:** Build a combined list of Static and Dynamic templates. Format: `"static-<pk>"` / `"dynamic-<pk>"` for value; label: `"{ref_id} (Static)"` or `"{ref_id} (Dynamic)"`. **Helper:** `get_document_template_choices()` in `apps/doctemplates/forms.py` returns a list of `(value, label)` tuples. The form adds a blank option (`"---------"`) in `__init__` so extra formset rows can be left empty. When choices are empty, the add view redirects to list with "Create at least one Static or Dynamic template first."

**Parsing:** On form save, parse `"static-5"` → ContentType for StaticDocumentTemplate, object_id=5. Use `ContentType.objects.get_for_model(StaticDocumentTemplate)` and `object_id`.

**Ordering:** Use up/down buttons for v1 (simpler than drag-and-drop). Each item has [Up] [Down] links. Up swaps order with previous item; Down swaps with next. Disable Up for first item, Down for last.

---

## 6. Navigation and Integration

- **Sidebar:** Add "Document Set Templates" link → `doctemplates:docsettemplate_list`, icon e.g. `bi bi-collection`. Insert after Dynamic Templates, before Images.
- **URLs:** Add `path("doc-set-templates/", ...)` in `apps.doctemplates.urls`. Names: `docsettemplate_list`, `docsettemplate_add`, `docsettemplate_edit`, `docsettemplate_delete_confirm`, `docsettemplate_item_move_up`, `docsettemplate_item_move_down`.

---

## 7. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–3)

1. **DocumentSetTemplate model**
   - In `apps/doctemplates/models.py`, add `DocumentSetTemplate` with `deal_type` (OneToOneField to `DealType`), `name` (CharField, max_length=200, blank=True). Add `__str__` and `Meta`.
   - Ensure `apps.deals` is in `INSTALLED_APPS` before `apps.doctemplates` so DealType is available.

2. **DocumentSetTemplateItem model**
   - Add `DocumentSetTemplateItem` with `document_set_template` (FK), `order` (PositiveIntegerField), `content_type` (FK to ContentType), `object_id` (PositiveIntegerField), `template` (GenericForeignKey).
   - Add `Meta` with `ordering = ['order']`, and `UniqueConstraint(fields=['document_set_template', 'order'], name='unique_order_per_template')` (or equivalent).

3. **Migrations**
   - Run `python manage.py makemigrations doctemplates --name add_docsettemplate`.
   - Run `python manage.py migrate`. If the shell does not have the project venv activated (e.g. in CI or when an agent runs commands), use the venv interpreter directly: `.venv/bin/python manage.py migrate`.

4. **URL routing**
   - Add `path("doc-set-templates/", ...)` with a minimal list view placeholder. Add paths for add, edit, delete, move-up, move-down (can 404 until Batch 3).

Batch 1 complete when models exist, migrations apply, and `/document-templates/doc-set-templates/` loads.

### Batch 2 — Forms (steps 5–7)

5. **DocumentSetTemplateForm**
   - Fields: `deal_type` (ModelChoiceField), `name` (CharField, required=False). On **Add** only: restrict queryset to Deal Types that do not yet have a Document Set Template — e.g. `DealType.objects.exclude(id__in=DocumentSetTemplate.objects.values_list('deal_type_id', flat=True))`. On Edit: show full queryset but set `deal_type` to disabled so it cannot be changed; override `save()` to update only `name` when editing (disabled fields are omitted from `cleaned_data`, so the template must submit a hidden `deal_type` for validation).
6. **DocumentSetTemplateItemFormSet**
   - Form with `template_choice` (ChoiceField, choices from `get_document_template_choices()` with blank option added in form `__init__`). Use `formset_factory` with `extra=2`, `min_num=1`, `validate_min=True`, and a **custom BaseFormSet** that in `clean()` rejects duplicate template choices (e.g. `BaseDocumentSetTemplateItemFormSet`).
   - Use a consistent formset prefix (e.g. `items`) for management form and POST keys.
   - Helpers: `items_to_formset_initial(items)` — convert ordered DocumentSetTemplateItem queryset to list of dicts with key `template_choice` (`"static-<pk>"` or `"dynamic-<pk>"`). `formset_to_items(cleaned_data_list, document_set_template)` — convert formset cleaned_data to unsaved DocumentSetTemplateItem instances; **skip empty rows** (blank template_choice) and assign 1-based order from row position.
   - Validation: no duplicate template choices; at least one item (enforced by formset min_num and custom clean).

7. **get_document_template_choices()**
   - In `apps/doctemplates/forms.py`: return `[(f"static-{t.pk}", f"{t.ref_id} (Static)") for t in StaticDocumentTemplate.objects.all().order_by("ref_id")] + [(f"dynamic-{t.pk}", f"{t.ref_id} (Dynamic)") for t in DynamicDocumentTemplate.objects.all().order_by("ref_id")]`. Order by ref_id for consistency. The form adds the blank option when building the field choices.

Batch 2 complete when forms validate and convert correctly.

### Batch 3 — Views and templates (steps 8–12)

8. **Views**
   - `docsettemplate_list` — List all DocumentSetTemplate with prefetch_related('items'). Pass `can_add` (True if at least one Deal Type has no Document Set Template) for Add button visibility.
   - `docsettemplate_add` — GET: if no Static/Dynamic templates exist, redirect to list with error "Create at least one Static or Dynamic template first."; if no available Deal Types, redirect with "Every deal type already has a document set template." Else: form + formset. POST: validate, create template and items, redirect.
   - `docsettemplate_edit` — GET: form with instance, formset from items; POST: validate, update template, replace items.
   - `docsettemplate_delete_confirm` — GET: confirmation; POST: delete.
   - `docsettemplate_item_move_up` / `docsettemplate_item_move_down` — POST only; get item, adjust order with sibling, redirect to edit.
   - All views: `@login_required`.

9. **URLs**
   - `doc-set-templates/` → list
   - `doc-set-templates/add/` → add
   - `doc-set-templates/<int:pk>/edit/` → edit
   - `doc-set-templates/<int:pk>/delete/` → delete confirm
   - `doc-set-templates/<int:pk>/items/<int:item_id>/move-up/` → move up
   - `doc-set-templates/<int:pk>/items/<int:item_id>/move-down/` → move down

10. **Templates**
    - `docsettemplate_list.html` — table (Name, Deal Type, Templates count, Actions), Add button (only when `can_add`), empty state. Optional subtitle e.g. "Ordered list of Static/Dynamic templates per deal type".
    - `docsettemplate_form.html` — deal_type, name; formset for items (template dropdown per row). On edit, pass a list of `(form, item_id)` per row (`form_rows`) so the template can render Up/Down only for existing items (`item_id` present); new/empty rows show no move buttons.
    - `docsettemplate_confirm_delete.html` — confirmation message (show name or deal type, and item count), POST form.

11. **Sidebar**
    - Add "Document Set Templates" nav item → `docsettemplate_list`, icon `bi bi-collection`, after Dynamic Templates, before Images. Active when `request.resolver_match.url_name` starts with `docsettemplate_` (list, add, edit).
12. **Optional**
    - Register `DocumentSetTemplate` (and `DocumentSetTemplateItem` as inline) in admin. The inline can be read-only (no add) since items reference templates via GenericForeignKey; the main doc set UI is used for editing items.

13. **Verification**
    - Full CRUD via UI; add template with one Static and one Dynamic template; edit and reorder with up/down; delete.

---

## 7a. Implementation Batches and Verification

Implement in **three batches**. After each batch, run the verification steps.

### Batch 1 — Data layer (steps 1–4)

**Includes:** DocumentSetTemplate, DocumentSetTemplateItem models, migrations, URL routing.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues. (Use `.venv/bin/python manage.py check` if the venv is not activated.)

2. **Migrations:** Run `python manage.py migrate` (or `.venv/bin/python manage.py migrate` if the venv is not activated). Verify `doctemplates_documentsettemplate` and `doctemplates_documentsettemplateitem` tables exist.

3. **Shell — create DocumentSetTemplate with items:**
   ```python
   from django.contrib.contenttypes.models import ContentType
   from apps.deals.models import DealType
   from apps.doctemplates.models import (
       DocumentSetTemplate,
       DocumentSetTemplateItem,
       StaticDocumentTemplate,
       DynamicDocumentTemplate,
   )

   dt = DealType.get_default()
   dst = DocumentSetTemplate.objects.create(deal_type=dt, name="Lease Documents")

   # Add item pointing to first Static template (if any)
   static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
   static_t = StaticDocumentTemplate.objects.first()
   if static_t:
       DocumentSetTemplateItem.objects.create(
           document_set_template=dst,
           order=1,
           content_type=static_ct,
           object_id=static_t.pk,
       )
   assert DocumentSetTemplate.objects.count() >= 1
   assert dst.items.count() >= 0
   ```

4. **URLs:** Visit `/document-templates/doc-set-templates/` — no 404; placeholder view acceptable.

Batch 1 complete when the above pass.

### Batch 2 — Forms (steps 5–7)

**Includes:** DocumentSetTemplateForm, DocumentSetTemplateItemFormSet, get_document_template_choices, conversion helpers.

**How to test after Batch 2:**

1. **Shell — get_document_template_choices returns list:**
   ```python
   from apps.doctemplates.forms import get_document_template_choices  # or utils
   choices = get_document_template_choices()
   assert isinstance(choices, list)
   # Each item is (value, label); value format "static-X" or "dynamic-X"
   ```

2. **Shell — valid DocumentSetTemplateForm:**
   ```python
   from apps.deals.models import DealType
   from apps.doctemplates.forms import DocumentSetTemplateForm

   dt = DealType.get_default()
   form = DocumentSetTemplateForm(data={"deal_type": dt.pk, "name": "Test Set"})
   assert form.is_valid(), form.errors
   ```

3. **Shell — formset converts template choice to ContentType/object_id:**
   ```python
   from apps.doctemplates.forms import formset_to_items  # adjust import as needed
   from apps.doctemplates.models import DocumentSetTemplate
   from django.contrib.contenttypes.models import ContentType

   dst = DocumentSetTemplate.objects.first()
   if dst:
       cleaned = [{"template_choice": "static-1"}]  # if Static pk=1 exists
       items = formset_to_items(cleaned, dst)
       assert len(items) == 1
       assert items[0].content_type is not None
       assert items[0].object_id is not None
   ```
   (Adjust pk and structure based on actual formset design.)

4. **Shell — formset rejects duplicate template choice:**
   ```python
   # Formset validation: two rows with same template_choice should fail
   # Implement and assert not formset.is_valid()
   ```

Batch 2 complete when forms and helpers work as above.

### Batch 3 — Views and templates (steps 8–13)

**Includes:** List, add, edit, delete, move-up, move-down views; templates; sidebar.

**How to test after Batch 3:**

1. **List:** Navigate to Document Set Templates; see empty list and "Add document set template" button.

2. **Add:** Create a Document Set Template with deal type "Lease - Single Signer", add at least one template (Static or Dynamic). Submit. Redirect to list; new row appears.

3. **Edit:** Edit the template; add a second template; use up/down to reorder. Save. List and edit reflect new order.

4. **Move up/down:** On edit page, click Up on the second item; it becomes first. Click Down on the first; it becomes second. Verify order persists.

5. **Delete:** Click Delete; see confirmation; POST to delete. Template and items removed.

6. **Validation — duplicate template:** On add or edit, try to add the same template twice; expect form error.

7. **Validation — no templates:** Try to save with zero templates; expect validation error (min_num=1).

8. **Sidebar:** "Document Set Templates" appears; active when on doc set templates list/add/edit.

9. **Deal type uniqueness:** Create a Document Set Template for "Lease - Single Signer". Try to create another — Add page should not offer "Lease - Single Signer" in the dropdown (filtered out), or Add button hidden if no Deal Types available.

10. **Empty templates:** With no Static or Dynamic templates, visit Add; redirect to list with "Create at least one Static or Dynamic template first."

11. **Protect templates in use:** Create a Document Set Template that includes a Static template. Go to Static Templates, try to delete that Static template. Expect error: "This template cannot be deleted because it is used in a Document Set Template." (Same for Dynamic.)

Batch 3 complete when all of the above pass.

---

## 8. File and URL Summary

| Item   | Value |
|--------|-------|
| App    | `apps.doctemplates` |
| Models | `DocumentSetTemplate(deal_type, name)`, `DocumentSetTemplateItem(document_set_template, order, content_type, object_id)` |
| List   | `/document-templates/doc-set-templates/` |
| Add    | `/document-templates/doc-set-templates/add/` |
| Edit   | `/document-templates/doc-set-templates/<id>/edit/` |
| Delete | GET confirm, POST delete at `/document-templates/doc-set-templates/<id>/delete/` |
| Move   | POST `/document-templates/doc-set-templates/<id>/items/<item_id>/move-up/` and `.../move-down/` |
| Nav    | Sidebar: "Document Set Templates" → list (after Dynamic Templates, before Images) |

---

## 9. Out of Scope (This Phase)

- Document generation (uses Document Set Templates; separate plan PLAN-ADD-DOCUMENT-SETS).
- Drag-and-drop reordering (up/down buttons for v1).
- Multiple Document Set Templates per Deal Type (future extensibility; unique on deal_type for now).
- Pagination or search on the list.

---

## 10. Implementation Notes

- **deal_type as OneToOneField:** Prefer `OneToOneField(DealType, on_delete=models.PROTECT)` for `DocumentSetTemplate.deal_type`. Django's system check warns that `ForeignKey(unique=True)` should be expressed as `OneToOneField`; using OneToOneField avoids the warning. If the model was created earlier with `ForeignKey(unique=True)`, a migration can change it to OneToOneField.
- **Running migrations without activated venv:** When the shell does not have the project's virtualenv activated (e.g. in automation, CI, or agent-run commands), run Django via the venv interpreter: `.venv/bin/python manage.py migrate`, `.venv/bin/python manage.py check`, etc.
- **GenericForeignKey:** Use `ContentType.objects.get_for_model(StaticDocumentTemplate)` and `get_for_model(DynamicDocumentTemplate)` when building/parsing choices. Store `content_type` and `object_id` on save. `formset_to_items` skips empty rows and assigns order from position.
- **Up/down logic:** To move item up: find item with `order == current_order - 1`; swap order values. Use temporary values to avoid unique constraint violation (e.g., set current to 0, set sibling to current_order, set current to sibling's old order). Then re-number all items sequentially (1, 2, 3, ...). To move down: analogous.
- **Formset prefix:** Use a constant prefix (e.g. `items`) for the item formset so management form and field names are predictable in templates and views.
- **DealType import and INSTALLED_APPS:** `from apps.deals.models import DealType`. Ensure `apps.deals` is listed **before** `apps.doctemplates` in `INSTALLED_APPS` to avoid import/dependency issues.
- **Protect Static/Dynamic templates in use:** Do not allow deleting a Static or Dynamic template if it is referenced by any `DocumentSetTemplateItem`. In the Static and Dynamic template **delete confirmation views** (on POST), query `DocumentSetTemplateItem` for references via `content_type` and `object_id`; if any exist, do not delete and re-render the confirmation page with an error message (e.g. "This template cannot be deleted because it is used in a Document Set Template.").

---

*End of plan. Proceed to implementation only after review.*

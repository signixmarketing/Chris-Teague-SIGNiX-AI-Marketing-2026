# Plan: Add Deals to the Lease App

This document outlines how to add **deals** (lease origination records) to the Django lease application. A deal has properties (dates, payment, deposit, insurance, governing law), is associated with a **lease officer** (User), and can have **zero-to-many vehicles** and **zero-to-many contacts**. The UI lets users create a deal, fill in its properties, and associate the user, vehicle(s), and contact(s).

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines two batches and how to test each one.

---

## 1. Goals and Scope

- **Model**: A `Deal` model with the properties listed in Section 2, plus a **ForeignKey** to User (lease officer) and **ManyToMany** relations to Vehicle and Contact.
- **UI**: A **Deals** page listing deals (table with key columns), plus **Add deal** and **Edit deal** forms where the user can fill in deal properties and select the lease officer, vehicle(s), and contact(s). Delete via confirmation page (POST only).
- **Access**: Authenticated users only (`@login_required`). On create, the lease officer defaults to the current user; the form can show or allow changing the lease officer (e.g. dropdown of staff users or read-only for current user—implementation choice).

---

## 2. Deal Relationships (Agreed)

| Relationship | Shape | Notes |
|--------------|--------|-------|
| **Deal → User (lease officer)** | **ForeignKey on Deal** (`lease_officer`) | One deal has one lease officer. Default to `request.user` when creating. |
| **Deal → Contacts** | **ManyToMany on Deal** (`contacts`) | Zero-to-many contacts per deal (e.g. lessee, co-signer). |
| **Deal → Vehicles** | **ManyToMany on Deal** (`vehicles`) | Zero-to-many vehicles per deal. |

---

## 3. Deal Model (Properties and Persistence)

- **Persistence**: Stored in the project’s existing **SQLite** database. Django migrations create the table and M2M tables; ORM handles reads/writes.
- **App**: New app `apps.deals` (under `apps/`), with `name = "apps.deals"` in `AppConfig`.

**Model: `Deal`**

- **Relationships**
  - `lease_officer` — `ForeignKey(settings.AUTH_USER_MODEL, on_delete=...)` with `related_name='deals'`. Required.
  - `vehicles` — `ManyToManyField(Vehicle, blank=True)`.
  - `contacts` — `ManyToManyField(Contact, blank=True)`.

- **Properties**
  - `date_entered` — `DateField` (date the deal was entered).
  - `lease_start_date` — `DateField`.
  - `lease_end_date` — `DateField`.
  - `payment_amount` — `DecimalField(max_digits=12, decimal_places=2)` (money).
  - `payment_period` — `CharField(max_length=20, default='month')` (e.g. "month" for monthly payments). Optional: use `choices` (e.g. month, week, year) or leave free text.
  - `security_deposit` — `DecimalField(max_digits=12, decimal_places=2)` (allow null/blank if needed).
  - `insurance_amount` — `DecimalField(max_digits=12, decimal_places=2)` (amount of insurance the lessee must have for the vehicle).
  - `governing_law` — `CharField(max_length=100, default='Delaware')` (state or state name).

**Conventions**: Docstrings, `__str__` (e.g. "Deal #&lt;id&gt;" or "Deal &lt;date_entered&gt; — &lt;lease_officer&gt;"), `verbose_name` / `verbose_name_plural` in `Meta`. Order deals by `-date_entered` or `-id` in list views.

---

## 4. Pages and Behavior

### 4.1 List page (Deals table)

- **URL**: `/deals/` (name `deal_list`).
- **Content**: Table with columns such as **Date entered**, **Lease officer**, **Lease start**, **Lease end**, **Payment**, **Vehicles** (count or summary), **Contacts** (count or summary), **Actions** (Edit, Delete).
- **Header**: Page title "Deals"; primary button **Add deal** linking to `/deals/add/`.
- **Empty state**: "No deals yet. Add one to get started." and Add deal button.
- **Layout**: Use `base.html`. Add **Deals** to the sidebar (e.g. after Contacts, before Admin).

### 4.2 Add deal

- **URL**: `/deals/add/` (name `deal_add`).
- **Method**: GET shows form; POST creates deal and redirects to list with "Deal added."
- **Form**: All deal properties (date_entered, lease_start_date, lease_end_date, payment_amount, payment_period, security_deposit, insurance_amount, governing_law). **Lease officer**: default to current user; show as read-only or dropdown of users (e.g. staff). **Vehicles**: multi-select (checkboxes or `<select multiple>`) so user can pick zero or more vehicles. **Contacts**: multi-select so user can pick zero or more contacts. Use Bootstrap/card styling consistent with other forms.

### 4.3 Edit deal

- **URL**: `/deals/<id>/edit/` (name `deal_edit`).
- **Method**: GET shows form with current values and current vehicles/contacts selected; POST updates and redirects to list with "Deal updated."
- **Form**: Same fields as add; M2M fields must load existing related vehicles/contacts so they are pre-selected.

### 4.4 Delete deal

- **Requirement**: Deletion must use **POST** (not GET). **Dedicated confirmation page**: GET `/deals/<id>/delete/` shows "Are you sure you want to delete this deal?" (with optional summary); form POSTs to delete; on POST, delete and redirect to list with "Deal deleted."

### 4.5 Implementation notes: deal form (date fields)

- **Date inputs on edit**: HTML5 `<input type="date">` requires the `value` attribute in **YYYY-MM-DD** format. The form’s date field value is a Python `date` object; if you output it without formatting (e.g. `{{ form.date_entered.value }}`), the browser may not recognize it and the fields will appear **empty on edit** even when the deal has dates. Always format date values for these inputs using the Django template filter: `{{ form.date_entered.value|date:'Y-m-d'|default:'' }}` (and the same for `lease_start_date` and `lease_end_date`). This ensures the value is in `Y-m-d` so the date picker displays correctly when editing.

---

## 5. Navigation and Integration

- **Sidebar** (`templates/base.html`): Add **Deals** link (e.g. after Contacts), URL `{% url 'deals:deal_list' %}`, icon e.g. `bi bi-file-earmark-text`. Mark active when `request.resolver_match.app_name == 'deals'`.
- **Config**: In `config/urls.py`, add `path("deals/", include("apps.deals.urls"))`. In `config/settings.py`, add `"apps.deals"` to `INSTALLED_APPS` (and ensure `apps.vehicles` and `apps.contacts` are present so Deal can reference them).
- **Jazzmin**: Optional: add "Deals" custom link to `/deals/` in the Admin sidebar.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–2)

1. **Create `apps.deals` app**
   - Create `apps/deals/` with `__init__.py`, `apps.py` (`name = "apps.deals"`), `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, and `migrations/__init__.py`.
   - Add `"apps.deals"` to `INSTALLED_APPS` in `config/settings.py` (after `apps.vehicles` and `apps.contacts` so Deal can import Vehicle and Contact).

2. **Deal model**
   - In `apps/deals/models.py`, define `Deal` with: `lease_officer` (FK to User), `vehicles` (M2M to Vehicle, blank=True), `contacts` (M2M to Contact, blank=True); and fields `date_entered`, `lease_start_date`, `lease_end_date`, `payment_amount`, `payment_period` (default `'month'`), `security_deposit`, `insurance_amount`, `governing_law` (default `'Delaware'`). Add `__str__` and `Meta` verbose names.
   - Run `python manage.py makemigrations deals` and `python manage.py migrate`.

No seed data is required for Batch 1 (deals are created via the UI). Optional: add a management command later to create a sample deal if desired.

### Batch 2 — UI and CRUD (steps 3–9)

3. **Forms**
   - In `apps/deals/forms.py`, create a `DealForm` (ModelForm or custom form) with all Deal fields plus `vehicles` and `contacts`. Use `ModelMultipleChoiceField` or the model’s M2M with a widget such as `CheckboxSelectMultiple` (or `SelectMultiple`) so users can select multiple vehicles and multiple contacts. Set `lease_officer` default in the view (e.g. `initial={'lease_officer': request.user}`) and either exclude it from the form (set in view on save) or show as read-only/dropdown.

4. **Views**
   - List: `deal_list` — list all deals (e.g. `Deal.objects.all().order_by('-date_entered')` or `order_by('-id')`); pass `deal_list` to template. Prefetch `vehicles` and `contacts` (and optionally `lease_officer`) for efficient display.
   - Add: `deal_add` — GET form (with lease_officer default); POST create deal, set `lease_officer=request.user` if not in form, save M2M (vehicles, contacts) from form; redirect to list with message.
   - Edit: `deal_edit` — GET form with instance and current vehicles/contacts; POST update and save M2M; redirect to list with message.
   - Delete: `deal_delete_confirm` — GET confirmation page; POST delete deal and redirect to list with "Deal deleted." All views `@login_required`.

5. **URLs**
   - In `apps/deals/urls.py`: `app_name = "deals"`; routes for list (`""`), add (`"add/"`), edit (`"<int:pk>/edit/"`), delete (`"<int:pk>/delete/"`).
   - In `config/urls.py`: `path("deals/", include("apps.deals.urls"))`.

6. **Templates**
   - `templates/deals/deal_list.html` — table (date entered, lease officer, lease start/end, payment, vehicles/contacts count or summary, Actions); "Add deal" button; empty state.
   - `templates/deals/deal_form.html` — add/edit form: sections for deal properties, lease officer (display or select), vehicles (multi-select), contacts (multi-select). Same card/Bootstrap style as other forms. **Date fields**: use `{{ form.<field>.value|date:'Y-m-d'|default:'' }}` for `date_entered`, `lease_start_date`, and `lease_end_date` so `<input type="date">` values display on edit (see Section 4.5).
   - `templates/deals/deal_confirm_delete.html` — confirmation message and POST form (Cancel → list, Delete → submit).

7. **Sidebar**
   - Update `templates/base.html`: add Deals nav item with link to `deals:deal_list` and active state when on deals app.

8. **Optional**
   - Register `Deal` in Django admin (list_display, filter, search; inline or raw_id for M2M if helpful). Add Jazzmin `custom_links` entry for "Deals" → `/deals/`.

9. **Verification**
   - Run server; log in; open Deals; create a deal (fill properties, select lease officer, vehicles, contacts); confirm it appears in the list with correct data; edit deal and change fields/vehicles/contacts; delete via confirmation page (POST only).

---

## 6a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps below.

### Batch 1 — Data layer (steps 1–2)

**Includes:** Create `apps.deals` app, add to `INSTALLED_APPS`, define `Deal` model (all properties + lease_officer FK + vehicles/contacts M2M), run migrations.

**How to test after Batch 1:**

1. **Django check:** With venv active, run `python manage.py check`. Expect "System check identified no issues (0)."
2. **Migrations:** Run `python manage.py migrate`. Confirm the `deals` migration is applied and that the `deals_deal` table and M2M tables (e.g. `deals_deal_vehicles`, `deals_deal_contacts`) exist without errors.
3. **Model in shell:** In `python manage.py shell`: `from apps.deals.models import Deal`; create a minimal deal (set required fields including `lease_officer` to an existing user); save; verify `deal.vehicles`, `deal.contacts`, and `deal.lease_officer` are accessible. Optionally add a vehicle and contact via `deal.vehicles.add(...)` and `deal.contacts.add(...)` and confirm they persist.

You will not have the Deals page or sidebar link until Batch 2. Batch 1 is complete when the above pass.

### Batch 2 — UI and CRUD (steps 3–9)

**Includes:** Forms (with multi-select for vehicles and contacts, lease officer handling), views (list, add, edit, delete), URLs, templates (list, form, confirm delete), sidebar, and optional admin/Jazzmin.

**How to test after Batch 2:**

1. Start the server. Log in as **karl** (or any staff user).
2. **Sidebar:** **Deals** appears (e.g. after Contacts). Click it; list at `/deals/`.
3. **Empty state:** With no deals, the list shows the empty-state message and "Add deal" button.
4. **Add deal:** Click "Add deal". Fill in date entered, lease start/end, payment amount, payment period (default "month"), security deposit, insurance amount, governing law (default "Delaware"). Confirm lease officer is set (e.g. current user). Select one or more vehicles and one or more contacts (if any exist). Submit. You should be redirected to the list with "Deal added." and the new deal in the table with correct dates, payment, and associated lease officer/vehicles/contacts.
5. **List:** Table shows date entered, lease officer, lease start/end, payment, and vehicles/contacts (count or names). Edit and Delete actions work.
6. **Edit:** Open a deal for edit. Change a property and/or vehicles/contacts; save. List and detail should reflect changes; "Deal updated." message shown.
7. **Delete:** Click Delete on a deal. Confirmation page (GET). Submit delete form (POST). Deal removed and "Deal deleted." shown. Visiting the delete URL with GET only does not delete.

Batch 2 is complete when all of the above pass.

---

## 7. File and URL Summary

| Item | Value |
|------|--------|
| App | `apps.deals` |
| Model | `Deal(lease_officer, vehicles M2M, contacts M2M, date_entered, lease_start_date, lease_end_date, payment_amount, payment_period, security_deposit, insurance_amount, governing_law)` |
| List | `/deals/` — table, Add button, Edit/Delete per row |
| Add | `/deals/add/` — form (properties + lease officer + vehicles + contacts), redirect to list |
| Edit | `/deals/<id>/edit/` — form, redirect to list |
| Delete | GET `/deals/<id>/delete/` — confirm; POST — delete, redirect to list |
| Nav | Sidebar: "Deals" → `/deals/` |
| Seed | Optional; no seed required for initial implementation |

---

## 8. Out of Scope (This Phase)

- SIGNiX integration / digital signing (future).
- Deal status workflow (draft, submitted, signed, etc.) beyond basic CRUD.
- Contact roles on a deal (e.g. lessee vs co-signer)—can add later with a through model if needed.
- Pagination or search on deal list (add later if needed).
- Soft delete (hard delete only for now).

---

*End of plan. Proceed to implementation only after review.*

# Plan: Add Vehicles to the Lease App

This document outlines how to add **vehicles** (jet packs) to the existing Django lease application. Vehicles have SKU, year, and JPIN; the app will provide a list page (table) and full CRUD: add, edit, delete.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines two batches and how to test each one.

**Part of the business-domain sequence.** See **PLAN-BIZ-DOMAIN-MASTER.md** for implementation order and how this plan relates to Contacts and Deals. **Design:** **DESIGN-BIZ-DOMAIN.md** (entity model, relationships, UI conventions).

---

## 1. Goals and Scope

- **Model**: A `Vehicle` model with `sku`, `year`, and `jpin` (all stored as strings; year as string to match the sample data).
- **Data**: One initial vehicle (jet pack) as specified below.
- **UI**: A **Vehicles** page that lists all vehicles in a table (columns: SKU, Year, JPIN) with actions to add, edit, and delete.
- **Access**: Same as profile—authenticated users only (`@login_required`). No per-user permissions; any logged-in user can manage vehicles (consistent with a small lease-officer app).

---

## 2. Vehicle Model

- **Persistence**: Vehicle data is stored in the project’s existing **SQLite** database (same as in the main PLAN-BASELINE.md). No additional database or configuration is required; Django migrations create the table and the ORM handles reads/writes.
- **App**: New app `apps.vehicles` (under `apps/`), with `name = "apps.vehicles"` in `AppConfig`.
- **Model**: `Vehicle`
  - `sku` — `CharField`, max length sufficient for names like "Skyward Personal Jetpack P-2024" (e.g. 200).
  - `year` — `CharField` (e.g. max_length=4 or 10) to store values like `"2024"`.
  - `jpin` — `CharField`, unique identifier (e.g. max_length=50); consider `unique=True` so each JPIN is unique per vehicle.

**Conventions**: Docstrings, `__str__` (e.g. return `sku` or `f"{sku} ({year})"`), and `verbose_name` / `verbose_name_plural` in `Meta`. No custom user or lease-officer link on the model in this phase.

---

## 3. Initial Vehicle (Seed Data)

One jet pack will be added as follows (per your specification):

| Field | Value |
|-------|--------|
| sku   | Skyward Personal Jetpack P-2024 |
| year  | 2024 |
| jpin  | 4CH8P4K7E3X6Z9R2V |

**Implementation**: A **management command** (e.g. `setup_initial_vehicle` or `seed_vehicles`) that creates this vehicle if it does not already exist (e.g. look up by `jpin` or `sku` to avoid duplicates). Idempotent so it can be run after `migrate` without duplicating the record. Document in this plan that running the command is part of setup (and optionally call it from the same place as `setup_initial_user` in docs, or keep as a separate step).

---

## 4. Pages and Behavior

### 4.1 List page (Vehicles table)

- **URL**: `/vehicles/` (e.g. name `vehicle_list`).
- **Content**: A table with three columns: **SKU**, **Year**, **JPIN**. Each row shows one vehicle. Add an **Actions** column (or inline buttons) with **Edit** and **Delete** per row.
- **Header**: Page title "Vehicles" (or "Vehicles (Jet Packs)");
  - A primary button **Add vehicle** that links to the add form (e.g. `/vehicles/add/`).
- **Empty state**: If there are no vehicles, show the table with a message like "No vehicles yet. Add one to get started." and the Add vehicle button.
- **Layout**: Use `base.html` (same sidebar as Profile). Add a **Vehicles** link in the sidebar between Profile and Admin (see Section 5).

### 4.2 Add vehicle

- **URL**: `/vehicles/add/` (name `vehicle_add`).
- **Method**: GET shows form; POST creates a vehicle and redirects to the list with a success message (e.g. "Vehicle added.").
- **Form**: Fields `sku`, `year`, `jpin`. Use a `ModelForm`; validation as per model (required fields, optional `unique=True` on `jpin`). Same styling as profile edit (card, Bootstrap).

### 4.3 Edit vehicle

- **URL**: `/vehicles/<id>/edit/` (e.g. `vehicle_edit` with `pk`).
- **Method**: GET shows form with current values; POST updates and redirects to list with "Vehicle updated."
- **Form**: Same fields as add; pre-filled with the selected vehicle. 404 if vehicle does not exist.

### 4.4 Delete vehicle

- **Requirement**: Deletion must use **POST** (not GET), to avoid accidental deletion via links and to stay consistent with Django best practice (like logout in the main plan).
- **Options**:
  - **Option A**: List page has a small form per row that POSTs to a delete URL (e.g. `/vehicles/<id>/delete/`). Include a confirmation step: either a Bootstrap modal ("Are you sure?") that submits the form, or a dedicated confirmation page that shows the vehicle and has "Cancel" / "Delete" (Delete = POST).
- **Option B**: Dedicated confirmation page: link "Delete" → GET `/vehicles/<id>/delete/` shows a page "Are you sure you want to delete &lt;vehicle sku&gt;?" with a form that POSTs to the same URL (or to a different action URL); on POST, delete and redirect to list with "Vehicle deleted."
- **Recommendation**: **Option B** (dedicated confirmation page) for clarity and one consistent POST endpoint. So: GET `/vehicles/<id>/delete/` → confirmation page; POST → delete and redirect to list.

---

## 5. Navigation and Integration

- **Sidebar** (`templates/base.html`): Add a **Vehicles** link after Profile and before Admin:
  - Text: "Vehicles", URL: `{% url 'vehicles:vehicle_list' %}`, icon: e.g. `bi bi-truck` or `bi bi-box-seam`. Mark active when `request.resolver_match.url_name` is in the vehicle URL names (e.g. `vehicle_list`, `vehicle_add`, `vehicle_edit`, `vehicle_delete_confirm`).
- **Config**: In `config/urls.py`, include the vehicles app URLs under the `vehicles/` prefix (e.g. `path("vehicles/", include("apps.vehicles.urls"))`). In `config/settings.py`, add `"apps.vehicles"` to `INSTALLED_APPS`.
- **Jazzmin**: Optional: add a "Vehicles" custom link in the Admin sidebar (e.g. to `/vehicles/`) so from Admin users can jump to the app vehicles list. Follow existing `custom_links` dict format.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–3)

1. **Create `apps.vehicles` app**
   - Create `apps/vehicles/` with `__init__.py`, `apps.py` (`name = "apps.vehicles"`), `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, and `migrations/__init__.py`.
   - Add `"apps.vehicles"` to `INSTALLED_APPS` in `config/settings.py`.

2. **Vehicle model**
   - In `apps/vehicles/models.py`, define `Vehicle` with `sku`, `year`, `jpin` (and optional `unique=True` on `jpin`). Add `__str__` and `Meta` verbose names.
   - Run `python manage.py makemigrations vehicles` and `python manage.py migrate`.

3. **Seed command**
   - Add `apps/vehicles/management/commands/setup_initial_vehicle.py` (or `seed_vehicles.py`) that creates the single jet pack (sku/year/jpin from Section 3) if not present (e.g. by `jpin`). Idempotent.
   - Run once: `python manage.py setup_initial_vehicle` (or the chosen command name).

### Batch 2 — UI and CRUD (steps 4–9)

4. **Forms**
   - In `apps/vehicles/forms.py`, create a `VehicleForm` ModelForm with fields `sku`, `year`, `jpin` for add and edit.

5. **Views**
   - List: `vehicle_list` — list all vehicles; pass `vehicle_list` to template.
   - Add: `vehicle_add` — GET form, POST create and redirect to list with message.
   - Edit: `vehicle_edit` — GET form with instance, POST update and redirect to list with message.
   - Delete: `vehicle_delete_confirm` — GET show confirmation page (vehicle summary + form); POST delete vehicle and redirect to list with "Vehicle deleted." Use `get_object_or_404(Vehicle, pk=pk)` for GET and POST.
   - All views: `@login_required`.

6. **URLs**
   - In `apps/vehicles/urls.py`: `app_name = "vehicles"`; routes for list, add, edit, delete (e.g. `vehicles/`, `vehicles/add/`, `vehicles/<int:pk>/edit/`, `vehicles/<int:pk>/delete/`).
   - In `config/urls.py`: add `path("vehicles/", include("apps.vehicles.urls"))` so list/add/edit/delete resolve to `/vehicles/`, `/vehicles/add/`, etc. (order so it does not conflict with `users` or `accounts`).

7. **Templates**
   - `templates/vehicles/vehicle_list.html` — extends `base.html`; table with SKU, Year, JPIN, Actions (Edit link, Delete link to confirmation page); "Add vehicle" button.
   - `templates/vehicles/vehicle_form.html` — used for add and edit (same form, different title: "Add vehicle" vs "Edit vehicle").
   - `templates/vehicles/vehicle_confirm_delete.html` — confirmation page with vehicle summary and POST form (Cancel → list, Delete → POST to delete view).

8. **Sidebar**
   - Update `templates/base.html`: add Vehicles nav item with link to `vehicles:vehicle_list` and active state for vehicle URL names.

9. **Optional**
   - Register `Vehicle` in Django admin (`apps/vehicles/admin.py`) for backup management.
   - Add Jazzmin `custom_links` entry for "Vehicles" → `/vehicles/`.

10. **Verification**
    - Run server; log in as karl. Open Vehicles: see table with the seeded jet pack. Add a vehicle, edit it, delete one (via confirmation page). Confirm no GET for delete (only POST), and messages show correctly.

---

## 6a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps below before continuing.

### Batch 1 — Data layer (steps 1–3)

**Includes:** Create `apps.vehicles` app, add to `INSTALLED_APPS`, define `Vehicle` model, run migrations, add and run the seed management command.

**How to test after Batch 1:**

1. **Django check:** With your venv active, run `python manage.py check`. You should see "System check identified no issues (0)."
2. **Migrations:** Run `python manage.py migrate`. Confirm the `vehicles` migration (and any new table) is applied without errors.
3. **Seed command:** Run the setup command (e.g. `python manage.py setup_initial_vehicle`). Then in the shell verify the vehicle exists:
   - `python manage.py shell`
   - `from apps.vehicles.models import Vehicle`
   - `v = Vehicle.objects.first()` (or `Vehicle.objects.get(jpin="4CH8P4K7E3X6Z9R2V")`)
   - Confirm: `v.sku` → `'Skyward Personal Jetpack P-2024'`, `v.year` → `'2024'`, `v.jpin` → `'4CH8P4K7E3X6Z9R2V'`
4. **Idempotent seed:** Run the seed command again; it should not create a duplicate (e.g. "already exists" or no error). Check `Vehicle.objects.count()` is still 1.

You will not have the Vehicles page or sidebar link until Batch 2. Batch 1 is complete when the above all pass.

### Batch 2 — UI and CRUD (steps 4–10)

**Includes:** Forms, views, URLs, templates (list, form, confirm delete), sidebar update, and optional admin/Jazzmin link.

**How to test after Batch 2:**

1. Start the server (e.g. `python manage.py runserver` or F5). Log in as **karl** / **karl**.
2. **Sidebar:** Confirm **Vehicles** appears in the sidebar (between Profile and Admin). Click it; you should see the vehicles list at `/vehicles/`.
3. **List page:** The table should show one row: SKU "Skyward Personal Jetpack P-2024", Year "2024", JPIN "4CH8P4K7E3X6Z9R2V", with Edit and Delete actions.
4. **Add:** Click "Add vehicle", fill in sku/year/jpin, submit. You should be redirected to the list with a success message and the new vehicle in the table.
5. **Edit:** Click Edit on a vehicle; change a field, save. List should show the updated data and a "Vehicle updated." message.
6. **Delete:** Click Delete on a vehicle. You should see the confirmation page (GET). Submit the delete form (POST). The vehicle should be removed from the list and a "Vehicle deleted." message shown. Confirm that visiting the delete URL with GET does **not** delete (only POST does).
7. **Empty state:** Delete all vehicles (or use the shell to remove them). Reload the list; you should see the empty-state message and the "Add vehicle" button.

Batch 2 is complete when all of the above pass.

---

## 7. File and URL Summary

| Item | Value |
|------|--------|
| App | `apps.vehicles` |
| Model | `Vehicle(sku, year, jpin)` |
| List | `/vehicles/` — table, Add button, Edit/Delete per row |
| Add | `/vehicles/add/` — form, redirect to list |
| Edit | `/vehicles/<id>/edit/` — form, redirect to list |
| Delete | GET `/vehicles/<id>/delete/` — confirm; POST — delete, redirect to list |
| Nav | Sidebar: "Vehicles" → `/vehicles/` |
| Seed | Management command; one jet pack (sku/year/jpin as in Section 3) |

---

## 8. Out of Scope (This Phase)

- Linking vehicles to leases or lease officers (future).
- SIGNiX or document/signing (future).
- Pagination or search (can add later if the list grows).
- Soft delete (hard delete only for now).

---

*End of plan. Proceed to implementation only after review.*

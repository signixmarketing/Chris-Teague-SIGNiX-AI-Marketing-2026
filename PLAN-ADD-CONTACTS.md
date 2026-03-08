# Plan: Add Contacts to the Lease App

This document outlines how to add **contacts** to the existing Django lease application. Contacts have First Name, Middle Name, Last Name, Email, and Phone Number; the app will provide a list page (table) and full CRUD: add, edit, delete—mirroring the Vehicles feature.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines two batches and how to test each one.

**Part of the business-domain sequence.** See **PLAN-BIZ-DOMAIN-MASTER.md** for implementation order and how this plan relates to Vehicles and Deals. **Design:** **DESIGN-BIZ-DOMAIN.md** (entity model, relationships, UI conventions).

---

## 1. Goals and Scope

- **Model**: A `Contact` model with `first_name`, `middle_name`, `last_name`, `email`, and `phone_number`.
- **Data**: One initial contact as specified below.
- **UI**: A **Contacts** page that lists all contacts in a table (columns: First Name, Middle Name, Last Name, Email, Phone Number) with actions to add, edit, and delete.
- **Access**: Same as profile and vehicles—authenticated users only (`@login_required`). Any logged-in user can manage contacts.

---

## 2. Contact Model

- **Persistence**: Contact data is stored in the project’s existing **SQLite** database (same as in the main PLAN-BASELINE.md). No additional database or configuration is required; Django migrations create the table and the ORM handles reads/writes.
- **App**: New app `apps.contacts` (under `apps/`), with `name = "apps.contacts"` in `AppConfig`.
- **Model**: `Contact`
  - `first_name` — `CharField` (e.g. max_length=150).
  - `middle_name` — `CharField` (e.g. max_length=150); **optional** (blank=True) so middle name can be empty.
  - `last_name` — `CharField` (e.g. max_length=150).
  - `email` — `EmailField` (e.g. max_length=254).
  - `phone_number` — `CharField` (e.g. max_length=30).

**Conventions**: Docstrings, `__str__` (e.g. return full name: first + middle + last, trimmed). `verbose_name` / `verbose_name_plural` in `Meta`. No unique constraint required for the initial version (optional: `unique=True` on `email` if contacts must have unique emails).

---

## 3. Initial Contact (Seed Data)

One contact will be added as follows (per your specification):

| Field         | Value                |
|---------------|----------------------|
| first_name    | Max                  |
| middle_name   | Danger               |
| last_name     | Fun                  |
| email         | signixkarl@gmail.com |
| phone_number  | 9197440153           |

**Implementation**: A **management command** (e.g. `setup_initial_contact`) that creates this contact if it does not already exist. Use a lookup that makes the command idempotent—e.g. by `email` (if unique) or by a combination such as (email, last_name). Idempotent so it can be run after `migrate` without duplicating the record.

---

## 4. Pages and Behavior

### 4.1 List page (Contacts table)

- **URL**: `/contacts/` (e.g. name `contact_list`).
- **Content**: A table with columns **First Name**, **Middle Name**, **Last Name**, **Email**, **Phone Number**, and **Actions** (Edit, Delete per row).
- **Header**: Page title "Contacts"; a primary button **Add contact** that links to `/contacts/add/`.
- **Empty state**: If there are no contacts, show the table with a message like "No contacts yet. Add one to get started." and the Add contact button.
- **Layout**: Use `base.html`. Add a **Contacts** link in the sidebar (e.g. after Vehicles, before Admin).

### 4.2 Add contact

- **URL**: `/contacts/add/` (name `contact_add`).
- **Method**: GET shows form; POST creates a contact and redirects to the list with a success message (e.g. "Contact added.").
- **Form**: Fields first_name, middle_name, last_name, email, phone_number. Use a ModelForm; middle_name optional (blank). Same styling as profile/vehicle forms (card, Bootstrap).

### 4.3 Edit contact

- **URL**: `/contacts/<id>/edit/` (e.g. `contact_edit` with `pk`).
- **Method**: GET shows form with current values; POST updates and redirects to list with "Contact updated."
- **Form**: Same fields as add; pre-filled. 404 if contact does not exist.

### 4.4 Delete contact

- **Requirement**: Deletion must use **POST** (not GET). Use a **dedicated confirmation page**: GET `/contacts/<id>/delete/` shows "Are you sure you want to delete &lt;contact name&gt;?" with a form that POSTs; on POST, delete and redirect to list with "Contact deleted."

---

## 5. Navigation and Integration

- **Sidebar** (`templates/base.html`): Add a **Contacts** link (e.g. after Vehicles, before Admin): Text "Contacts", URL `{% url 'contacts:contact_list' %}`, icon e.g. `bi bi-people`. Mark active when `request.resolver_match.app_name == 'contacts'`.
- **Config**: In `config/urls.py`, add `path("contacts/", include("apps.contacts.urls"))`. In `config/settings.py`, add `"apps.contacts"` to `INSTALLED_APPS`.
- **Jazzmin**: Optional: add a "Contacts" custom link in the Admin sidebar to `/contacts/`.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–3)

1. **Create `apps.contacts` app**
   - Create `apps/contacts/` with `__init__.py`, `apps.py` (`name = "apps.contacts"`), `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, and `migrations/__init__.py`.
   - Add `"apps.contacts"` to `INSTALLED_APPS` in `config/settings.py`.

2. **Contact model**
   - In `apps/contacts/models.py`, define `Contact` with first_name, middle_name (optional/blank), last_name, email, phone_number. Add `__str__` (e.g. full name) and `Meta` verbose names.
   - Run `python manage.py makemigrations contacts` and `python manage.py migrate`.

3. **Seed command**
   - Add `apps/contacts/management/commands/setup_initial_contact.py` that creates the contact from Section 3 if not present (e.g. lookup by email). Idempotent.
   - Run once: `python manage.py setup_initial_contact`.

### Batch 2 — UI and CRUD (steps 4–9)

4. **Forms**
   - In `apps/contacts/forms.py`, create a `ContactForm` ModelForm with fields first_name, middle_name, last_name, email, phone_number (middle_name optional).

5. **Views**
   - List: `contact_list` — list all contacts; pass `contact_list` to template.
   - Add: `contact_add` — GET form, POST create and redirect to list with message.
   - Edit: `contact_edit` — GET form with instance, POST update and redirect to list with message.
   - Delete: `contact_delete_confirm` — GET confirmation page; POST delete and redirect to list with "Contact deleted." All views `@login_required`.

6. **URLs**
   - In `apps/contacts/urls.py`: `app_name = "contacts"`; routes for list, add, edit, delete (e.g. `""`, `"add/"`, `"<int:pk>/edit/"`, `"<int:pk>/delete/"`).
   - In `config/urls.py`: `path("contacts/", include("apps.contacts.urls"))`.

7. **Templates**
   - `templates/contacts/contact_list.html` — table (First Name, Middle Name, Last Name, Email, Phone Number, Actions); "Add contact" button; empty state.
   - `templates/contacts/contact_form.html` — add/edit form (same template, different title).
   - `templates/contacts/contact_confirm_delete.html` — confirmation page with POST form.

8. **Sidebar**
   - Update `templates/base.html`: add Contacts nav item with link to `contacts:contact_list` and active state when on contacts app.

9. **Optional**
   - Register `Contact` in Django admin. Add Jazzmin `custom_links` entry for "Contacts" → `/contacts/`.

10. **Verification**
    - Run server; log in; open Contacts; see seeded contact; add, edit, delete (via confirmation page); confirm delete is POST-only.

---

## 6a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps below.

### Batch 1 — Data layer (steps 1–3)

**Includes:** Create `apps.contacts` app, add to `INSTALLED_APPS`, define `Contact` model, run migrations, add and run the seed management command.

**How to test after Batch 1:**

1. **Django check:** With venv active, run `python manage.py check`. Expect "System check identified no issues (0)."
2. **Migrations:** Run `python manage.py migrate`. Confirm the `contacts` migration is applied without errors.
3. **Seed command:** Run `python manage.py setup_initial_contact`. Then in the shell verify the contact exists:
   - `python manage.py shell`
   - `from apps.contacts.models import Contact`
   - `c = Contact.objects.get(email="signixkarl@gmail.com")` (or `.first()`)
   - Confirm: `c.first_name` → `'Max'`, `c.middle_name` → `'Danger'`, `c.last_name` → `'Fun'`, `c.email` → `'signixkarl@gmail.com'`, `c.phone_number` → `'9197440153'`
4. **Idempotent seed:** Run the seed command again; it should not create a duplicate. `Contact.objects.count()` should still be 1.

You will not have the Contacts page or sidebar link until Batch 2. Batch 1 is complete when the above all pass.

### Batch 2 — UI and CRUD (steps 4–10)

**Includes:** Forms, views, URLs, templates (list, form, confirm delete), sidebar update, and optional admin/Jazzmin link.

**How to test after Batch 2:**

1. Start the server. Log in as **karl** / **karl**.
2. **Sidebar:** **Contacts** appears (e.g. after Vehicles). Click it; list at `/contacts/`.
3. **List page:** Table shows one row: Max, Danger, Fun, signixkarl@gmail.com, 9197440153, with Edit and Delete.
4. **Add:** Click "Add contact", fill form, submit. Redirect to list with success message and new contact in table.
5. **Edit:** Edit a contact; save. List shows updated data and "Contact updated."
6. **Delete:** Click Delete → confirmation page (GET). Submit delete form (POST). Contact removed and "Contact deleted." shown. Visiting delete URL with GET only does not delete.
7. **Empty state:** Delete all contacts; reload list. Empty-state message and "Add contact" button visible.

Batch 2 is complete when all of the above pass.

---

## 7. File and URL Summary

| Item   | Value |
|--------|--------|
| App    | `apps.contacts` |
| Model  | `Contact(first_name, middle_name, last_name, email, phone_number)` |
| List   | `/contacts/` — table, Add button, Edit/Delete per row |
| Add    | `/contacts/add/` — form, redirect to list |
| Edit   | `/contacts/<id>/edit/` — form, redirect to list |
| Delete | GET `/contacts/<id>/delete/` — confirm; POST — delete, redirect to list |
| Nav    | Sidebar: "Contacts" → `/contacts/` |
| Seed   | Management command; one contact (Section 3 data) |

---

## 8. Out of Scope (This Phase)

- Linking contacts to leases, vehicles, or lease officers (future).
- Pagination or search (can add later).
- Soft delete (hard delete only).

---

*End of plan. Proceed to implementation only after review.*

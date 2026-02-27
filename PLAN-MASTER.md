# Plan Master — Implementation Order

This document defines the order in which to implement all PLANs to build (or rebuild) the lease origination app. Follow the plans in sequence. Each plan is self-contained with its own batches and verification steps.

**Usage:** Implement each plan below in order. Within each plan, follow its Implementation Order (Section 6) and Batches/Verification (Section 6a or equivalent). Do not skip ahead—later plans depend on the foundation and features from earlier plans.

---

## 1. PLAN-BASELINE.md

**Purpose:** Foundation of the app—Django project, venv, users app with LeaseOfficerProfile, auth (login/logout), base templates (base.html, base_plain.html), profile view/edit, initial user (karl), and Admin with Jazzmin.

**Implement:** Batch 1 (venv, project bootstrap, users app, model, migrations, setup_initial_user) then Batch 2 (auth, base template, profile views, URLs, admin base override). See PLAN-BASELINE.md Section 13 and Section 14.

---

## 2. PLAN-ADD-VEHICLES.md

**Purpose:** Vehicles app—Vehicle model (sku, year, jpin), CRUD (list, add, edit, delete with confirmation), sidebar link, seed jet pack via setup_initial_vehicle.

**Implement:** Batch 1 (apps.vehicles, model, migrations, seed command) then Batch 2 (forms, views, URLs, templates, sidebar, optional admin). See PLAN-ADD-VEHICLES.md Section 6 and Section 6a.

---

## 3. PLAN-ADD-CONTACTS.md

**Purpose:** Contacts app—Contact model (first_name, middle_name, last_name, email, phone_number), CRUD (list, add, edit, delete with confirmation), sidebar link, seed contact via setup_initial_contact.

**Implement:** Batch 1 (apps.contacts, model, migrations, seed command) then Batch 2 (forms, views, URLs, templates, sidebar, optional admin). See PLAN-ADD-CONTACTS.md Section 6 and Section 6a.

---

## 4. PLAN-ADD-DEALS.md

**Purpose:** Deals app—Deal model (lease_officer FK, vehicles M2M, contacts M2M; date_entered, lease_start/end, payment_amount, payment_period, security_deposit, insurance_amount, governing_law), CRUD with form for properties + multi-select vehicles/contacts. **Note:** Use `{{ form.<date_field>.value|date:'Y-m-d'|default:'' }}` for date inputs so they display on edit (Section 4.5).

**Implement:** Batch 1 (apps.deals, model, migrations) then Batch 2 (forms, views, URLs, templates, sidebar, optional admin). See PLAN-ADD-DEALS.md Section 6 and Section 6a.

---

## 5. PLAN-ADD-IMAGES.md

**Purpose:** Images app—Image model (name, file with upload_to under media/images/, stable URL via uuid), CRUD (list with URL column, add, edit with current image and optional replacement, delete with file cleanup). MEDIA_ROOT/MEDIA_URL, serve media in dev. Pillow required.

**Implement:** Batch 1 (apps.images, media config, model, migrations) then Batch 2 (forms with file upload, views, URLs, templates, sidebar, optional admin). Single "Add image" button in header only—no duplicate below table when empty. See PLAN-ADD-IMAGES.md Section 6 and Section 6a.

---

## Summary Table

| Order | Plan                 | App         | Key deliverables                                                |
|-------|----------------------|-------------|------------------------------------------------------------------|
| 1     | PLAN-BASELINE.md     | apps.users  | Auth, profile, base templates, karl user                         |
| 2     | PLAN-ADD-VEHICLES.md | apps.vehicles | Vehicle CRUD, jet pack seed                                    |
| 3     | PLAN-ADD-CONTACTS.md | apps.contacts | Contact CRUD, Max Danger Fun seed                             |
| 4     | PLAN-ADD-DEALS.md    | apps.deals  | Deal CRUD, M2M vehicles/contacts, lease officer                 |
| 5     | PLAN-ADD-IMAGES.md   | apps.images | Image upload, list with URL, edit with replacement              |

---

## Next Steps: Document Features

Once plans 1–5 above are completed, proceed to **PLAN-DOCS-MASTER.md** for document-related features (Static Document Templates, Dynamic Document Templates, Document Set Templates, etc.). See PLAN-DOCS-MASTER.md for the implementation sequence.

---

*To recreate this app from scratch: implement plans 1–5 in order, following each plan's implementation order and verification steps. Then implement the plans in PLAN-DOCS-MASTER.md.*

# Design: Core Business Domain (Vehicles, Contacts, Deals)

This document captures the design for the **core business domain** of the lease origination application: **Vehicles**, **Contacts**, **DealType**, and **Deals**. It defines the entities, their relationships, and the shared UI and workflow conventions. Implementation follows **PHASE-PLANS-BIZ-DOMAIN.md** and the individual **10-PLAN-ADD-VEHICLES.md**, **20-PLAN-ADD-CONTACTS.md**, and **30-PLAN-ADD-DEALS.md**.

**Related designs:** **../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md** defines the deal-centric schema and `get_deal_data(deal)` that consume this domain. **../06-DOCS/DESIGN-DOCS.md** assumes Deals (and Deal Type) exist and uses them for document sets and signing.

**Knowledge:** **../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md** describes the general pattern (products, customers, deals, document-centric flow) that this domain instantiates. **KNOWLEDGE-LEASE-JETPACKS.md** describes this application’s domain (vehicle leasing, jet packs, business objects, terminology).

---

## Scope

- **Domain entities** — Vehicle, Contact, DealType, Deal: what they represent, their properties, and how they relate.
- **Deal-centric workflow** — The deal is the central object for lease origination; vehicles and contacts are managed independently and associated with deals via ManyToMany.
- **UI conventions** — Shared patterns for list, add, edit, delete; for Deals, the View/Edit split (list → View detail → Edit/Delete from detail).
- **Deal type** — Single classification for v1 ("Lease - Single Signer"); used for document-set template association later (DESIGN-DOCS). Not shown in user-facing forms.

This design does not cover Images, the data schema interface, document templates, or SIGNiX; those are in their respective DESIGN and PLAN files.

---

## Current Platform (Assumed)

This design assumes only **../01-BASELINE/10-PLAN-BASELINE.md** is implemented (see **../01-BASELINE/DESIGN-BASELINE.md** and **../GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md** for baseline design and capabilities):

- Django project, venv, users app with LeaseOfficerProfile.
- Auth (login/logout), base templates (base.html, base_plain.html), profile view/edit.
- Initial user (e.g. karl) and Admin (Jazzmin).

The business domain plans add **apps.vehicles**, **apps.contacts**, and **apps.deals** and extend the sidebar. They do not replace or modify baseline.

---

## 1. Domain Model and Relationships

### 1.1 Entities

| Entity    | Purpose |
|----------|---------|
| **Vehicle** | A leaseable asset (in this app, jet packs). Identified by SKU, year, and JPIN. Managed in a standalone list; associated with deals via M2M. |
| **Contact** | A person (e.g. lessee, co-signer) with name, email, and phone. Managed in a standalone list; associated with deals via M2M. |
| **DealType** | A classification for a deal (e.g. "Lease - Single Signer"). Used to determine which document set template applies (DESIGN-DOCS). One type in v1; not user-selectable in forms. |
| **Deal** | A lease origination record: dates, payment, deposit, insurance, governing law; one lease officer (User), one deal type, zero-to-many vehicles, zero-to-many contacts. The primary object for the user workflow and for document generation. |

### 1.2 Relationship Table (Agreed)

| Relationship       | Shape | Notes |
|--------------------|-------|--------|
| **Deal → User (lease officer)** | **ForeignKey on Deal** (`lease_officer`) | One deal has one lease officer. Default to current user when creating. |
| **Deal → DealType** | **ForeignKey on Deal** (`deal_type`) | One deal has one deal type. Default to "Lease - Single Signer"; not shown in forms. |
| **Deal → Vehicles** | **ManyToMany on Deal** (`vehicles`) | Zero-to-many vehicles per deal. |
| **Deal → Contacts** | **ManyToMany on Deal** (`contacts`) | Zero-to-many contacts per deal (e.g. lessee, co-signer). |

Vehicles and Contacts have **no** direct relationship to each other. They are linked only through Deals. Implement **Vehicles** and **Contacts** before **Deals** so the Deal form can offer multi-select for both.

### 1.3 Why Deal-Centric

- Documents are generated **for a deal** (DESIGN-DOCS, DESIGN-DATA-INTERFACE). The internal schema and `get_deal_data(deal)` use Deal as the root; vehicles and contacts are reached via `deal.vehicles` and `deal.contacts`.
- The user workflow centers on creating and viewing deals; vehicles and contacts are supporting data managed in their own lists and attached to deals when needed.

---

## 2. Entity Properties (Summary)

**Vehicle** — `sku` (CharField), `year` (CharField), `jpin` (CharField, unique). Conventions: docstrings, `__str__`, verbose_name in Meta.

**Contact** — `first_name`, `middle_name` (optional/blank), `last_name`, `email`, `phone_number`. Conventions: docstrings, `__str__` (full name), verbose_name in Meta.

**DealType** — `name` (CharField, unique). One default "Lease - Single Signer" created by migration; `DealType.get_default()` returns it (get_or_create). Used when creating deals and for document set template association.

**Deal** — **Relations:** `lease_officer` (FK to User), `deal_type` (FK to DealType), `vehicles` (M2M, blank=True), `contacts` (M2M, blank=True). **Properties:** `date_entered`, `lease_start_date`, `lease_end_date`, `payment_amount`, `payment_period`, `security_deposit`, `insurance_amount`, `governing_law`. Default deal type set in `Deal.save()` and in the add view when `deal_type_id` is None. Conventions: docstrings, `__str__`, verbose_name in Meta; list views order by `-date_entered` or `-id`.

Full field specs, migrations, and seed data are in the individual plan files (**10-PLAN-ADD-VEHICLES.md**, **20-PLAN-ADD-CONTACTS.md**, **30-PLAN-ADD-DEALS.md**).

---

## 3. UI and Workflow Conventions

### 3.1 Shared Conventions (Vehicles, Contacts, Deals)

- **Access** — Authenticated users only (`@login_required`). No per-entity permissions in v1; any logged-in user can manage vehicles, contacts, and deals.
- **List page** — Table with relevant columns and an **Actions** column (View where applicable, Edit, Delete or link to delete confirmation).
- **Add** — Dedicated add URL (e.g. `/vehicles/add/`); form; redirect to list or detail on success.
- **Edit** — Dedicated edit URL (e.g. `/vehicles/<id>/edit/`); form with existing data; redirect on success.
- **Delete** — Dedicated confirmation page: GET shows "Are you sure?" with object summary; POST performs delete. No inline delete without confirmation.
- **Sidebar** — Each entity has a sidebar link. Order: Profile → Vehicles → Contacts → Deals → … (then Images, Schema, etc. per ../70-PLAN-MASTER.md). Use base template and existing layout (e.g. Jazzmin custom_links or equivalent).
- **Templates** — Use `base.html`; consistent layout and styling with profile and baseline.

### 3.2 View/Edit Split (Deals Only)

Deals use a **View/Edit split** so that the primary way to open a deal is **View** (read-only detail), not Edit:

- **List** — Table has **View** (primary link to deal detail) and **Delete**. No Edit button on the list.
- **Deal detail** — Read-only summary at `/deals/<pk>/`. Buttons: **Back** (to list), **Edit**, **Delete**. This page is the natural place for the **Documents** section (added by PLAN-ADD-DOCUMENT-SETS) and for **Send for Signature** (DESIGN-SIGNiX-SUBMIT).
- **Flow** — List → View (detail) → Edit or Delete from detail.

Rationale: Separates viewing from editing and gives a stable detail page for documents and signing. DESIGN-DOCS and DESIGN-SIGNiX-SUBMIT assume this structure.

### 3.3 Deal Type in the UI

Deal type is **not** shown in add/edit forms. It is set automatically (default "Lease - Single Signer"). The deal list and deal detail may show the deal type as read-only information. Document Set Templates are associated with Deal Type (DESIGN-DOCS); the single type in v1 is sufficient for that association.

---

## 4. Seed Data and Setup

- **Vehicle** — One initial vehicle (e.g. Skyward Personal Jetpack P-2024, 2024, JPIN as specified in PLAN-ADD-VEHICLES) via idempotent management command (e.g. `setup_initial_vehicle`).
- **Contact** — One initial contact (e.g. Max Danger Fun, email, phone as specified in PLAN-ADD-CONTACTS) via idempotent management command (e.g. `setup_initial_contact`).
- **DealType** — One type "Lease - Single Signer" created by migration (RunPython) so `migrate` is self-contained. Optional management command `setup_initial_deal_type` for manual setup.

Seed data supports demos and testing; the app does not depend on it for core logic.

---

## 5. Implementation Order and References

- **Order** — Implement **Vehicles** first, then **Contacts**, then **Deals**. See **PHASE-PLANS-BIZ-DOMAIN.md** for the full sequence and deliverables.
- **Source of truth for implementation** — **10-PLAN-ADD-VEHICLES.md**, **20-PLAN-ADD-CONTACTS.md**, **30-PLAN-ADD-DEALS.md** (model fields, URLs, batch steps, verification).
- **../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md** — Assumes this domain exists; defines deal-centric schema and `get_deal_data(deal)` using Deal, Vehicle, Contact, User.
- **../06-DOCS/DESIGN-DOCS.md** — Assumes Deals and Deal Type exist; document sets and templates are associated with deals and deal type.

---

## Decisions Log

### Deal-centric model

The deal is the central object. Vehicles and contacts are first-class entities with their own CRUD but are used in the app primarily as members of a deal’s vehicles and contacts. The data interface (DESIGN-DATA-INTERFACE) and document features (DESIGN-DOCS) reflect this: schema and document context are deal-rooted.

### View/Edit split for Deals

Deals use a read-only detail page as the primary entry from the list; Edit and Delete are on the detail page. This provides a stable place for the Documents section and Send for Signature and avoids editing from the list.

### Deal type not in forms

Deal type is set automatically to the single v1 value ("Lease - Single Signer"). It is used for document set template association (DESIGN-DOCS); exposing it in forms can be a later extension when multiple deal types exist.

### Shared UI conventions

Vehicles, contacts, and deals share the same patterns: list with table, add/edit forms, delete with confirmation page, sidebar link, authenticated-only access. Consistency simplifies implementation and user experience.

### Seed data via management commands (Vehicle, Contact) and migration (DealType)

Vehicle and Contact seeds are idempotent management commands so they can be run at any time. DealType is created in a migration so the schema and default type exist after `migrate`; optional command for manual re-run. See individual PLANs for exact commands and data.

---

*End of design. Implementation follows PHASE-PLANS-BIZ-DOMAIN.md and the individual 10-PLAN-ADD-VEHICLES.md, 20-PLAN-ADD-CONTACTS.md, and 30-PLAN-ADD-DEALS.md. See ../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md for schema and deal data; ../06-DOCS/DESIGN-DOCS.md for documents and signing.*

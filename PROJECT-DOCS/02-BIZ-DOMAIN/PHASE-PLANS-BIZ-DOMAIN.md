# Phase Plans: Business Domain — Implementation Order

**Status:** Complete. The three plans in this phase plans document (Vehicles, Contacts, Deals) have been implemented and are part of the current codebase.

This document defines the order in which to implement the **core business domain entities** of the lease application: **Vehicles**, **Contacts**, and **Deals**. Each plan adds one or more domain models, seed data where specified, and the standard management UI (list, add, edit, delete with confirmation). Deals depend on Vehicles and Contacts (ManyToMany), so Vehicles and Contacts are implemented first.

**Design:** For entity relationships, deal-centric workflow, and UI conventions, see **DESIGN-BIZ-DOMAIN.md**.

**Knowledge:** **../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md** describes the general pattern (products, customers, deals); **KNOWLEDGE-LEASE-JETPACKS.md** describes this application’s domain (vehicle leasing, jet packs). The design and plans implement that pattern for this codebase.

**Usage:** Implement each plan below in sequence. Within each plan, follow its Implementation Order (Section 6) and Batches/Verification (Section 6a). Do not skip ahead—later plans depend on earlier ones.

**Source of truth:** The individual plan files (10-PLAN-ADD-VEHICLES.md, 20-PLAN-ADD-CONTACTS.md, 30-PLAN-ADD-DEALS.md). Refer to them for model fields, seed data, URLs, and batch steps.

---

## Prerequisites

- **../01-BASELINE/10-PLAN-BASELINE.md** (70-PLAN-MASTER.md plan 1) is implemented: Django project, users app with LeaseOfficerProfile, auth (login/logout), base templates, profile view/edit, initial user, and Admin. The biz domain plans add new apps under `apps/` and extend the sidebar; they do not replace baseline.

---

## 1. 10-PLAN-ADD-VEHICLES.md

**Purpose:** Add the **Vehicles** (jet packs) entity—model, list page, and full CRUD so users can manage vehicles before associating them with deals.

**Deliverables:**
- **App** — New app `apps.vehicles` with `name = "apps.vehicles"` in AppConfig.
- **Model** — `Vehicle` with `sku`, `year`, `jpin` (CharField; jpin unique). Conventions: docstrings, `__str__`, verbose_name in Meta.
- **Seed** — One initial vehicle (Skyward Personal Jetpack P-2024, 2024, JPIN 4CH8P4K7E3X6Z9R2V) via idempotent management command (e.g. `setup_initial_vehicle`).
- **UI** — List page `/vehicles/` (table: SKU, Year, JPIN, Actions); Add `/vehicles/add/`, Edit `/vehicles/<id>/edit/`, Delete via dedicated confirmation page (GET confirm, POST delete). Sidebar link "Vehicles" (e.g. after Profile, before Admin).
- **Access** — Authenticated users only (`@login_required`).

**Dependencies:** None (only baseline).

**Implement:** Batch 1 (app, model, migrations, seed command); Batch 2 (forms, views, URLs, templates, sidebar, optional admin). See 10-PLAN-ADD-VEHICLES.md Section 6 and Section 6a.

---

## 2. 20-PLAN-ADD-CONTACTS.md

**Purpose:** Add the **Contacts** entity—model, list page, and full CRUD so users can manage contacts before associating them with deals.

**Deliverables:**
- **App** — New app `apps.contacts` with `name = "apps.contacts"` in AppConfig.
- **Model** — `Contact` with `first_name`, `middle_name` (optional/blank), `last_name`, `email`, `phone_number`. Conventions: docstrings, `__str__` (full name), verbose_name in Meta.
- **Seed** — One initial contact (Max Danger Fun, signixkarl@gmail.com, 9197440153) via idempotent management command (e.g. `setup_initial_contact`).
- **UI** — List page `/contacts/` (table: First Name, Middle Name, Last Name, Email, Phone Number, Actions); Add `/contacts/add/`, Edit `/contacts/<id>/edit/`, Delete via dedicated confirmation page (GET confirm, POST delete). Sidebar link "Contacts" (e.g. after Vehicles, before Admin).
- **Access** — Authenticated users only (`@login_required`).

**Dependencies:** None (only baseline). Implement after Vehicles so sidebar order is consistent (Profile → Vehicles → Contacts → …).

**Implement:** Batch 1 (app, model, migrations, seed command); Batch 2 (forms, views, URLs, templates, sidebar, optional admin). See 20-PLAN-ADD-CONTACTS.md Section 6 and Section 6a.

---

## 3. 30-PLAN-ADD-DEALS.md

**Purpose:** Add **Deals** (lease origination records)—DealType and Deal models, list/detail/add/edit/delete, and the **View/Edit split** so the deal detail page is the primary entry point and the natural place for the Documents section (added later).

**Deliverables:**
- **App** — New app `apps.deals` with `name = "apps.deals"` in AppConfig.
- **Models** — `DealType` (name; `get_default()` returning "Lease - Single Signer", created by migration). `Deal`: ForeignKey to User (lease_officer), ForeignKey to DealType (deal_type), ManyToMany to Vehicle (vehicles), ManyToMany to Contact (contacts); properties: date_entered, lease_start_date, lease_end_date, payment_amount, payment_period, security_deposit, insurance_amount, governing_law. Default deal type set in `Deal.save()` and in add view.
- **Seed** — Deal Type "Lease - Single Signer" created by migration (RunPython). Optional `setup_initial_deal_type` command.
- **UI** — List `/deals/` (table with View, Delete per row; no Edit on list). **Deal detail** `/deals/<pk>/` (read-only summary; Back, Edit, Delete; placeholder for Documents section). Add `/deals/add/`, Edit `/deals/<id>/edit/`, Delete via dedicated confirmation page (GET confirm, POST delete). **View/Edit split:** list links to detail via View; Edit and Delete are on the detail page. Sidebar link "Deals" (e.g. after Contacts, before Admin).
- **Form note** — Date fields on add/edit: use `{{ form.<date_field>.value|date:'Y-m-d'|default:'' }}` so `<input type="date">` displays correctly on edit (Section 4.6 of plan).
- **Access** — Authenticated users only; lease officer defaults to `request.user` on create.

**Dependencies:** Plan 1 (Vehicles) and Plan 2 (Contacts)—Deal has M2M to Vehicle and Contact. ../01-BASELINE/10-PLAN-BASELINE.md provides User and base templates.

**Implement:** Batch 1 (app, DealType and Deal models, migrations with DealType seed); Batch 2 (forms with vehicles/contacts multi-select, views, URLs, templates, sidebar, optional admin). See 30-PLAN-ADD-DEALS.md Section 6 and Section 6a.

---

## Summary Table

| Order | Plan | Key deliverables |
|-------|------|------------------|
| 1 | 10-PLAN-ADD-VEHICLES.md | apps.vehicles, Vehicle model (sku, year, jpin), CRUD + list, seed jet pack, sidebar |
| 2 | 20-PLAN-ADD-CONTACTS.md | apps.contacts, Contact model (first_name, middle_name, last_name, email, phone_number), CRUD + list, seed contact, sidebar |
| 3 | 30-PLAN-ADD-DEALS.md | apps.deals, DealType + Deal (lease_officer, deal_type, vehicles M2M, contacts M2M, properties), View/Edit split, CRUD, sidebar |

---

## Dependency Overview

```
Plan 1 (Vehicles: model, CRUD, seed)
        |
        v
Plan 2 (Contacts: model, CRUD, seed)
        |
        v
Plan 3 (Deals: DealType, Deal with M2M to Vehicle and Contact, View/Edit split, CRUD)
```

Deals require Vehicle and Contact to exist so the Deal form can offer multi-select for vehicles and contacts. Implement in order 1 → 2 → 3.

---

## Relation to 70-PLAN-MASTER.md

**70-PLAN-MASTER.md** treats this group as a single step (plan 2 in the main sequence). Implement ../01-BASELINE/10-PLAN-BASELINE.md first, then implement the three plans in this document in order. After PHASE-PLANS-BIZ-DOMAIN, proceed to ../03-IMAGES/10-PLAN-ADD-IMAGES.md (70-PLAN-MASTER.md plan 3) and ../04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md (70-PLAN-MASTER.md plan 4).

---

*To implement the core business domain: ensure ../01-BASELINE/10-PLAN-BASELINE.md is complete, then implement 10-PLAN-ADD-VEHICLES.md, 20-PLAN-ADD-CONTACTS.md, and 30-PLAN-ADD-DEALS.md in that order, following each plan’s Section 6 and Section 6a.*

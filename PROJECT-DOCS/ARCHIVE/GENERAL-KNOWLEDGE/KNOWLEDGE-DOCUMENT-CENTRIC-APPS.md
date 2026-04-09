# Knowledge: Document-Centric Business Applications (Template Pattern)

This document describes the **general pattern** that this project implements: an application that provides a UI for employees to manage **products** (or catalog), **customers** (or contacts), and **deals** (or cases/transactions), and that concludes with **document generation** and **electronic signing**. The pattern is reusable across many domains—wealth management onboarding, bank account opening, personal or commercial loans, equipment or vehicle leasing, installment plans for health procedures, and similar document-centric business processes.

**This project as template:** The codebase is structured so it can be adapted to other domains. The *architecture* (baseline, core business domain, images, data interface, document templates, signing integration) stays the same; the **business domain** (what counts as a product, a customer, a deal) changes per use case. The pattern **assumes a baseline** (authentication, user profile with timezone, app shell, admin, initial user) documented in [KNOWLEDGE-APP-FOUNDATION.md](KNOWLEDGE-APP-FOUNDATION.md) and [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md); [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md) is the Django implementation of that baseline. For the concrete instantiation in this repo (vehicle leasing, jet packs), see [02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md](../02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md). For this application’s design decisions, see [02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md](../02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md), [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md), and the PLAN files.

**Why these patterns are explicit:** In many document-centric applications, the way data is mapped to templates, how templates generate documents, how text tagging is configured, how deals are tied to document sets, how documents are versioned, and how the signing provider is integrated are **muddled with business logic**. That makes the application hard to maintain and hard for developers in a *different* business domain to learn from or empathize with. In this project, these six patterns are **explicit and separate** from the leasing domain: **(1)** data-to-template mapping is a clear layer (data interface, mapping UI); **(2)** templates are used to generate documents via a defined flow; **(3)** text tagging is configured (e.g. in tagging_data), not hardcoded; **(4)** deals are associated with document set templates via deal type (configuration, not hardcoded logic); **(5)** documents are modeled as instances with versions (draft, submitted, final); **(6)** the SIGNiX integration is a general interface not bundled with business logic. The design and plan documents describe these patterns so that they remain maintainable and learnable across domains. See [40-REQUIREMENTS.md](../40-REQUIREMENTS.md) (R-R4), [20-APPROACH.md](../20-APPROACH.md) (Principles), and [10-PROJECT-PITCH.md](../10-PROJECT-PITCH.md) (Design goals) for the full statement.

---

## 1. The Pattern in Plain Language

Many business processes share the same shape:

1. **An employee** (e.g. loan officer, wealth advisor, lease officer, account opener) works in an internal application.
2. They **manage a catalog** of what the organization offers—products, account types, loan products, leaseable assets, etc.
3. They **manage people**—customers, clients, applicants, co-signers—who will be parties to transactions or agreements.
4. They **create and manage deals** (or cases, applications, transactions)—each deal represents one “instance” of the process: one onboarding, one account opening, one loan, one lease. A deal links to one or more catalog items and one or more people.
5. When the deal is ready, **documents** are generated from the deal’s data (and from templates that define what documents are needed for that type of deal).
6. Those documents are **sent for signature**—customers and often the employee (or other authorized staff) sign electronically. When signing is complete, the application stores the final, signed documents.

The application’s job is to provide the **UI and data model** for steps 2–4 and to **orchestrate** steps 5–6 (document generation and signing) so that the employee has a single place to enter data, generate documents, and track signing.

---

## 2. Three Pillars: Products, Customers, Deals

Across domains, the pattern reduces to three conceptual pillars and their relationships.

### 2.1 Products (or catalog)

- **What it is:** The set of things the organization “sells” or offers—funds, account types, loan products, leaseable assets (vehicles, equipment), health procedure packages, etc.
- **Who manages it:** Typically internal staff (and sometimes admins). Data is entered once and reused across many deals.
- **Relationship to deals:** A deal references one or more products (e.g. “this lease is for these two vehicles”; “this account opening is for this product type”). So products exist **independently** and are **associated** with deals (often ManyToMany).
- **In this template:** Implemented as a “products” or domain-specific entity (e.g. **Vehicles** in the lease app). Same CRUD pattern: list, add, edit, delete; sidebar; authenticated users.

### 2.2 Customers (or contacts, parties)

- **What it is:** The people who are parties to the deal—applicants, signers, co-signers, guarantors. They may be external (customer, client) or internal (employee as signer).
- **Who manages it:** Staff enter and maintain contact/customer records; when creating or editing a deal, they attach the relevant people to that deal.
- **Relationship to deals:** A deal references one or more people (e.g. primary applicant + co-signer; lease officer + lessee). So customers/contacts exist **independently** and are **associated** with deals (often ManyToMany).
- **In this template:** Implemented as **Contacts** (or “customers” in another domain). Same pattern: list, add, edit, delete; attach to deals via multi-select or equivalent.

### 2.3 Deals (or cases, transactions, applications)

- **What it is:** The central “transaction” or “case”—one onboarding, one account opening, one loan application, one lease. It has **properties** (dates, amounts, terms) and **relationships** (which products, which people, which employee is responsible).
- **Who manages it:** The employee creates the deal, fills in properties, attaches products and people, and drives the workflow toward document generation and signing.
- **Relationship to products and customers:** The deal **has** links to products and customers (and often to an “owner” or “officer” user). It is the **root object** for document generation: “Generate documents for *this* deal” means use this deal’s data and its linked products and people.
- **In this template:** Implemented as **Deals** (with an optional **DealType** or classification so different deal types can trigger different document sets). The deal detail page is the natural place for “Documents” and “Send for Signature.”

### 2.4 Deal type (classification)

- **What it is:** A classification of the deal (e.g. “Lease - Single Signer”, “Account Opening - Joint”, “Loan - Personal”). Used to decide **which document set template** applies (which documents to generate, in what order, with which signer slots).
- **Relationship:** One deal has one deal type (ForeignKey). Deal type is often set by default or by workflow, not by free user choice in v1.

---

## 3. How the UI Supports the Pattern

- **Lists and CRUD:** Each pillar has a list page (table) and full CRUD: add, edit, delete (with confirmation). Sidebar links so the employee can jump to Products, Customers, or Deals.
- **Deal-centric workflow:** From the **Deals** list, the employee opens a deal (e.g. “View” to a read-only detail page). On the deal detail page they see properties, linked products, linked people, and—once document features are built—a **Documents** section (generate, regenerate, send for signature). So the **deal** is the hub; products and customers are managed elsewhere and attached to the deal.
- **View/Edit split for deals:** The deal **list** links to the deal **detail** (View). Edit and Delete live on the detail page. That keeps a stable “deal view” for documents and signing and avoids editing from the list.
- **Access:** Typically authenticated employees only; no per-entity permissions in the minimal template. Role-based access can be added later.

---

## 4. From Data to Documents to Signing

1. **Data entry** — Employee enters deal data and attaches products and people. The application stores everything in a structured way (deal-centric schema).
2. **Schema and deal data** — A **data interface** (e.g. `get_deal_data(deal)`) returns the full deal-centric structure (deal properties + linked products + linked people + officer) in a consistent, JSON-friendly shape. Document templates use this as the **single source** for populating documents. See [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) in this repo.
3. **File assets (images)** — Uploaded images (or other assets) are stored with stable URLs or identifiers so templates can reference them (e.g. logos). See [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) and [KNOWLEDGE-FILE-ASSETS-MEDIA.md](KNOWLEDGE-FILE-ASSETS-MEDIA.md).
4. **HTML-to-PDF** — Rendered HTML from dynamic templates is converted to PDF (e.g. wkhtmltopdf + pdfkit) before storage. See [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md) and [KNOWLEDGE-HTML-TO-PDF.md](KNOWLEDGE-HTML-TO-PDF.md).
5. **Document templates** — The organization defines **static** templates (e.g. PDFs with form fields) and **dynamic** templates (e.g. HTML with placeholders mapped to deal data). **Document set templates** say “for this deal type, generate these documents in this order.” See [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md).
6. **Document set** — For a given deal, the app creates a **document set** from the document set template: it generates or attaches the documents and populates them with `get_deal_data(deal)`. The employee can regenerate if deal data changes.
7. **Signing** — When ready, the employee sends the document set for signature. Signers (derived from the deal’s people and from template configuration) receive the documents and sign electronically. The app tracks status and, when complete, stores the signed documents. See [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md), [09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md](../09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md), and [KNOWLEDGE-SIGNiX.md](KNOWLEDGE-SIGNiX.md) in this repo.

---

## 5. Using This Project as a Template for Another Domain

- **Keep:** Baseline (auth, users, base templates), the *structure* of a business domain (three pillars: products, customers, deals), the data interface pattern (deal-centric schema, `get_deal_data`), document templates and document sets, signing integration (SIGNiX or another provider).
- **Replace / rename:** The **business domain** itself. For example:
  - **Wealth management onboarding:** Products = funds/products; Customers = clients; Deals = onboarding cases (with type, e.g. individual vs joint).
  - **Bank account opening:** Products = account types; Customers = applicants/co-owners; Deals = account applications.
  - **Personal loans:** Products = loan products; Customers = borrowers/co-signers; Deals = loan applications.
  - **Equipment leasing:** Products = equipment (like Vehicles in this app); Customers = lessees/guarantors; Deals = lease deals.
  - **Health procedure installments:** Products = procedures/packages; Customers = patients/guarantors; Deals = payment plans or agreements.

Rename apps and models to match the domain (e.g. `apps.vehicles` → `apps.equipment`, `Vehicle` → `Equipment`, `Deal` → `OnboardingCase`). The *pattern*—list/CRUD for each pillar, deal-centric detail page, document set from deal type, signing—stays the same. DESIGN-BIZ-DOMAIN and PHASE-PLANS-BIZ-DOMAIN in this repo describe how we implemented the pattern for **one** domain (vehicle leasing); use them as a reference and reimplement the domain layer for your own products, customers, and deals.

---

## 6. References in This Repo

Design and plan documents in this repo are aligned with this pattern: **designs** specify decisions consistent with the knowledge; **plans** specify implementation steps that realize the designs. The following documents implement or extend this pattern for the lease application and its document/signing features.

| Document | Content |
|----------|---------|
| [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md) | Application baseline: auth, profile (with timezone), app shell, admin integration, initial user. |
| [02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md](../02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md) | This application’s core domain design (Vehicles, Contacts, Deals, DealType) and UI conventions. |
| [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) | Deal-centric schema and `get_deal_data(deal)` for document population and debugging. |
| [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) | Document templates, document sets, and workflow toward signing. |
| [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) | Image (file asset) upload, stable URLs, how document features consume images; extension point for DMS. |
| [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) | Submitting document sets for signature (SIGNiX). |
| [09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md](../09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md) | Push, status sync, download, and transaction detail. |
| [KNOWLEDGE-APP-FOUNDATION.md](KNOWLEDGE-APP-FOUNDATION.md) | Baseline capabilities (auth, profile with timezone, app shell, admin, initial user); technology-agnostic; Django implementation in PLAN-BASELINE. |
| [KNOWLEDGE-FILE-ASSETS-MEDIA.md](KNOWLEDGE-FILE-ASSETS-MEDIA.md) | File upload and storage without a DMS; stable URLs; when to use a DMS. |
| [02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md](../02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md) | This application’s domain: vehicle leasing (jet packs), business objects, and terminology. |
| [KNOWLEDGE-HTML-TO-PDF.md](KNOWLEDGE-HTML-TO-PDF.md) | HTML-to-PDF for document generation; wkhtmltopdf and pdfkit; constraints and alternatives. |
| [KNOWLEDGE-SIGNiX.md](KNOWLEDGE-SIGNiX.md) | SIGNiX Flex API and integration reference. |
| [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) | Implementation order for the full stack; PHASE-PLANS-BIZ-DOMAIN for the core domain. Document generation enablers (plans 3–4 + SETUP-WKHTMLTOPDF): DESIGN-DATA-INTERFACE, DESIGN-IMAGES, SETUP-WKHTMLTOPDF; knowledge in KNOWLEDGE-FILE-ASSETS-MEDIA and KNOWLEDGE-HTML-TO-PDF. |
| [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md) | Setup for wkhtmltopdf + pdfkit before dynamic document generation; run after plans 1–4, before PHASE-PLANS-DOCS. See [KNOWLEDGE-HTML-TO-PDF.md](KNOWLEDGE-HTML-TO-PDF.md) for background. |

---

*This knowledge file describes the **pattern** of document-centric business applications. For the concrete business objects and terminology in the lease/jet-pack application, see [02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md](../02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md).*

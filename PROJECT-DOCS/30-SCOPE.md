# Scope — Lease Origination Sample Application

This document states **what is in scope** and **what is out of scope** for this version of the lease origination sample application. It complements [40-REQUIREMENTS.md](40-REQUIREMENTS.md) (what the system must do) and [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) (why we are doing the project). Scope is **outlined** during Ideation (to support the pitch) and **tightened** during the Design phase, per the project lifecycle in [20-APPROACH.md](20-APPROACH.md) (Section 5.5). Scope may be revised when we add or defer features; approach is in [20-APPROACH.md](20-APPROACH.md).

---

## 1. In Scope (This Version)

### 1.1 Application capabilities

- **Baseline**: Authentication (login, session, logout), user profile (display name, contact, timezone), app shell (sidebar + content; minimal layout for login/logged-out), admin area (user management, configuration), initial user via idempotent setup. *(See REQUIREMENTS R-B1–R-B5.)*
- **Business domain**: Vehicles, contacts, deals (including deal type), with full CRUD, list, and deal detail (view) with edit/delete. Deal links to lease officer, deal type, vehicles (M2M), contacts (M2M). *(See REQUIREMENTS R-D1–R-D4.)*
- **Images**: Upload, storage, stable URLs; CRUD and list. *(See REQUIREMENTS R-I1.)*
- **Data interface**: Internal schema and `get_deal_data(deal)`; schema viewer page; Debug Data page (deal list with View JSON). *(See REQUIREMENTS R-S1–R-S2.)*
- **Document templates**: Static (PDF with form fields) and dynamic (HTML with mapping); document set templates (ordered list, associated with deal type). *(See REQUIREMENTS R-T1–R-T3.)*
- **Document sets**: Generate, regenerate, delete; document instances and versions; view/download; status flow (draft → submitted to SIGNiX → final). *(See REQUIREMENTS R-T4.)*
- **Document generation**: HTML-to-PDF (wkhtmltopdf + pdfkit) for dynamic templates. *(See REQUIREMENTS R-G1.)*
- **SIGNiX integration**: Submit document set; signer identification and slot→person resolution; signers table on deal view (reorder, authentication); Send for Signature button; signature transactions dashboard and related transactions on deal view; push notifications (status and per-signer progress); download on complete (signed docs, audit trail, certificate); signature transaction detail page. *(See REQUIREMENTS R-X1–R-X7.)*

### 1.2 Documentation and template use

- **Documentation**: Knowledge, Design, and Plan documents that allow the application to be **recreated from scratch** and used as a **template** for other document-centric applications (e.g. personal loans, wealth management onboarding). *(See REQUIREMENTS R-R1–R-R3.)*
- **Engineering best practices**: Code maintainability, clarity, and structure—including no duplication (use helpers/services for shared logic) and separation of concerns (logic in services, views thin)—as defined in [20-APPROACH.md](20-APPROACH.md) are **in scope**; implementation should follow these expectations.
- **Requirements, scope, approach**: [40-REQUIREMENTS.md](40-REQUIREMENTS.md), 30-SCOPE.md, [20-APPROACH.md](20-APPROACH.md), and [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) so that stakeholders, scope, and approach are explicit and maintainable.

### 1.3 Deal type and domain

- **Single deal type** in this version (e.g. “Lease - Single Signer”); the design allows for additional deal types later. The application focuses on the **vehicle leasing (jet pack)** scenario as the concrete use case.

### 1.4 Deployment and environment

- **Development and demo**: The application is intended for development, demonstration, and reference use. SQLite is in scope for local/dev; production deployment, scaling, and hardening are out of scope for this version (see Section 2).

---

## 2. Out of Scope (This Version)

The following are **explicitly out of scope** for this version. They are not requirements (see [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5) and are not planned for implementation in the current PLAN set. They may be revisited in a later version or in a derivative project.

- **Role-based access control** — Fine-grained roles (e.g. viewer, editor, admin) beyond “staff can use the app and admin.”
- **Multi-tenancy** — Multiple organizations or tenants in one deployment.
- **Public or customer-facing portal** — Lessees do not log in to this application; they sign via SIGNiX-hosted flows.
- **Full audit trail of domain data** — Who created/updated vehicles, contacts, deals (beyond SIGNiX signing audit trail).
- **Alternative signing providers** — Integration with a provider other than SIGNiX.
- **Production hardening** — Production-grade deployment, high availability, backup/restore, compliance certifications (e.g. SOC2, HIPAA).
- **Multiple deal types in the UI** — We implement one deal type; adding more is a future extension.
- **API for third-party systems** — No requirement for a public REST or other API for external systems to create/read deals or documents.

---

## 3. Later / Future (Not Committed)

The following may be in scope for a **later version** or a **derivative project** but are not committed for this version:

- Additional deal types and document set templates.
- Refinements to signing flow (e.g. resend, cancel transaction, limit re-submissions).
- Optional validation or tooling (e.g. QueryTransactionStatus polling, push request validation).
- Role-based permissions or multi-tenancy if a future use case requires them.
- Public API for integration with other systems.

---

## 4. Template Use (When Reusing This Project)

When this project is used as a **template** for another document-centric application:

- **In scope to carry over**: Baseline (auth, profile, app shell, admin), the *structure* of the business domain (products, customers, deals), data interface pattern, document templates and document sets, signing integration pattern. Documentation (Knowledge, Design, Plan) and the requirements/scope/approach structure should be adapted for the new project.
- **Out of scope / replace**: The **business domain** itself (vehicles, contacts, deals for leasing) — replace with the new domain’s entities (e.g. loan products, borrowers, loan applications). SIGNiX may be replaced with another signing provider if the new project so chooses; the integration pattern (submit, status, download) remains applicable.
- **Scope for the new project**: The new project should define its own 30-SCOPE.md (and [40-REQUIREMENTS.md](40-REQUIREMENTS.md), 20-APPROACH.md) so that in/out of scope is clear for that application.

---

*What the system must do: [40-REQUIREMENTS.md](40-REQUIREMENTS.md). Why we are doing the project: [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md). How we build and document: [20-APPROACH.md](20-APPROACH.md). Work-breakdown and effort: [50-WBS.md](50-WBS.md), [60-LOE.md](60-LOE.md).*

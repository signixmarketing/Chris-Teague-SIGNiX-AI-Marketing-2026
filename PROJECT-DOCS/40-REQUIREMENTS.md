# Requirements — Lease Origination Sample Application

This document states the **requirements** for the lease origination sample application: what the system must do and satisfy so that the project meets the goals described in [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md). Requirements are written so that they can be verified; scope (what we build in which version) is in [30-SCOPE.md](30-SCOPE.md); approach (how we build and document) is in [20-APPROACH.md](20-APPROACH.md).

**Relationship to user profiles and value proposition:** Requirements should **consider and align with** the [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) document. Each persona's jobs, pains, and gains inform what the system must do; the "Maps to requirements" in that document provide traceability from value to requirements. When determining or updating requirements, ensure they serve the personas and the value proposition described there.

---

## 1. Context and Stakeholders

The application serves multiple stakeholders (see [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) for the full narrative):

- **Project lead** — Responsible for direction, technical research, best practices, and ensuring the application and documentation serve project goals (learning AI-powered development, creating a template for teaching, proving out SIGNiX integration, clarifying end-to-end usage).
- **Lease officers** — Primary users in the scenario; employees who manage vehicles, contacts, deals, generate documents, and send for signature.
- **Lessees (contacts)** — Second signers in the scenario; customers who sign documents.
- **System administrators** — Staff who configure the system (e.g. document templates, SIGNiX configuration); may be the same person as the lease officer in a small deployment.
- **Engineering and technical staff** — Consumers of the project for learning (AI-powered code generation, signature integration API usage).
- **Sales, support, and marketing staff** — Consumers of the application for demos and of content for education and promotion.
- **Third-party developers** — Consumers of the application as a reference implementation and of content for learning how to integrate with SIGNiX.
- **Future projects** — Consumers of the project as a template for other document-centric applications (e.g. personal loans, wealth management onboarding).

The application must satisfy the functional and non-functional requirements below so that it can be recreated from scratch, extended with new features, and used as a template for other document-centric applications.

---

## 2. Functional Requirements

### 2.1 Baseline (authentication, profile, app shell, admin)

- **R-B1** The system shall provide **authentication**: login, session, and logout. Only authenticated users shall access the main application; unauthenticated requests shall redirect to login.
- **R-B2** The system shall provide a **user profile** per user with display name (e.g. first, last, full), contact info (email, phone), and **timezone** (IANA) so that dates and times are shown in the user’s local time app-wide.
- **R-B3** The system shall provide a consistent **app shell** (e.g. sidebar + content area) for all main application pages. Login and logged-out pages shall use a minimal layout (no sidebar).
- **R-B4** The system shall provide an **admin (back-office)** area for user and configuration management, with navigation between the app and admin (e.g. “Back to app”, link to profile from admin).
- **R-B5** The system shall support **initial user setup** via a repeatable, idempotent step (e.g. management command or seed script) so that the application can be bootstrapped from scratch reliably.

### 2.2 Business domain (vehicles, contacts, deals)

- **R-D1** The system shall support **vehicles** (or equivalent catalog): create, read, update, delete; list with consistent UI; association with deals. In this application, vehicles represent leaseable assets (e.g. jet packs).
- **R-D2** The system shall support **contacts** (or equivalent parties): create, read, update, delete; list with consistent UI; association with deals. In this application, contacts represent lessees and other signers.
- **R-D3** The system shall support **deals** (or equivalent transactions): create, read, update, delete; list; **deal detail (view)** as the primary way to open a deal; edit and delete from the detail page. A deal shall link to a **deal type**, one or more vehicles, one or more contacts, and a **lease officer** (user). Deal properties (e.g. dates, payment, deposit, insurance, governing law) shall be stored and displayed.
- **R-D4** The system shall support at least one **deal type** (e.g. “Lease - Single Signer”) so that document set templates can be associated with deal types.

### 2.3 Images and file assets

- **R-I1** The system shall support **upload and storage of images** (or other file assets) with stable identifiers or URLs so that document templates can reference them (e.g. logos).

### 2.4 Data interface (schema and deal data)

- **R-S1** The system shall provide an **internal data schema** that describes the deal-centric data structure (deal, vehicles, contacts, lease officer) for mapping and document population.
- **R-S2** The system shall provide **deal data retrieval** (e.g. `get_deal_data(deal)`) that returns the full deal-centric structure in a consistent, JSON-friendly shape. Document templates shall use this as the **single source** for populating documents (no direct model traversal for population).

### 2.5 Document templates and document sets

- **R-T1** The system shall support **static document templates** (e.g. PDFs with form fields): upload, metadata (ref_id, description), and configuration of form field definitions (e.g. for SIGNiX tagging).
- **R-T2** The system shall support **dynamic document templates** (e.g. HTML with placeholders): upload, mapping of template variables to deal data or images, and text tagging (e.g. signature/date fields for SIGNiX).
- **R-T3** The system shall support **document set templates**: an ordered list of static and/or dynamic templates, associated with a deal type, so that “generate documents for this deal” uses the correct set of templates.
- **R-T4** The system shall support **document sets** per deal: generate documents from the deal’s document set template, regenerate when deal data changes, view and download documents, and delete document set. Document instances and versions shall be stored (e.g. draft, submitted to SIGNiX, final).

### 2.6 Document generation (HTML-to-PDF)

- **R-G1** The system shall convert **rendered HTML** (from dynamic templates) **to PDF** before storage (e.g. via wkhtmltopdf + pdfkit or equivalent) so that generated documents are PDFs.

### 2.7 Signing (SIGNiX integration)

- **R-X1** The system shall **submit a deal’s document set to SIGNiX** for signature (SubmitDocument flow): build payload from deal, document set, signers, and configuration; send to SIGNiX; store transaction identifier and first signer link; update document instance version status (e.g. “Submitted to SIGNiX”).
- **R-X2** The system shall **identify signers** from the document set template (e.g. signer slots from tagging_data) and **resolve slots to people** (e.g. slot 1 = lease officer, slot 2 = first contact). The user shall be able to **reorder signers** and set **authentication** per signer (e.g. SelectOneClick, SMSOneClick).
- **R-X3** The system shall provide a **Send for Signature** action on the deal detail page that triggers submit and opens the first signer’s signing URL (e.g. in a new window).
- **R-X4** The system shall maintain a **signature transactions dashboard** (list of submitted transactions with status, links) and a **related transactions** section on the deal detail page.
- **R-X5** The system shall support **push notifications** from SIGNiX (e.g. Send, partyComplete, complete, suspend, cancel, expire) and update transaction status and per-signer progress (e.g. “1/2”, “2/2”) so that the dashboard and deal view reflect current state.
- **R-X6** When a transaction **completes** (push action=complete), the system shall **download signed documents** from SIGNiX, store them as final document instance versions, and store the **audit trail** and **certificate of completion** on the transaction.
- **R-X7** The system shall provide a **signature transaction detail page** (link from dashboard and deal view) showing transaction info, signers, documents (as sent vs signed), event timeline, and links to view/download audit trail and certificate of completion.

### 2.8 Reference and template quality

- **R-R1** The application shall be **recognizable to a third-party developer** as a realistic example of an application that integrates with SIGNiX—i.e. the integration pattern (data → templates → generation → submit → dashboard/sync) shall be clear and accurate.
- **R-R2** The **documentation and structure** shall support **recreating the application from scratch** by following the project’s plans and design documents.
- **R-R3** The **documentation and structure** shall support using the project as a **template** for other document-centric applications (e.g. different business domain: personal loans, wealth management onboarding) so that someone can say “using this project as a template, make a project like this, but for X” and have a clear path to do so.
- **R-R4** The system and its documentation shall **make explicit and keep separate from business logic** the following patterns—so that they are maintainable and so that developers in other business domains can learn from and reuse them without domain-specific clutter:
  - **(a) Data-to-template mapping** — How application data is mapped to templates (e.g. schema paths → template variables) shall be a clear, documented layer, not ad-hoc code in business logic.
  - **(b) Use of templates to generate documents** — How templates are used to generate documents (template + data → output) shall be a defined flow, separable from domain logic.
  - **(c) Configurable text tagging** — Text tagging (e.g. signature/date fields for SIGNiX) shall be **configured** (e.g. in tagging_data), not hardcoded; no logic that encodes specific data or template structure shall be required to assign fields to signers or field types.
  - **(d) Deals and document set templates** — How deals are associated with document set templates (e.g. via deal type) shall be explicit; which documents apply to a deal shall be determined by configuration, not hardcoded business logic.
  - **(e) Documents as instances with versions** — Documents shall be modeled as **instances with versions** (e.g. draft, submitted to SIGNiX, final) so that the pattern is general and clear.
  - **(f) General SIGNiX interface** — The SIGNiX integration (build payload, send, push handling, download) shall be a **general interface** not bundled with business logic, so that it can be reused or adapted for other document-centric applications without domain-specific code.

---

## 3. Non-Functional Requirements

- **R-N1** The application shall be **demonstrable** in a sales or education context: it shall run, support the full lease-officer and lessee workflow, and show SIGNiX integration end-to-end without requiring production-scale infrastructure (e.g. SQLite for dev is acceptable).
- **R-N2** The application shall be **maintainable and extendable**: code and documentation shall be structured so that a developer (or project lead using AI-powered development) can add or change features in a disciplined way, with clear reference to design and knowledge documents. In particular: **avoid code duplication**—when the same functionality is needed in multiple places, implement it once in a **helper function or service** and call it from views or other code; put **business logic and integration logic** (e.g. SIGNiX payload building, document generation, schema discovery) in **services or dedicated modules** where appropriate, rather than in views or UI code; and maintain **clear separation of concerns** (UI focused on request/response and orchestration; business and integration logic in services or shared modules) so the codebase stays clear, testable, and easy to extend.
- **R-N3** Access to the main application shall be **authenticated users only**; there is no requirement for a public-facing or anonymous user experience in this version.

---

## 4. Constraints

- **R-C1** The application shall integrate with **SIGNiX** for electronic signing (Flex API, SubmitDocument, GetAccessLink, push notifications, DownloadDocument, ConfirmDownload) as the chosen provider for this project.
- **R-C2** The application shall be implemented using the **Django** framework and the **Python** ecosystem as specified in the project’s plans; technology choices are documented in [20-APPROACH.md](20-APPROACH.md).
- **R-C3** The application shall follow the **Knowledge → Design → Plan** documentation structure and the deal-centric pattern described in [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) so that requirements, scope, and approach remain aligned with the implementation.

---

## 5. Out of Scope / Not Requirements (This Version)

The following are **not** required for this version of the application; they may be in scope for a later version or a different project (see [30-SCOPE.md](30-SCOPE.md) for in/out of scope):

- **Role-based permissions** — No requirement for fine-grained roles (e.g. viewer, editor, admin) beyond staff access to the app and admin.
- **Multi-tenancy** — No requirement for multiple organizations or tenants in a single deployment.
- **Public or customer-facing portal** — No requirement for lessees to log in to the application; they sign via SIGNiX-hosted flows.
- **Full audit trail of data changes** — No requirement to record who changed what and when for domain data (vehicles, contacts, deals); SIGNiX provides signing audit trail.
- **Alternative signing providers** — No requirement to support a provider other than SIGNiX in this project.
- **Production hardening** — No requirement for production-grade deployment, scaling, backup, or compliance certifications in this version; the application is for reference, demo, and template use.

---

*Stakeholder and benefit narrative: [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md). User profiles and value proposition: [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md). What is in or out of scope for this version: [30-SCOPE.md](30-SCOPE.md). How we build and document: [20-APPROACH.md](20-APPROACH.md). Work-breakdown and effort: [50-WBS.md](50-WBS.md), [60-LOE.md](60-LOE.md).*

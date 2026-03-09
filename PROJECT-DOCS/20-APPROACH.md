# Approach — Lease Origination Sample Application

This document describes **how** we build and document the lease origination sample application: principles, technology choices, documentation structure, and conventions. It complements [40-REQUIREMENTS.md](40-REQUIREMENTS.md) (what the system must do), [30-SCOPE.md](30-SCOPE.md) (what is in or out of scope), and [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) (why we are doing the project). The approach is chosen to support recreating the application from scratch, extending it with new features, and using it as a template for other document-centric projects.

---

## 1. Principles

- **Deal-centric design** — The deal is the hub for documents and signing; products and contacts are managed independently and associated with deals.
- **Single source for document data** — Document features use the data interface (`get_deal_data`, schema) only; no direct model traversal for population. This keeps the mapping layer explicit and reusable.
- **Documentation as a first-class deliverable** — Knowledge, Design, and Plan documents are maintained so that the application can be recreated, extended, or reused as a template.
- **Idempotent and repeatable setup** — Initial user, seeds, and configuration can be run again without breaking state.
- **Batch-and-verify implementation** — Plans are executed in batches with verification steps so that progress is testable and reversible.
- **Separation of document and signing patterns from business logic** — The following patterns are kept **explicit and separate** from domain logic (vehicles, contacts, deals, leasing). When these patterns are muddled with business logic, the result is hard to maintain and hard for developers in a different business domain to learn from. This project makes them first-class:
  - **Data-to-template mapping** — How data is mapped to templates (e.g. schema paths → template variables) is a clear, documented layer (data interface, mapping UI), not ad-hoc code in business logic.
  - **Templates used to generate documents** — How templates are used to generate documents (template + data → rendered output → PDF) is a defined flow, separable from domain logic.
  - **Configurable text tagging** — Text tagging (signature fields, date-signed fields for SIGNiX) is **configured** (e.g. in tagging_data), not hardcoded; no logic encodes specific data or template structure to assign fields to signers.
  - **Deals and document set templates** — How deals are set up according to document template sets is explicit: deal type → document set template → ordered list of templates. Which documents apply is determined by configuration, not hardcoded business logic.
  - **Documents as instances with versions** — Documents are modeled as **instances with versions** (DocumentInstance, DocumentInstanceVersion; draft, submitted to SIGNiX, final) so that the pattern is general and clear—not one-off handling of “this PDF we generated.”
  - **General SIGNiX interface** — The SIGNiX integration (build payload, send, parse response, push handling, download) is a **general interface** not bundled with business logic, so that a developer in another domain (e.g. personal loans) can reuse or adapt it without wading through lease-specific code.
- **Code maintainability and structure** — Engineering best practices for maintainability, clarity, and code structure are expected. **Do not duplicate code** when the same functionality is needed in multiple places: create and use **helper functions or services** and call them from views or other code. Put logic that belongs outside the UI—e.g. data transformation, integration with external APIs, document generation, schema discovery—into **services or dedicated modules** rather than bloating views or forms. Views and UI code should focus on request/response handling and simple orchestration; **separation of concerns** (UI vs. business logic vs. integration) is an expectation so the codebase stays clear, testable, and easy to extend.

---

## 2. Documentation Structure

The project uses two levels of documentation: **project-level** documents that define intent, boundaries, and methodology before execution; and **phase-level** documents (Knowledge, Design, Plan) that are produced and updated as each phase is tackled. Section 6 describes the order in which these are created and used; this section describes what each layer is and how the documents relate.

### 2.1 Project-level documents

These documents are created early (pitch → scope → requirements → work-breakdown and level of effort) and are the basis for stakeholder review and approval before execution begins:

- [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) — Why the project exists, who it serves, what benefits are expected, what success looks like. Used to secure sponsorship and alignment.
- [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) — User profiles (personas) in the application scenario: jobs to be done, pains the system addresses, gains it delivers, and mapping to requirements. Supports product thinking and template reuse; when using the project as a template, replace these profiles with those for the new project.
- **20-APPROACH.md** (this document) — How we build and document: principles, documentation structure, technology choices, conventions, and the execution methodology (Section 6).
- [30-SCOPE.md](30-SCOPE.md) — What is in scope and out of scope for this version. Keeps requirements and phases focused and gives stakeholders shared expectations.
- [40-REQUIREMENTS.md](40-REQUIREMENTS.md) — What the system must do and satisfy; breaks the project into phases with clear boundaries and deliverables.
- [50-WBS.md](50-WBS.md) — Work-breakdown: all work on the project (architecture, knowledge, design, planning, implementation, documentation updates), organized by phase and work type. Used for planning, resource assignment, and GANTT-level views.
- [60-LOE.md](60-LOE.md) — Level of effort estimate aligned with the WBS; gives stakeholders and project managers a view of effort so they can confirm commitment or adjust scope.
- [70-PLAN-MASTER.md](70-PLAN-MASTER.md) — Implementation order (execution map); top-level sequence of phases and plans.
- [80-FUTURE-ROADMAP.md](80-FUTURE-ROADMAP.md) — Future roadmap: where to take the project after initial implementation; candidate priorities and themes (not committed).

Together these define **intent, boundaries, methodology, and planned work**. They do not specify implementation steps; that belongs in the phase-level Knowledge, Design, and Plan documents.

### 2.2 Phase-level: Knowledge → Design → Plan

Within each phase (e.g. baseline, business domain, document templates, signing integration), work follows three layers. Each layer has a distinct role:

- **Knowledge** — Topic-specific information that the implementer (or AI) needs to design, plan, and implement the phase. Knowledge documents consolidate concepts, constraints, and links to external resources (e.g. SIGNiX Flex API, wkhtmltopdf behavior). They are **technology-agnostic or domain-conceptual** where possible so they remain useful if the implementation choice changes. Examples: [GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md](GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md), [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md), [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md). **When to use:** Create or update a knowledge file when a phase depends on expertise that is not already captured or is scattered; do not move to design until the knowledge for the phase is in place.

- **Design** — Decisions and contracts for the phase: what the system will do, how components relate, what the implementation must satisfy. Designs do not prescribe every line of code—that belongs in the plan. They state *what* and *why*; plans state *how* and *in what order*. Examples: [01-BASELINE/DESIGN-BASELINE.md](01-BASELINE/DESIGN-BASELINE.md), [06-DOCS/DESIGN-DOCS.md](06-DOCS/DESIGN-DOCS.md), [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md). **When to use:** Write or update the design for the phase before any implementation; review until there are no open issues or unresolved decisions. Designs point to the plan(s) that will implement them and to relevant knowledge documents.

- **Plan** — The implementation work for the phase: steps grouped into **batches**, **verification steps** per batch, and **tests** (automated where possible; manual for the project lead where needed). A phase may have one plan (e.g. PLAN-BASELINE) or many, with a **phase plans document** (e.g. PHASE-PLANS-BIZ-DOMAIN, PHASE-PLANS-DOCS) defining the order. Examples: [01-BASELINE/10-PLAN-BASELINE.md](01-BASELINE/10-PLAN-BASELINE.md), [02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md](02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md), [07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md). **When to use:** Outline the implementation work after the design is stable; pressure-test the plans before implementation. Implementation then proceeds plan by plan, batch by batch. The top-level sequence of plans is in [70-PLAN-MASTER.md](70-PLAN-MASTER.md); within a phase, the phase plans document defines the order of its sub-plans. Many plans include an **"Open Issues" or "Implementation Decisions"** section; in this project these typically record **resolved or decided** items (e.g. design choices, gotchas, recommendations), not open blockers—readers should not assume listed items are still outstanding.

This order—Knowledge first, then Design, then Plan, then Implementation—is repeated for every phase. See Section 6.5 for the full sequence and Section 6.6 for the documentation feedback loop (updating plans, designs, and knowledge as implementation reveals new information).

### 2.3 Cross-references and navigation

Keeping the doc set navigable and consistent depends on explicit cross-references:

- **Plans** should point to their **Design** and **Knowledge** documents (e.g. in a plan’s header or prerequisites). That way anyone following the plan knows which design and knowledge apply.
- **Designs** should point to the **Plan(s)** that implement them and to relevant **Knowledge** documents. That way the design remains the single source of truth and implementers know which plans to follow.
- **Knowledge** documents may reference designs and plans where the pattern is implemented (e.g. KNOWLEDGE-DOCUMENT-CENTRIC-APPS lists DESIGN-* and PLAN-MASTER). Knowledge stays conceptual; the references help readers find the concrete application in this project.

When you add or change a document, update any references and **reference tables** (e.g. the document table in [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md)) so the set stays consistent and a new reader (or an AI) can find the right doc without guesswork. The gold standard in Section 6.7 depends on this.

---

## 3. Technology Choices

The following technology choices underpin the application. Rationale and concrete versions are documented in the plans (e.g. [01-BASELINE/10-PLAN-BASELINE.md](01-BASELINE/10-PLAN-BASELINE.md) Section 2, **requirements.txt**); this section summarizes the stack and why it was chosen.

- **Django and Python** — Django provides auth, admin, ORM, templates, and a standard project layout; it is widely used and well supported. Use a current **LTS** version (e.g. Django 5.x) with version pins in **requirements.txt** for reproducibility. Python version follows Django’s compatibility (e.g. Python 3.10+). See PLAN-BASELINE for the initial stack table.
- **SQLite** — Used for development and demo so the application runs without an external database. Suitable for reference, demonstration, and template use; production deployments may switch to PostgreSQL or another database.
- **Jazzmin** — Admin theme and sidebar menu for Django Admin. Provides a consistent look between the main app and the admin area and improves navigation. See PLAN-BASELINE.
- **SIGNiX Flex API** — The chosen provider for electronic signing. The application uses **SubmitDocument** (submit document set, get first-signer link), **GetAccessLink** (when the response does not include the link), **push notifications** (Send, partyComplete, complete, suspend, cancel, expire) for status and per-signer progress, and **DownloadDocument** plus **ConfirmDownload** for signed documents and artifacts (audit trail, certificate of completion). See [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) and the SIGNiX API documentation.
- **wkhtmltopdf and pdfkit** — HTML-to-PDF for dynamic document generation. wkhtmltopdf is installed on the system; pdfkit is the Python binding. Dynamic templates are rendered with Django templates, then converted to PDF before storage. See [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) and [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md).
- **Pillow** — Image handling and validation for the Images app (upload, storage, stable URLs). Required by the document template flow when templates reference images (e.g. logos). See [03-IMAGES/10-PLAN-ADD-IMAGES.md](03-IMAGES/10-PLAN-ADD-IMAGES.md) and [GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md](GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md).

Other dependencies (e.g. for testing or tooling) are listed in **requirements.txt** and called out in the relevant plans. When using this project as a template, you can substitute alternatives (e.g. a different signing provider or PDF library) provided the documentation and design are updated to match.

---

## 4. Development and AI-Powered Code Generation

This project is built using **AI-powered code generation** (e.g. **Cursor** or a similar environment) as the primary development method. The project lead directs the work by conversing with the AI; the AI produces code, documentation, and edits to the codebase. The project lead does not edit files directly—that keeps a single source of edits and makes every change traceable to a conversation and to the plan/design/knowledge set. For the project lead’s role in detail, see Section 6.8.

**Keeping implementation aligned:** Use the project-level documents to stay on track. When adding a feature, reference [40-REQUIREMENTS.md](40-REQUIREMENTS.md) to confirm it is in scope and to satisfy the right requirement IDs. Use [30-SCOPE.md](30-SCOPE.md) to avoid building out-of-scope functionality. Use **20-APPROACH.md** (and the relevant Design and Knowledge docs) so that patterns (e.g. data interface, document instances and versions, SIGNiX as a general interface) are implemented consistently. When the AI suggests an approach that conflicts with the design or plan, point to the design or plan and ask for alignment.

**Conventions for directing work:** When requesting implementation, reference the **plan and batch** (e.g. “implement Batch 2 of PLAN-ADD-DEALS”) so the AI can follow the plan’s steps and verification criteria. After each batch, review the output against the plan’s verification steps and run any tests (automated or manual). If implementation diverges from the plan for a good reason, update the plan so that the next run (or another implementer) follows the same path. When design or knowledge gaps appear, update the Design or Knowledge document before or as part of the next change. This is the documentation feedback loop described in Section 6.6.

---

## 5. Conventions (Implementation)

Implementation follows a fixed order and structure so that the application can be recreated from scratch and the documentation remains accurate.

- **Implementation order** — Follow [70-PLAN-MASTER.md](70-PLAN-MASTER.md) for the top-level sequence of plans. Within each phase that has multiple plans, follow the **phase plans document** for that phase (e.g. [02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md](02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md), [06-DOCS/PHASE-PLANS-DOCS.md](06-DOCS/PHASE-PLANS-DOCS.md), [07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md](07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md), [09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md](09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md)). Do not skip ahead; later plans depend on earlier ones. Setup documents (e.g. [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md), [08-NGROK/10-PLAN-NGROK.md](08-NGROK/10-PLAN-NGROK.md)) are executed at the points specified in PLAN-MASTER.
- **Batches and verification** — Each plan groups its steps into **batches** and defines **verification steps** for each batch (and often a “Section 6a” or equivalent). Implement batch by batch; run the plan’s verification and any tests after each batch; only when the batch is verified complete move to the next. This keeps progress testable and reversible.
- **No duplication and separation of concerns** — When functionality is needed in more than one place, implement it once in a **helper function** or **service** (e.g. in `services.py` or a dedicated module) and call it from views, forms, or other code. Do not copy-paste logic. Put business logic, data access, and integration code (e.g. SIGNiX payload building, document generation, schema discovery) in services or shared modules; keep **views** focused on HTTP request/response and thin orchestration. This keeps the codebase maintainable, testable, and consistent with the principles in Section 1.
- **Naming and structure** — Applications live under **apps/** (e.g. `apps.users`, `apps.deals`, `apps.schema`). Templates, URL patterns, and static files follow the structure established in the plans (e.g. PLAN-BASELINE for project layout, app-specific plans for URLs and views). Use the plan as the source of truth for naming and layout; when in doubt, follow the plan’s section on structure or the existing codebase pattern.

### 5.5 Project lifecycle (Ideation → Design → Implementation)

When approaching a **new project**, follow this flow. It uses **stage gates** (stakeholder approval to move from Ideation to Design, and from Design to Implementation) and keeps the documentation set **complete and coherent** so the project can be reproduced from scratch. The detailed execution steps are in Section 6.

**Ideation → Design (gate 1)**  
Create a **project pitch** and get **project stakeholder approval** to take the project from **Ideation** to **Design**. To support the pitch:
- **Outline user profiles and value proposition** ([15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md)) — who is served, their jobs, pains, and gains (and, as you refine, mapping to requirements).
- **Confirm or adapt the approach** ([20-APPROACH.md](20-APPROACH.md)) — how you will build and document; adapt if the project or domain demands a different methodology.
- **Outline scope** ([30-SCOPE.md](30-SCOPE.md)) — what is in or out of scope for this version.

Once stakeholders approve moving to Design, proceed.

**Design phase**  
- **Tighten** understanding of user profiles, value proposition, and scope. **Determine requirements** ([40-REQUIREMENTS.md](40-REQUIREMENTS.md)); requirements should **consider and align with** the user profiles and value proposition so that each requirement traces back to who it serves and what value it provides (see Section 6.3).
- **Update the project pitch** as new information is learned so the "why" and "who we serve" stay aligned with what you are building.
- When requirements are determined, create the **work-breakdown** ([50-WBS.md](50-WBS.md)) and **level of effort** ([60-LOE.md](60-LOE.md)).
- **As it makes sense** during Design: collect and document **knowledge**; outline **designs**; divide the project into **phases** and outline the **plan master** ([70-PLAN-MASTER.md](70-PLAN-MASTER.md)). The plan master can be an **outline** (phases, plan names, order); full plan content (batches, steps, verification) is created when you are about to implement each phase.
- When learnings warrant it, **update scope or requirements** (and the pitch and user profiles as needed)—not only refine wording, but add, remove, or re-prioritize so the doc set stays accurate.
- **Seek project stakeholder approval** to proceed from Design to **Implementation**.

**Implementation (gate 2)**  
- **Finalize knowledge and design** for the work you are about to do. **Phase-by-phase finalization** is acceptable: finalize knowledge and design for the next phase, then create that phase's **plan files**, then implement that phase before moving to the next. This avoids big-bang design while keeping plans grounded in stable design and knowledge.
- When creating plans, follow all **implementation best practices** (Section 5: no duplication, separation of concerns, batches and verification, naming and structure).
- **At the end of each work item** (e.g. batch or phase): assess whether learnings should be applied to the existing documentation set—requirements, design, knowledge, scope, user profiles and value proposition, and pitch. Update those documents so the set remains **complete and coherent** and would allow reproducing the project's implementation from scratch.
- **During implementation**, apply the implementation best practices and **bubble learnings up** to the appropriate documentation; do not leave critical information only in conversation or code.

For the full step-by-step methodology (pitch, scope, requirements, Knowledge → Design → Plan, documentation feedback loop), see Section 6.

---

## 6. Project Execution Methodology (Best Practices)

This section describes the **recommended order** for executing a project of this kind and aligns with the **project lifecycle** in Section 5.5 (Ideation → Design → Implementation). It is written for educational use: follow this sequence to apply best practices. The project is completed with **Cursor** (or a similar AI-powered development environment), with the project lead conversing with Cursor and all documentation and code created directly by Cursor (the project lead does not edit files). The goal is disciplined, repeatable execution that keeps implementation, plans, designs, and knowledge consistent and sufficient to recreate the application from scratch—and to use it as a template for other document-centric applications.

**Note on this project's history:** In early phases of this project, some of this process was not strictly followed in order. The documentation now reflects the **end state as if the full sequence had been followed from the start**. New projects should follow the sequence below from the beginning.

### 6.1 Project pitch (Ideation; gate 1)

Start with a **project pitch** (e.g. [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md)) that secures sponsorship and stakeholder approval. The pitch states why the project is being done, who it serves, what benefits are expected, and what success looks like. **To support the pitch**, outline **user profiles and value proposition** ([15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md)), **confirm or adapt the approach** (this document), and **outline scope** ([30-SCOPE.md](30-SCOPE.md)). Seek **project stakeholder approval** to take the project from **Ideation** to **Design**. Until stakeholders have approved (or at least aligned on) the pitch and agreed to proceed to Design, do not move on to tightening scope or determining requirements.

### 6.2 Scope (outline in Ideation; tighten in Design)

Clarify **scope**: what is in scope for this version and what is out of scope. Scope is **outlined** during Ideation (to support the pitch) and **tightened** during the Design phase. Capture it in a scope document (e.g. [30-SCOPE.md](30-SCOPE.md)). Scope defines the boundary of the project so that requirements and phases stay focused and stakeholders share the same expectations. When learnings during Design warrant it, update scope (add, remove, or re-prioritize)—not only refine wording.

### 6.3 Requirements (Design phase; consider profiles and value proposition)

Determine **requirements** (e.g. [40-REQUIREMENTS.md](40-REQUIREMENTS.md)) during the **Design phase**. Requirements state what the system must do and satisfy. They should **consider and align with** the **user profiles and value proposition** ([15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md)) so that each requirement traces back to who it serves and what value it provides; the "Maps to requirements" in the user profiles document supports this traceability. Requirements should **break the project into phases**: each phase has a clear boundary and deliverable (e.g. baseline, business domain, images, data interface, document templates, signing integration). **Update the project pitch** as new information is learned. When learnings warrant it, **update requirements** (and scope, pitch, or user profiles)—add, remove, or re-prioritize so the doc set stays accurate. The requirements document references or implies the phase structure so that the next step—work-breakdown and level of effort—can be built from it.

### 6.4 Work-breakdown and level of effort (Design phase; stakeholder approval to implement)

Once requirements are determined, produce a **work-breakdown** and **level of effort estimate** for stakeholder review. The work-breakdown spells out the phases and, within each phase, the plans and major batches (or work packages). The level of effort estimate gives stakeholders a clear view of the effort required so they can confirm commitment, adjust scope, or prioritize. **Seek project stakeholder approval** to proceed from **Design** to **Implementation**. Once stakeholders have reviewed and approved (or agreed to proceed), move on to executing the phases.

**In this repository:** The work-breakdown is [50-WBS.md](50-WBS.md) and the level of effort estimate is [60-LOE.md](60-LOE.md). They are aligned with the phase/plan structure in [40-REQUIREMENTS.md](40-REQUIREMENTS.md) and [70-PLAN-MASTER.md](70-PLAN-MASTER.md) and with the project’s actual experience; they are presented as the best-practice artifacts for stakeholder review.

### 6.5 Tackle each phase: Knowledge → Design → Plan → Implementation

Once the pitch, scope, requirements, and (where available) work-breakdown/LOE are in place, and **stakeholder approval to implement** has been obtained, **tackle each phase in turn**. **Finalize knowledge and design** for the phase (phase-by-phase finalization is acceptable). The **plan master** ([70-PLAN-MASTER.md](70-PLAN-MASTER.md)) may be an outline (phases, plan names, order) until you create full plan content when about to implement each phase. Within each phase, follow this order:

**1. Knowledge identification** — Identify what topic-specific knowledge Cursor (or the implementation team) would need to design, plan, and implement the phase. If that knowledge is not already present or is scattered, create or update a **knowledge file** to hold it. Knowledge files consolidate what must be known: summaries, concepts, and links to external resources (e.g. SIGNiX Flex API documentation, wkhtmltopdf constraints). Examples: [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md), [GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md](GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md), [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md). Knowledge is technology-agnostic or domain-conceptual where possible. Do not move to design until the knowledge for the phase is in place.

**2. Design** — Write (or update) the **Design** for the phase. The design states decisions and contracts: what the system will do, how components relate, and what the implementation must satisfy. It does not prescribe every line of code—that belongs in the plan. Review the design until there are no open issues or unresolved decisions. Designs point to the plan(s) that will implement them and to relevant knowledge documents. No implementation begins until the design for that phase is stable.

**3. Plan(s)** — Outline the **implementation work** for the phase in one or more **plans**. When multiple plans are needed, a **phase plans document** for the phase defines the sequence in which those plans are implemented. Within each plan: determine implementation steps; group steps into **batches**; define **verification steps** for each batch; specify **tests** (automated and unit wherever possible; manual testing tasks for the project lead where needed). **Pressure-test** the plans before implementation until there are no open implementation decisions or questions. The top-level sequence of phases is in [70-PLAN-MASTER.md](70-PLAN-MASTER.md); within a phase, the phase plans document (e.g. PHASE-PLANS-BIZ-DOMAIN, PHASE-PLANS-DOCS) defines the order of plans. Implementation proceeds phase by phase and plan by plan—no skipping ahead.

**4. Implementation** — Implement **in order**: plan by plan, and within each plan **batch by batch**. After each batch: run tests (automated and, where necessary, manual); verify against the plan's verification steps and the project lead's expectations; **only when the batch is verified complete and correct** move to the next batch. This keeps every step validated before building on it and keeps the implementation consistent with the plan.

### 6.6 Documentation feedback loop

Throughout the process, **with the completion of every significant aspect**, the documentation is reviewed and updated so that it stays aligned with reality:

1. **Plans** — Plans are updated to **accurately reflect the actual implementation** and to capture **lessons learned** (e.g. gotchas, workarounds, section references like “Section 12.1” for known pitfalls). If implementation diverged from the plan for a good reason, the plan is updated so that the next time (or another developer/AI) follows it, the same path is taken.
2. **Designs** — Designs are updated to **reflect real-world experience** from implementing the plans. If a design decision was refined or a constraint discovered, the design document is updated so that it remains the single source of truth for decisions.
3. **Knowledge** — Knowledge learned from the process of writing and implementing the plans and designs is **accurately and thoroughly documented** in the relevant knowledge file. New concepts, API details, or constraints that emerged during implementation are added so that future phases or a from-scratch rebuild have the benefit of that knowledge.
4. **Requirements, scope, user profiles and value proposition, pitch** — When learnings warrant it, **update** these documents (not only refine wording—add, remove, or re-prioritize as needed). For example, a new requirement may emerge from implementation; a scope boundary may need to shift; a persona's pains or gains may be refined. Keeping these aligned ensures traceability from value to requirements to implementation.

This **iterative documentation loop** ensures that the implementation, plan, design, knowledge, requirements, scope, and user profiles stay **consistent**. Maintain **consistency and cross-references**: every plan should point to its design and knowledge; designs should point to plans; requirements should align with user profiles and value proposition; when adding or changing a document, update references and references tables (e.g. in KNOWLEDGE-DOCUMENT-CENTRIC-APPS) so the doc set stays navigable. The gold standard (see below) depends on it.

### 6.7 Gold standard: recreate from scratch and use as template

The **gold standard** for the methodology is: **if Cursor (or another developer or AI-powered system) were to redo the implementation from scratch using only the documentation—no prior conversation, no hidden context—the implementation would complete without problems and would result in the same functionality.** The documentation should also support **using the project as a template** for another document-centric application (e.g. different business domain) so that someone can adapt it without the original business domain obscuring the patterns. That means:

- **PROJECT-PITCH**, **USER-PROFILES-VALUE-PROPOSITION**, **SCOPE**, **REQUIREMENTS**, **WBS**, **LOE**, and **APPROACH** make intent, who is served (and value), boundaries, methodology, and planned work and effort clear.
- Knowledge files give Cursor everything it needs to understand the domain and the integration points.
- Designs give Cursor the decisions and contracts it must satisfy.
- Plans give Cursor the exact sequence of steps and batches, with verification criteria and tests.
- Cross-references (plan → design, plan → knowledge, design → plan) allow Cursor to navigate the doc set without guesswork.
- No critical information lives only in conversation history or in the project lead’s head.

Whenever you add a feature or fix a gap, ask: "If we started over tomorrow, would the docs be sufficient for Cursor to get here again? Could someone use this as a template for another domain?" If not, update the docs.

### 6.8 Role of the project lead

The **project lead** directs the work by **conversing with Cursor**: requesting specific deliverables (e.g. “create KNOWLEDGE-APP-FOUNDATION,” “add Design/Knowledge refs to PLAN-MASTER,” “implement Batch 2 of PLAN-ADD-DEALS”), reviewing output, asking for refinements or consistency passes, and performing manual verification where automated tests are not enough. The project lead does **not** edit the code or documentation files directly—Cursor does that. This keeps a single “source of edits” and ensures that every change is traceable to a conversation and to the plan/design/knowledge set. The project lead also holds the **gold standard** in mind: when reviewing plans or docs, the question is whether someone (or some AI) could use them to recreate the application from scratch or adapt it as a template.

### 6.9 Validation: how well does this project match the methodology?

The current project files **largely match** the best-practices sequence above: phases, plan order, batches, verification steps, Knowledge/Design/Plan layering, cross-references, and lessons learned in plans are all present. The work-breakdown ([50-WBS.md](50-WBS.md)) and level of effort estimate ([60-LOE.md](60-LOE.md)) are in the repository and aligned with PLAN-MASTER and the phase plans. In early phases, some steps (e.g. project pitch, scope, requirements) were not done strictly in order; the documentation now reflects the end state as if the full sequence had been followed. Automated test coverage is strongest in the SIGNiX phase, with earlier phases relying more on manual verification steps in the plans. The methodology in §6.1–6.8 is the **recommended approach** for new projects and for teaching.

---

*What the system must do: [40-REQUIREMENTS.md](40-REQUIREMENTS.md). What is in or out of scope: [30-SCOPE.md](30-SCOPE.md). Why we are doing the project: [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md). Work-breakdown and effort: [50-WBS.md](50-WBS.md), [60-LOE.md](60-LOE.md).*

# Future Roadmap — Lease Origination Sample Application

This document describes **where to take the project after its initial implementation**: candidate features, themes, and a rough order of priority. Nothing here is **committed**—it is indicative and should be updated as the product and stakeholder needs evolve. What is **in or out of scope for the current version** remains in [30-SCOPE.md](30-SCOPE.md); what the system **must do today** is in [40-REQUIREMENTS.md](40-REQUIREMENTS.md). **If you are a new project lead or developer**, start with **"How to use this document"** below.

**Relationship to other docs:** The "Later / Future" list in [30-SCOPE.md](30-SCOPE.md) Section 3 and the "Out of Scope / Not Requirements" list in [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5 define what we are **not** building in this version. This roadmap adds **prioritization and rationale** (e.g. which persona or business need drives a given direction) and suggests an order for future work. When prioritizing, trace back to the [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) personas (especially the lease team leader) and the value proposition.

**Unified structure:** The roadmap below combines both types into **one set of proposals**. They are grouped into **Previously deferred scope** (items from scope/requirements "later" lists) and **New features** (exploratory or net-new ideas). Work can be prioritized from either group or from the combined prioritization table; the distinction is kept so stakeholders can see where each proposal originated.

### How to use this document

This roadmap is the single place for **candidate** future work. Nothing here is committed until the project lead (or stakeholders) decide to do it and, as appropriate, update scope or requirements. Two roles use it differently:

**For the project lead**

- **Define direction and prioritize** — Work with stakeholders (e.g. lease team leader, compliance, sponsor) to decide which proposals to pursue and in what order. Use the table in Section 2: **Type** (deferred scope vs new feature), **Showcases SIGNiX** and **Real-business app** (impact), **Primary personas** (who benefits), and **Effort** (rough size). Deferred-scope items are often what people expect "next" after reading scope/requirements; new features are optional unless you make them a goal.
- **Balance quick wins vs strategic bets** — For example: Troubleshooting tools or Dashboard as landing can be quick wins; Client portal or eNotary are larger bets. The suggested order under §1.1 (deferred scope) is a starting point, not mandatory—you can mix in new features or reorder.
- **Commit work** — When you decide to implement a proposal, agree with the developer on that choice. The work then follows Section 3 and [20-APPROACH.md](20-APPROACH.md) (Knowledge → Design → Plan → Implement in batches). If the work becomes part of a release or "in scope" for a phase, update [30-SCOPE.md](30-SCOPE.md) or [40-REQUIREMENTS.md](40-REQUIREMENTS.md) as needed so the doc set stays consistent.
- **Stakeholder alignment** — Use [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) to trace proposals to personas. The "Primary personas" column helps you explain who benefits from each proposal.

**For the developer**

- **Pick your next piece of work** — Do not start a proposal from this roadmap until the project lead (or stakeholder) has agreed it is next. Once agreed, use the proposal name and the description in Section 1 as the source of what to build; use the table in Section 2 for context (Effort, personas, type).
- **Execute** — Follow Section 3 and [20-APPROACH.md](20-APPROACH.md): Knowledge first (create or update knowledge docs as needed), then Design (decisions and contracts), then Plan (batches, verification steps, tests), then Implement batch by batch. The Approach is the authority; Section 3 is the short version for roadmap work.
- **Where implementation lives** — Once a proposal is committed, you will create or update phase-level docs: Knowledge (e.g. under [GENERAL-KNOWLEDGE](GENERAL-KNOWLEDGE/) or in a phase folder), Design (e.g. in 06-DOCS, 07-SIGNiX-SUBMIT, or a new folder), and Plan(s) (batches, steps, verification). The top-level sequence is in [70-PLAN-MASTER.md](70-PLAN-MASTER.md); new work may extend it or add a new phase.
- **Effort** — The Effort column is a high-level estimate. Use it to scope the conversation with the lead; refine with a design or spike before committing to a timeline. If you discover the effort is very different, update the table when you update the roadmap (Section 4).

**Getting started (new to this project?)**

1. Read this document top to bottom (intro, how to use, Section 1 lists, Section 2 table, Section 3, Section 4).
2. Read [20-APPROACH.md](20-APPROACH.md) Section 5 (Conventions) and Section 6 (Execution Methodology) so you know how work is done.
3. Read [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) and [30-SCOPE.md](30-SCOPE.md) so you know who is served and what is in or out of scope for the current version.
4. Use the **Suggested first initiatives** list and the Section 2 table to choose one to three proposals to prioritize. Agree with the other role (lead or developer) on what is next.
5. When you start implementing, follow Section 3. When you commit to something or reprioritize, update this document (Section 4).

---

## 1. Proposals

Ideas for work that could be done on the project. These are candidate features and directions, not committed; they can be refined, prioritized, or sequenced as needed. The two lists below keep the distinction between **previously deferred scope** and **new features**; the prioritization table in Section 2 includes all of them.

### 1.1 Previously deferred scope

These proposals are derived from or closely aligned with the "Later / Future" list in [30-SCOPE.md](30-SCOPE.md) Section 3 and the "Out of Scope / Not Requirements" list in [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5—items already called out as "not this version" but natural next steps.

- **Reporting and key metrics** — Deals created, documents sent, completion rates, time-to-sign, and simple reports so the lease team leader (or delegate) can manage the business. Aligns with the **lease team leader** persona ([15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md)): "Use reports and metrics to manage the business." Today the signature transactions dashboard and deal-level related transactions give visibility; reporting and dashboards beyond that list are a natural next step.

- **Troubleshooting tools** — Identify transactions or deals that have been pending too long (e.g. customer hasn't signed after X days), lists of stale or stuck transactions, and optional alerts so the team can follow up and get processes back on track. Aligns with the **lease team leader** persona: "Troubleshoot when the process breaks down" and "proactive tools (e.g. unsigned after X days)."

- **Multiple deal types in the UI** — The design already allows additional deal types; the current version implements one (e.g. "Lease - Single Signer"). Adding more deal types and their document set templates would support broader product offerings without changing the core pattern. See [30-SCOPE.md](30-SCOPE.md) Section 3.

- **Signing flow refinements** — Resend invitation, cancel transaction, limit re-submissions, and similar refinements to make day-to-day operations smoother when signers delay or a mistake is made. Optional validation or tooling (e.g. QueryTransactionStatus polling, push request validation) can improve reliability. See [30-SCOPE.md](30-SCOPE.md) Section 3.

- **Role-based access control** — Fine-grained roles (e.g. viewer, editor, admin) beyond "staff can use the app and admin," so the lease team leader (or compliance) can have read-only or summary views without day-to-day edit access. Only add if a concrete use case requires it ([30-SCOPE.md](30-SCOPE.md) Section 2 and 3).

- **Public API for third-party systems** — REST or other API for external systems to create/read deals or documents, for integration with CRM, LOS, or other tools. See [30-SCOPE.md](30-SCOPE.md) Section 3.

- **Multi-tenancy** — Multiple organizations or tenants in one deployment, if a future use case requires it ([30-SCOPE.md](30-SCOPE.md) Section 3).

- **Full audit trail of domain data** — Who created/updated vehicles, contacts, deals (in addition to SIGNiX signing audit trail), for compliance or operational review. See [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5.

- **Production hardening** — Production-grade deployment, high availability, backup/restore, compliance certifications (e.g. SOC2, HIPAA) if the application moves beyond reference, demo, and template use. See [30-SCOPE.md](30-SCOPE.md) Section 2.

- **Alternative signing providers** — Integration with a provider other than SIGNiX; only relevant if the project or a derivative chooses to support multiple providers ([30-SCOPE.md](30-SCOPE.md) Section 2 and 3).

**Suggested order for deferred scope (from earlier roadmap):** When prioritizing within this group, a reasonable sequence was: (1) Troubleshooting tools, (2) Reporting and key metrics, (3) Signing flow refinements, (4) Multiple deal types in the UI, (5) Role-based access, (6+) API, multi-tenancy, audit trail, production hardening, alternative providers as needs dictate.

### 1.2 New features

Exploratory or net-new ideas: SIGNiX showcase features, new surfaces, documentation, and strategic options. Some overlap with deferred scope (e.g. management reports with reporting and key metrics; more deal types and templates with multiple deal types in the UI); the table in Section 2 includes both so they can be prioritized together.

- **Navigation and admin UI** — Clear up the menu on the left, making it more obvious for the lease officer to find what they are interested in, while putting configuration options into a sub-menu. Make the UI consistent by either committing to using Jazzmin fully or removing Jazzmin.

- **Dashboard as default landing** — Add a dashboard and make it the default landing page for the application. The dashboard should be useful to the lease officer, giving them an at-a-glance screen to comprehend what's in the system and what it does, with the ability to launch from there to their next step (work on a deal, add or modify a contact, add or modify a vehicle, etc.). It should also give insight into open signature transactions.

- **Client portal** — Add client portal functionality. Such functionality might allow customers to browse vehicles and/or a store without logging in (see the store proposal for details). Then they could log in to view their deals and documents. When logged in, if they have open signature transactions, they might enter the SIGNiX signing room from there, without needing to find the link in their email.

- **Coordinate-based tagging** — Add support for SIGNiX coordinate-based tagging. The app already supports two of the three SIGNiX tagging approaches: PDFs with form fields and PDFs with text tagging. The third is PDFs with coordinate-based tagging, where signature and other form fields are specified by type, name, location (X/Y coordinates) on a page, and size (width and height). This would allow users to upload PDFs without form fields and tag them via the coordinate system. The feature must be designed with SIGNiX's coordinate-based tagging in mind and would showcase a valuable SIGNiX capability.

- **Digital billboard** — Integrate SIGNiX's digital billboard feature, which shows an image at the end of a signer's session. This can be tailored by signer and transaction, enabling highly tailored messaging and call-to-action. For an internal audience (users / loan officers) this could deliver a relevant message; for signers / customers, it could send them to the company's store (see store proposal).

- **Storefront** — A storefront for customers that would promote accessories for the vehicles, etc. In the Jet Pack scenario, that could include flight suits, boots, gloves, helmets (including those with communications systems or heads-up displays), key rings, towels, etc. This could be used to showcase the digital billboard feature at the end of the signer's (customer's) experience.

- **User guides** — User guides for the primary user (lease officer), the power user / system administrator (configuration, adding and updating templates, etc.), and for the IT Operations team (install, host, manage, and maintain the system).

- **More authentication types** — Support additional SIGNiX authentication types, such as ID Verify.

- **eNotary workflow** — Add eNotary workflow to showcase SIGNiX's eNotary platform. This would involve introducing the notary as a user and having a notarization workflow (e.g. notarized bill of sale, notarized title transfer, lien documents applicable to financing, etc.).

- **SIGNiX fraud alert** — Introduce SIGNiX fraud alert functionality so that the Compliance Officer can be notified of any suspicious transactions.

- **ReadyDoX on client portal** — On the client portal or client-facing side of the application, add SIGNiX ReadyDoX for document self-service.

- **Online help** — Creation of online help.

- **Management reports for lease team leader** — For the lease team leader, a set of appropriate management reports, such as deals by lease officer, time to sign documents, etc.

- **Auto-detect form fields in static PDFs** — PDF processing to automatically identify form fields in an uploaded static PDF.

- **More deal types and templates** — Additional deal types and document templates, such as two-signer leases, leases with a guarantor, cash purchase deals, trade-in deals, etc.

- **Refactor tech stack** — Strengthen the underlying technology stack for production or scale. Examples: move the database from SQLite to PostgreSQL or SQL Server; move file handling from local storage (media folder) to a document or content management system (e.g. Directus) or cloud storage (e.g. Azure Blob Storage, Amazon S3); move user identity and access to an enterprise identity platform (e.g. Azure Entra ID, Okta). Each change should be designed and implemented in line with the Approach (separation of concerns, services); the current stack is documented in [20-APPROACH.md](20-APPROACH.md) Section 3 (Technology Choices).

- **Recreate application on a different tech stack** — Build the same application (or a close variant) on a different technology baseline than Django/Python. Examples: .NET + Entity Framework Core + SQL Server; ASP.NET Core Web API + React, Angular, or Vue; Java Spring Boot + Spring Data JPA + PostgreSQL; Express.js + Sequelize + PostgreSQL; NestJS + TypeORM or Prisma; Python Django + React; Python Flask + SQLAlchemy + Jinja2 / Tailwind; etc. Goals: demonstrate the power of AI-assisted code generation; validate the value of the project documentation set (Knowledge, Design, Plan) as the source of truth for recreating behavior; serve as an educational tool for how to use AI to generate and maintain document-centric applications; and help developers familiar with a given stack (e.g. .NET) understand how to integrate with SIGNiX using their preferred stack. The existing docs (especially [20-APPROACH.md](20-APPROACH.md), phase-level Design and Knowledge, and SIGNiX integration patterns) would drive the new implementation; the result would be a parallel codebase, not a replacement of the Django app unless the project chooses to sunset it.

- **Repurposing to other domains** — Repurposing of the application to a different domain, including creating new templates and business logic—e.g. wealth management onboarding, personal loans, commercial loans, business equipment loans or leases (or sales), farming equipment loans or leases (or sales), healthcare installment plans (e.g. for knee surgery, cosmetic dental work, etc.).

---

## 2. Prioritization of proposals

The table below supports prioritization by **type** (previously deferred scope vs new feature), **impact** (showcasing SIGNiX, making the app more like a real business application, and benefit by user profile), and **level of effort** (high-level estimate; opinion only, to be refined with design and spikes). Work can be prioritized from either type or from the combined list. **Proposals are ordered to surface high-impact, manageable-scope items first** so that teams can quickly identify strong candidates for early execution and prioritization discussions.

**Suggested first initiatives**

When choosing what to tackle first, the following proposals often work well: they deliver **visible value quickly**, fit into a **manageable number of batches**, and demonstrate **core patterns** (documentation-driven development, integration with SIGNiX, UX improvement). They are a good place to start when you want to pick one or two items from the backlog.

- **Troubleshooting tools** — Visible list/filter (e.g. unsigned after X days); clear batches (query, view, optional alerts); addresses a common pain for the lease team leader.
- **Dashboard as default landing** — Highly visible; at-a-glance screen with links and open transactions; can be implemented in a few batches (landing page, cards, data).
- **Navigation and admin UI** — Clear scope (menu reorg, config in sub-menu); visible improvement; commits to Jazzmin or simplifies the shell.
- **Reporting and key metrics** — High impact for the team leader; batchable (one report at a time); builds on existing visibility.
- **Digital billboard** — SIGNiX showcase; tailored end-of-session image; small–medium effort; strong demo value.
- **Signing flow refinements** — Resend, cancel, or limit re-submissions; improves daily operations; batchable (e.g. resend first).
- **Management reports for lease team leader** — Deals by officer, time to sign; visible reports; overlaps with reporting theme.
- **More authentication types (e.g. ID Verify)** — SIGNiX capability; small–medium effort; demonstrates integration and configuration.

**Scales:**

- **Type:** **Deferred scope** = from scope/requirements "later" lists; **New feature** = exploratory or net-new idea.
- **Showcases SIGNiX:** High = directly demonstrates a distinct SIGNiX capability (e.g. coordinate tagging, eNotary, digital billboard); Medium = uses SIGNiX in a visible or expanded way; Low = indirect or minimal; — = none.
- **Real-business app:** High = strongly improves fit for production or real-world use; Medium = meaningful improvement; Low = incremental.
- **Primary personas:** Lease officer; Team leader (lease team leader); Sys admin (system administrator); Compliance; Customer/signer. Only those with material benefit are listed.
- **Effort:** Small = days to a couple of weeks; Medium = several weeks; Large = a couple of months or more; XLarge = multi-month or domain shift. Assumes one capable developer; no spike or discovery done yet.

| Proposal | Type | Showcases SIGNiX | Real-business app | Primary personas | Effort |
|----------|------|------------------|-------------------|------------------|--------|
| Troubleshooting tools | Deferred scope | Low | High | Team leader | Medium |
| Dashboard as default landing | New feature | Low | High | Lease officer, Team leader | Medium |
| Navigation and admin UI | New feature | Low | High | Lease officer, Sys admin | Medium |
| Reporting and key metrics | Deferred scope | Low | High | Team leader | Medium |
| Digital billboard | New feature | High | Medium | Lease officer, Customer, Sys admin | Small–Medium |
| Signing flow refinements | Deferred scope | Low | High | Lease officer | Medium |
| Management reports for lease team leader | New feature | Low | High | Team leader | Medium |
| More authentication types (e.g. ID Verify) | New feature | High | Medium | Sys admin, Compliance | Small–Medium |
| Multiple deal types in the UI | Deferred scope | Low | High | Lease officer, Sys admin | Medium |
| Role-based access control | Deferred scope | — | High | Team leader, Compliance | Medium |
| User guides | New feature | — | High | Lease officer, Sys admin, IT Ops | Medium |
| SIGNiX fraud alert | New feature | High | High | Compliance, Team leader | Medium |
| Online help | New feature | — | Medium | Lease officer, Sys admin, Customer | Small–Medium |
| Client portal | New feature | Medium | High | Lease officer, Customer | Large |
| Coordinate-based tagging | New feature | High | Medium | Lease officer, Sys admin | Medium–Large |
| ReadyDoX on client portal | New feature | High | Medium | Customer | Medium–Large |
| Auto-detect form fields in static PDFs | New feature | Medium | High | Lease officer, Sys admin | Large |
| More deal types and templates | New feature | Low | High | Lease officer, Sys admin | Medium |
| Public API for third-party systems | Deferred scope | Low | High | Lease officer, Sys admin | Large |
| Multi-tenancy | Deferred scope | — | High | Sys admin, Team leader | Large |
| Full audit trail of domain data | Deferred scope | — | High | Compliance, Team leader | Medium |
| Production hardening | Deferred scope | — | High | Sys admin, IT Ops | Large |
| Alternative signing providers | Deferred scope | Low | High | Sys admin | Large |
| Storefront | New feature | Low | Medium | Customer, Lease officer | Large |
| eNotary workflow | New feature | High | High | Notary (new), Compliance, Lease officer | Large |
| Refactor tech stack | New feature | — | High | Sys admin, IT Ops | Large |
| Recreate application on a different tech stack | New feature | Low | Medium (educational / multi-stack) | Developer (other stack), Educator | XLarge |
| Repurposing to other domains | New feature | Low | High (new domain) | All (new domain) | XLarge |

---

## 3. How to execute roadmap work

When moving a theme or proposal forward into design and implementation, follow the **methodology in [20-APPROACH.md](20-APPROACH.md)** (Section 5 Conventions, Section 6 Project Execution Methodology). The Approach is the authority; this section summarizes how it applies to roadmap work.

1. **Knowledge** — Before design for the work begins, ensure **knowledge is in place**: update relevant knowledge documents or create one or more new knowledge files as needed (e.g. under [GENERAL-KNOWLEDGE](GENERAL-KNOWLEDGE/) or in the relevant project doc folder). Do not move to design until the knowledge for the work is adequate. As implementation proceeds, keep the knowledge base in sync with new capabilities, integration patterns, and decisions (documentation feedback loop—Approach §6.6).

2. **Design → Plan → Implement in batches** — Follow the sequence **Knowledge → Design → Plan → Implementation** (Approach §6.5). For the theme or proposal: **Design** (decisions and contracts; stable before implementation); **Plan** (steps in **batches**, with **verification steps** per batch and **tests**—automated wherever possible; manual testing tasks for the project lead where needed); **Implement** one batch at a time, verifying each batch before proceeding. Where the project lead must perform testing or validation, provide clear details on how to test (steps, data, expected outcomes) so validation is repeatable and unambiguous.

3. **Separation of concerns and code structure** — Follow Approach §1 and §5: maintain the separation of concerns between **business logic** and **integration** (e.g. SIGNiX API, external services). Use **helpers and services**; do not duplicate code; put logic that belongs outside the UI in services or dedicated modules. Avoid embedding integration details or third-party specifics in domain or UI layers.

### Prompt template for directing implementation of a proposal

When you are ready to start implementation of a roadmap proposal, you can use the following prompt to direct the work. Replace **\[PROPOSAL]** with the exact proposal name from Section 1 or 2 (e.g. "Troubleshooting tools", "Dashboard as default landing", "Digital billboard"). The prompt is designed to align the implementation with the Approach, code standards, and documentation feedback loop, and to prioritize automated testing so that progress can be verified without heavy manual testing.

---
**Copy from here:**

Implement the roadmap proposal **\[PROPOSAL]** from [PROJECT-DOCS/80-FUTURE-ROADMAP.md](80-FUTURE-ROADMAP.md). Use this document and Section 1 for the scope and intent; use the prioritization table in Section 2 for context (including Primary personas for this proposal). **Goal:** Deliver the implemented proposal as a new phase (or phases), fully documented and integrated into the project so that the application can be recreated from scratch using only the documentation set, and mark the proposal as completed in the roadmap when done.

**Use the project documentation set:** Refer to the broader project documentation as needed. Before creating new knowledge, search the repository for existing knowledge files (e.g. under PROJECT-DOCS/GENERAL-KNOWLEDGE or in phase folders such as 06-DOCS, 07-SIGNiX-SUBMIT) and use or extend them if they already cover the topic. Consult relevant Design and Plan documents for existing patterns, constraints, and structure (e.g. [70-PLAN-MASTER.md](70-PLAN-MASTER.md), phase plans, and DESIGN-* files). Create new knowledge only when it does not already exist or is not findable.

**User profiles and value proposition:** Read [PROJECT-DOCS/15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) so the solution aligns with who is served and what they value. The proposal's "Primary personas" in the roadmap table (Section 2) indicate who benefits—design and implement so the outcome matches those users' expectations and gains (e.g. lease team leader, lease officer, sys admin, compliance).

**Methodology:** Read and follow [PROJECT-DOCS/20-APPROACH.md](20-APPROACH.md) Section 5 (Conventions) and Section 6 (Project Execution Methodology). Work in this order: (1) **Knowledge** — ensure relevant knowledge exists or create/update knowledge files (e.g. under PROJECT-DOCS/GENERAL-KNOWLEDGE or the relevant phase folder); do not start design until knowledge is in place. (2) **Design** — create or update the design for this work (decisions, contracts, what the system will do); stabilize before implementation. (3) **Plan** — create or update the **phase plan** (PHASE-PLANS-*.md) and **detailed plan(s)** for this phase, with steps grouped into **batches**, **verification steps** for each batch, and **tests**. (4) **Implement** — execute one batch at a time; after each batch, run the verification steps and tests (e.g. run the project test suite from the project root), then update the plan (and design or knowledge if learnings warrant it) before proceeding. This documentation feedback loop is mandatory: capture new learnings in the plan, design, or knowledge so the doc set stays accurate and the next batch builds on a correct base.

**Phases, phase plans, and PLAN-MASTER:** Roadmap proposals usually represent one or more new **phases** of the project. Create a new phase folder (e.g. 10-DASHBOARD, 11-TROUBLESHOOTING) following the naming pattern in [PROJECT-DOCS/00-INDEX.md](00-INDEX.md) and [PROJECT-DOCS/70-PLAN-MASTER.md](70-PLAN-MASTER.md). Within the phase: create or update the Design, then create a **phase plan** (PHASE-PLANS-*.md) that defines the implementation order and links to each detailed plan. If the work is large, break the phase into **multiple plans** (e.g. 10-PLAN-..., 20-PLAN-...); each plan has its own batches and verification. If the work is small, a single plan in the phase folder may suffice. The phase plan document is the single place that lists the order of plans for this phase and points to the Design and Knowledge. When implementation is complete: update [PROJECT-DOCS/70-PLAN-MASTER.md](70-PLAN-MASTER.md) (add the new phase to the implementation order and update the "To recreate this app from scratch" summary at the end); and update [PROJECT-DOCS/80-FUTURE-ROADMAP.md](80-FUTURE-ROADMAP.md) to indicate that this proposal has been completed (e.g. per Section 4 Maintenance—note that the proposal was committed and implemented so the roadmap reflects current state).

**Decisions and open issues:** Where the design or plan has open issues, or where an implementation choice is ambiguous, make a reasonable recommendation consistent with the Approach and existing docs, document the decision in the plan or design, and proceed. Only stop to ask the user when the choice is blocking, has major tradeoffs the user must weigh, or cannot be inferred from the project documentation.

**Code standards:** Follow Approach §1 and §5. Use **helpers and services**; do not duplicate logic. Keep **separation of concerns** between UI, business logic, and integration (e.g. SIGNiX, external APIs). Put logic that does not belong in views or forms into services or dedicated modules. Name and structure code consistently with the existing codebase and the plan.

**Folder structure and file naming:** Use the same folder structure and file naming conventions as the existing project. For documentation: phase folders (e.g. 01-BASELINE, 06-DOCS, 07-SIGNiX-SUBMIT), DESIGN-* for design docs, NN-PLAN-* or PLAN-* for plans, KNOWLEDGE-* for knowledge files, PHASE-PLANS-* for phase plan order; general knowledge under PROJECT-DOCS/GENERAL-KNOWLEDGE. For code: apps under apps/, with structure and naming as in the existing plans and codebase. When adding a new phase or new docs, follow the patterns shown in [PROJECT-DOCS/00-INDEX.md](00-INDEX.md). When you add or change any project-level or phase-level documentation (new or updated knowledge, design, or plan files, or a new phase folder), update [PROJECT-DOCS/00-INDEX.md](00-INDEX.md) so the index stays complete and the doc set remains navigable.

**Testing:** Automated tests are essential. Prefer unit tests and integration tests that can be run from the command line (e.g. pytest, Django test runner) so that progress can be verified without manual UI testing. Include tests in the plan for each batch where applicable. If manual verification is required for a step, document the exact steps, data, and expected outcome in the plan so it can be repeated. Aim for a **working, testable result** by the end of the work—either a complete batch or a clear path (with remaining batches and verification) to get there. If something cannot be completed in one pass, state what is done, what is left, and how to run tests and verification so the next pass can continue.

**Deliverables:** Produce or update as needed: knowledge file(s), design document(s), phase plan (PHASE-PLANS-*.md) and detailed plan(s) with batches and verification, code changes, and automated tests. When adding or changing documentation, update [PROJECT-DOCS/00-INDEX.md](00-INDEX.md) as appropriate. When the phase is complete: update [PROJECT-DOCS/70-PLAN-MASTER.md](70-PLAN-MASTER.md) so the new phase is in the implementation order and the "recreate from scratch" summary is accurate; and update [PROJECT-DOCS/80-FUTURE-ROADMAP.md](80-FUTURE-ROADMAP.md) to indicate that this proposal has been completed (per Section 4 Maintenance). After each batch, update the plan (and design or knowledge if needed) with any new decisions, gotchas, or refinements. At the end, provide a short summary: what was implemented, how to run the tests, and any remaining work or follow-up batches. **Done when:** The new phase is in PLAN-MASTER, 00-INDEX and the roadmap are updated, tests pass, and the summary has been provided.
**Copy to here.**
---

---

## 4. Maintenance of this document

- **Update when** priorities change, a proposal is committed to a release (or phase), or new ideas emerge from implementation or stakeholder feedback. **Project lead** typically owns prioritization and when to update the table or lists; **developer** may suggest changes (e.g. revised Effort, new proposals) and should update the table if effort or scope shifts during implementation.
- **Keep scope and requirements the source of truth** for "in this version" vs "not in this version"; this document is for **direction and order**, not a substitute for [30-SCOPE.md](30-SCOPE.md) or [40-REQUIREMENTS.md](40-REQUIREMENTS.md). When a roadmap proposal is committed to a release, add or adjust scope/requirements as needed so the doc set stays consistent.
- **When using this project as a template**, replace or adapt this roadmap for the new project's own post–initial-implementation direction.

---

*What is in or out of scope for this version: [30-SCOPE.md](30-SCOPE.md). What the system must do: [40-REQUIREMENTS.md](40-REQUIREMENTS.md). User profiles and value proposition: [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md). How we build and execute: [20-APPROACH.md](20-APPROACH.md). Implementation order for the current version: [70-PLAN-MASTER.md](70-PLAN-MASTER.md).*

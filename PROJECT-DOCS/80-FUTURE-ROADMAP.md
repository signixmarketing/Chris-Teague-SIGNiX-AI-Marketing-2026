# Future Roadmap — Lease Origination Sample Application

This document describes **where to take the project after its initial implementation**: candidate features, themes, and a rough order of priority. Nothing here is **committed**—it is indicative and should be updated as the product and stakeholder needs evolve. What is **in or out of scope for the current version** remains in [30-SCOPE.md](30-SCOPE.md); what the system **must do today** is in [40-REQUIREMENTS.md](40-REQUIREMENTS.md).

**Relationship to other docs:** The "Later / Future" list in [30-SCOPE.md](30-SCOPE.md) Section 3 and the "Out of Scope / Not Requirements" list in [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5 define what we are **not** building in this version. This roadmap adds **prioritization and rationale** (e.g. which persona or business need drives a given direction) and suggests an order for future work. When prioritizing, trace back to the [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md) personas (especially the lease team leader) and the value proposition.

---

## 1. Future Priorities (themes)

The following themes are candidates for post–initial-implementation work. They are grouped by **priority** (high / medium / later) to guide where to invest next. Priorities are indicative and may change with stakeholder input or new use cases.

### 1.1 High priority

- **Reporting and key metrics** — Deals created, documents sent, completion rates, time-to-sign, and simple reports so the lease team leader (or delegate) can manage the business. Aligns with the **lease team leader** persona ([15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md)): "Use reports and metrics to manage the business." Today the signature transactions dashboard and deal-level related transactions give visibility; reporting and dashboards beyond that list are a natural next step.
- **Troubleshooting tools** — Identify transactions or deals that have been pending too long (e.g. customer hasn’t signed after X days), lists of stale or stuck transactions, and optional alerts so the team can follow up and get processes back on track. Aligns with the **lease team leader** persona: "Troubleshoot when the process breaks down" and "proactive tools (e.g. unsigned after X days)."

### 1.2 Medium priority

- **Multiple deal types in the UI** — The design already allows additional deal types; the current version implements one (e.g. "Lease - Single Signer"). Adding more deal types and their document set templates would support broader product offerings without changing the core pattern. See [30-SCOPE.md](30-SCOPE.md) Section 3.
- **Signing flow refinements** — Resend invitation, cancel transaction, limit re-submissions, and similar refinements to make day-to-day operations smoother when signers delay or a mistake is made. Optional validation or tooling (e.g. QueryTransactionStatus polling, push request validation) can improve reliability. See [30-SCOPE.md](30-SCOPE.md) Section 3.
- **Role-based access control** — Fine-grained roles (e.g. viewer, editor, admin) beyond "staff can use the app and admin," so the lease team leader (or compliance) can have read-only or summary views without day-to-day edit access. Only add if a concrete use case requires it ([30-SCOPE.md](30-SCOPE.md) Section 2 and 3).

### 1.3 Later / as needed

- **Public API for third-party systems** — REST or other API for external systems to create/read deals or documents, for integration with CRM, LOS, or other tools. See [30-SCOPE.md](30-SCOPE.md) Section 3.
- **Multi-tenancy** — Multiple organizations or tenants in one deployment, if a future use case requires it ([30-SCOPE.md](30-SCOPE.md) Section 3).
- **Full audit trail of domain data** — Who created/updated vehicles, contacts, deals (in addition to SIGNiX signing audit trail), for compliance or operational review. See [40-REQUIREMENTS.md](40-REQUIREMENTS.md) Section 5.
- **Production hardening** — Production-grade deployment, high availability, backup/restore, compliance certifications (e.g. SOC2, HIPAA) if the application moves beyond reference, demo, and template use. See [30-SCOPE.md](30-SCOPE.md) Section 2.
- **Alternative signing providers** — Integration with a provider other than SIGNiX; only relevant if the project or a derivative chooses to support multiple providers ([30-SCOPE.md](30-SCOPE.md) Section 2 and 3).

---

## 2. Future Roadmap (suggested order)

A suggested sequence for post–initial-implementation work. Adjust based on stakeholder feedback and resource availability.

| Order | Theme | Rationale |
|-------|--------|-----------|
| 1 | **Troubleshooting tools** | Quick win for the lease team leader; "unsigned after X days" and stale-transaction lists directly address pain. |
| 2 | **Reporting and key metrics** | Complements visibility already in place; supports managing the business and justifying the system. |
| 3 | **Signing flow refinements** | Improves daily operations (resend, cancel, re-submission limits) without expanding scope of deal types. |
| 4 | **Multiple deal types in the UI** | Unlocks more product scenarios using the existing document-set and deal-type pattern. |
| 5 | **Role-based access** | Add when a concrete need exists (e.g. leader/compliance read-only views). |
| 6+ | **API, multi-tenancy, audit trail, production hardening, alternative providers** | As business or compliance needs dictate. |

---

## 3. Maintenance of this document

- **Update when** priorities change, a theme is committed to a release, or new ideas emerge from implementation or stakeholder feedback.
- **Keep scope and requirements the source of truth** for "in this version" vs "not in this version"; this document is for **direction and order**, not a substitute for [30-SCOPE.md](30-SCOPE.md) or [40-REQUIREMENTS.md](40-REQUIREMENTS.md).
- **When using this project as a template**, replace or adapt this roadmap for the new project’s own post–initial-implementation direction.

---

*What is in or out of scope for this version: [30-SCOPE.md](30-SCOPE.md). What the system must do: [40-REQUIREMENTS.md](40-REQUIREMENTS.md). User profiles and value proposition: [15-USER-PROFILES-VALUE-PROPOSITION.md](15-USER-PROFILES-VALUE-PROPOSITION.md). Implementation order for the current version: [70-PLAN-MASTER.md](70-PLAN-MASTER.md).*

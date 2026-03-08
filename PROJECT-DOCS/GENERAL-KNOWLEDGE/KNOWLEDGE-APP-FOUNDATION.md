# Knowledge: Application Foundation (Baseline for Data-Centric and Document-Centric Apps)

This document describes the **foundation** that data-centric and document-centric business applications need before adding products, customers, deals, and document generation. It is **technology-agnostic**: the same capabilities and principles apply whether you build with Python/Django, .NET, Node, Go, or another stack. This repo implements the foundation in Django per [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md); the design decisions are in [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md).

---

## 1. What the Baseline Is For

The baseline is the **first layer** of the application. Every later feature assumes it is in place:

- **Products, customers, and deals** (PHASE-PLANS-BIZ-DOMAIN) — Need authenticated users, a “current user,” and a consistent app shell (sidebar, content area) so that list/add/edit/delete pages share the same layout and navigation.
- **Images and data interface** (PLAN-ADD-IMAGES, PLAN-DATA-INTERFACE) — Need the same shell and auth; the data interface and document features use the current user (e.g. as lease officer on a deal).
- **Document templates and document sets** (PHASE-PLANS-DOCS) — Need deal data, which is tied to users and profiles; profile timezone drives how dates and times are displayed app-wide.
- **Signing** (PHASE-PLANS-SIGNiX-SUBMIT, etc.) — Need the same shell (Documents section on deal detail, Send for Signature) and the same notion of “current user” and profile.

Without the baseline, you cannot add these features in a coherent way. The baseline is not “generic CRUD”—it is the **employee-facing app foundation** that the rest of the pattern assumes.

---

## 2. Core Capabilities (Checklist)

Any implementation of the baseline—in any stack—should provide the following. Use this as a checklist when building from scratch or when porting the template to another technology.

| Capability | What it means |
|------------|----------------|
| **Authentication** | Login, session, and logout. Only authenticated users can use the main app. Unauthenticated requests redirect to login. |
| **User profile** | Each user has profile data: display name (e.g. first, last, full), contact info (email, phone), and **timezone** (IANA name) so that dates and times are shown in the user’s local time app-wide (deal dates, document dates, etc.). |
| **App shell** | A consistent layout for all main app pages: e.g. a **sidebar** (navigation) plus a **content** area. The same shell wraps Profile, Products, Customers, Deals, Documents, and any other feature so the UX is unified. |
| **Minimal layout for auth pages** | Login and post-logout pages use a **minimal** layout (e.g. centred card, no sidebar) because the user is not yet in the app workflow. |
| **Admin (back-office)** | A separate area for user and role management (and optionally other config). Staff can open it from the app and return to the app without losing context. The app and admin feel connected (e.g. “Back to app,” link to profile from admin header). |
| **Initial user** | A **repeatable**, **idempotent** way to create the first user (and profile) so that “setup from scratch” is documented and reliable. Running the step again does not duplicate or break data. |

---

## 3. Why This Matters for Document-Centric Apps

- **Deals and documents reference “the current user.”** For example, the lease officer on a deal is the user who created or owns the deal. The baseline must provide a clear notion of “current user” and a place to store display info (profile) used in the UI and in generated documents.
- **Profile timezone drives date/time display.** Deal dates, document version dates, and signing timestamps are shown in the user’s timezone. The baseline should store timezone per user and apply it app-wide (e.g. via middleware or request context) so you don’t have to fix it later.
- **The same shell hosts Documents and Send for Signature.** The deal detail page (and later the Documents section) lives inside the app shell. If the shell is inconsistent or missing, every feature after the baseline will feel bolted on. Getting the shell right first (sidebar, base templates, auth redirects) avoids rework.

---

## 4. Why Python and Django Fit This Template

For this repo, **Python and Django** were chosen because they provide the baseline capabilities with minimal custom code:

- **Built-in auth** — User model, login/logout views, session middleware, `@login_required`. No need to build auth from scratch.
- **Admin** — Django Admin gives user/group management and is extensible (e.g. Jazzmin for theming and sidebar). The “admin area” capability is satisfied out of the box.
- **ORM and migrations** — Profile can be a OneToOne to User; migrations keep schema and data in sync. Easy to add more apps (vehicles, contacts, deals) later.
- **Templates and views** — Base templates (app shell vs plain) and view logic are straightforward. The same patterns scale to the rest of the app.
- **Ecosystem** — Mature, well-documented, and widely used. A developer cloning this template can focus on the business domain and documents rather than reinventing auth and admin.

The same **baseline capabilities** can be implemented in other stacks (see Section 6). This repo provides the **Django** implementation in [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md); [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md) states the decisions any implementation should satisfy.

---

## 5. Principles (Summary)

- **Authenticated employees** — Users are staff (lease officers, etc.), not anonymous or public customers. Every main app page requires login.
- **Profile and context** — Profile holds display name, contact info, and timezone. Timezone is first-class so date/time display is consistent and correct from day one.
- **App shell** — One layout (sidebar + content) for all main app pages; a second, minimal layout for login and logged-out. No feature should invent its own shell.
- **Admin and app linked** — Users can go from app to admin and back; profile is reachable from the admin header (e.g. person icon → profile). The app and admin feel like one product.
- **Initial user** — Idempotent setup step (e.g. management command or seed script) so that “run from scratch” is documented and repeatable.

---

## 6. Implementing in Another Stack

If you use this project as a **conceptual template** but implement in a **different language or framework** (e.g. .NET, Node, Go):

- Use **this knowledge file** and [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md) as the **capability and design checklist**. They describe *what* the baseline must provide and *why*, not how to code it in Django.
- [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md) remains the **Django** implementation reference. You do not need to duplicate it in another language; the value for a non-Python project is the checklist (auth, profile with timezone, app shell, admin, initial user) and the design decisions (root redirect, logout via POST, two layouts, etc.).
- Implement the same **contract**: authenticated users, profile with timezone, app shell with sidebar, admin linked to app, idempotent initial user. Map stack-specific details (e.g. ASP.NET Core Identity, Express + Passport, Next.js auth) to that contract.

---

## 7. References in This Repo

| Document | Content |
|----------|---------|
| [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md) | Design decisions for the baseline (profile shape, redirect, logout, shell, admin, initial user). |
| [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md) | Django implementation: project structure, users app, profile, auth, base templates, admin, setup command. Section 13 = order, Section 14 = batches and verification. |
| [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) | Baseline is plan 1; then biz domain, images, data interface, wkhtmltopdf, document features, signing. |
| [KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) | The overall pattern; assumes this baseline before adding products, customers, deals, and documents. |

---

*This knowledge file describes the **foundation** for data-centric and document-centric business applications. For design decisions, see [01-BASELINE/DESIGN-BASELINE.md](../01-BASELINE/DESIGN-BASELINE.md). For the Django implementation, see [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md).*

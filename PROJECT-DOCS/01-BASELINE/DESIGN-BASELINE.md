# Design: Application Baseline (Foundation for Data-Centric and Document-Centric Apps)

This document captures the **design** for the application baseline: authentication, user profile (with timezone), app shell (base layout and navigation), admin integration, and initial user. It is the foundation that all later plans (business domain, images, data interface, documents, signing) assume. Implementation in this repo follows [10-PLAN-BASELINE.md](10-PLAN-BASELINE.md) (Django).

**Knowledge:** [GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md) describes the principles and capabilities that the baseline must provide; it is technology-agnostic so that the same foundation can be implemented in other stacks. This design states the **decisions** that any implementation should satisfy.

---

## Scope

- **In scope:** Authentication (login, session, logout); user profile with display info and timezone; app shell (base templates: sidebar + content for app pages, minimal layout for login/logged-out); admin area linked to the app; initial user created via a repeatable, idempotent step.
- **Out of scope:** Business domain (products, customers, deals), images, data interface, document templates, signing. Those are defined in their respective DESIGN and PLAN files.

---

## Assumed Platform

None. The baseline is **plan 1** in [70-PLAN-MASTER.md](../70-PLAN-MASTER.md); it is implemented first. All other designs assume this baseline is in place.

---

## 1. User and Profile

- **User model:** One logical user per identity. Use the framework’s built-in user model in v1 (e.g. Django’s `User`) to keep the plan simple; no custom user model required initially.
- **Profile:** Extension of the user (e.g. OneToOne relation) holding:
  - **Display name** — first name, last name, full name (stored or computed from first + last).
  - **Contact** — email, phone number.
  - **Timezone** — IANA timezone name (e.g. America/New_York); used app-wide for date/time display (deal dates, document dates, etc.). Default for new users; user can change it in profile edit.
- **Convention:** Prefer one source of truth for display (e.g. profile); optionally sync with the built-in user for consistency with auth/admin. Timezone is activated per request (e.g. middleware or request context) so all templates and formatting use the user’s local time.

---

## 2. Authentication and Navigation

- **Root URL:** If authenticated → redirect to profile (or main app home). If not authenticated → redirect to login. No content at root until the user is in one of these states.
- **Login:** Dedicated login page; after successful login, redirect to profile (or configured home). Use the framework’s standard auth views where possible.
- **Logout:** **POST only.** Logout must not be triggered by a plain GET link (e.g. to avoid CSRF or framework restrictions). Use a form that POSTs to the logout URL with a CSRF token and a submit button styled as a nav link so the menu stays consistent.
- **Protected views:** All main app views (profile, and later products, customers, deals, documents) require an authenticated user. Unauthenticated requests redirect to login.

---

## 3. App Shell and Layout

- **App pages** (profile and all future feature pages): Use a **single base template** with:
  - **Sidebar** — Fixed (e.g. left), with brand/app name, navigation links (e.g. Profile, Admin, Log out), and a content area. Layout should match or align with the admin area so the app and admin feel like one product.
  - **Content area** — Page title (block or variable) and main content (block). Messages (e.g. success after save) displayed in the content area.
- **Login and logged-out pages:** Use a **minimal** base template (e.g. centred card, no sidebar). The user is not yet in the app workflow; avoid showing the full shell until authenticated.
- **Display name:** A single app display name (e.g. “Vehicle Leasing”) used in the shell (sidebar brand) and in the admin (site title/header). Set in one place so it stays consistent.

---

## 4. Admin Integration

- **Admin area:** Separate area for user/group management (and optionally other config). Accessible to staff users. Use the framework’s admin or a back-office UI that provides equivalent capability.
- **Navigation between app and admin:** From the app sidebar, a link to the admin (e.g. “Admin”). From the admin, a link back to the app (e.g. “Back to app” in the admin sidebar) and a link to the user’s profile (e.g. person icon in the admin header → profile page). This keeps the app and admin connected; users do not rely on the browser back button to switch.

---

## 5. Initial User

- **Mechanism:** A repeatable, idempotent step (e.g. management command, migration with RunPython, or seed script) that creates the first user and profile if they do not exist. Running the step again must not duplicate users or break data.
- **Data:** First user has a known username and password (document that production must use strong passwords and env-based secrets). Profile fields populated per design (name, contact, timezone). User is staff (and optionally superuser) so they can access admin and all app features.
- **When to run:** Documented in the implementation plan (e.g. after migrations, before first run). Part of “setup from scratch” so new developers and new environments can bootstrap the app reliably.

---

## 6. Relation to Other Designs

- **DESIGN-BIZ-DOMAIN,** **DESIGN-IMAGES,** **DESIGN-DATA-INTERFACE,** **DESIGN-DOCS** (and SIGNiX designs) all assume this baseline: users app (or equivalent), auth, base templates, profile with timezone. They extend the shell with new sidebar links and new content; they do not replace auth or layout.
- **[70-PLAN-MASTER.md](../70-PLAN-MASTER.md):** Baseline is plan 1. After [10-PLAN-BASELINE.md](10-PLAN-BASELINE.md), implement [02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md](../02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md), then [03-IMAGES/10-PLAN-ADD-IMAGES.md](../03-IMAGES/10-PLAN-ADD-IMAGES.md), [04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md](../04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md), then [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md), then document and signing plans.

---

## 7. Implementation

- **In this repo:** [10-PLAN-BASELINE.md](10-PLAN-BASELINE.md) — Django project structure, `apps.users`, `LeaseOfficerProfile` model, auth URLs, base templates (`base.html`, `base_plain.html`), profile views and forms, admin theme (Jazzmin), custom_links and person-icon override, setup command. Section 13 = implementation order; Section 14 = batches and verification. Django-specific details (Jazzmin `custom_links` dict, logout POST form, template paths) stay in the plan.
- **In another stack:** Use this design as the contract (user + profile, timezone, root redirect, logout via POST, two layouts, admin linked to app, idempotent initial user). Implement with the equivalent of your framework’s auth, admin, and templates.

---

## Decisions Log

### Built-in user + profile (no custom user in v1)

Use the framework’s built-in user model; extend with a OneToOne (or equivalent) profile for display name, contact, and timezone. Keeps the baseline simple and avoids migration complexity. A custom user model can be a later refactor if needed.

### Profile timezone for app-wide date display

Profile stores an IANA timezone; it is activated per request (e.g. middleware) so that all date/time display in the app uses the user’s local time. Deal dates, document version dates, and signing timestamps are shown consistently without ad-hoc conversion.

### Logout via POST only

Logout is triggered by a POST request (form with CSRF token), not a GET link. Aligns with framework security and avoids 405 or CSRF issues. The nav “Log out” is a submit button styled to match other sidebar links.

### Two base templates (app shell vs plain)

App pages use a base with sidebar + content; login and logged-out use a minimal base (no sidebar). Keeps auth pages simple and avoids showing the full shell before the user is authenticated.

### Admin and app linked

“Back to app” and “Profile” (or equivalent) in the admin sidebar/header so users can move between app and admin without losing context. The app and admin feel like one product.

### Idempotent initial user

The step that creates the first user (and profile) is idempotent: running it again does not create duplicates or fail. Supports “setup from scratch” and repeatable onboarding.

---

*End of design. Implementation in this repo follows [10-PLAN-BASELINE.md](10-PLAN-BASELINE.md). For principles and capabilities (technology-agnostic), see [GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md).*

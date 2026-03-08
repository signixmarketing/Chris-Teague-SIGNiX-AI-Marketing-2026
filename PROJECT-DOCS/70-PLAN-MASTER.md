# Plan Master — Implementation Order

This document defines the order in which to implement all PLANs to build (or rebuild) the lease origination app. Follow the plans in sequence. Each plan is self-contained with its own batches and verification steps.

**Usage:** Implement each plan below in order. Within each plan, follow its Implementation Order (Section 6) and Batches/Verification (Section 6a or equivalent). Do not skip ahead—later plans depend on the foundation and features from earlier plans.

---

## 1. 01-BASELINE/10-PLAN-BASELINE.md

**Purpose:** Foundation of the app—Django project, venv, users app with LeaseOfficerProfile, auth (login/logout), base templates (base.html, base_plain.html), profile view/edit, initial user (karl), and Admin with Jazzmin.

**Design:** 01-BASELINE/DESIGN-BASELINE.md. **Knowledge:** GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md.

**Implement:** Batch 1 (venv, project bootstrap, users app, model, migrations, setup_initial_user) then Batch 2 (auth, base template, profile views, URLs, admin base override). See 01-BASELINE/10-PLAN-BASELINE.md Section 13 and Section 14.

---

## 2. 02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md (Vehicles, Contacts, Deals)

**Purpose:** Core business domain entities and their management UI—**Vehicles**, **Contacts**, and **Deals**. Implement the three plans in the order defined in **02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md**: PLAN-ADD-VEHICLES (Vehicle model, CRUD, seed jet pack), PLAN-ADD-CONTACTS (Contact model, CRUD, seed contact), PLAN-ADD-DEALS (DealType and Deal with lease_officer, deal_type, vehicles/contacts M2M, View/Edit split, CRUD). Deals depend on Vehicles and Contacts.

**Design:** 02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md. **Knowledge:** GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md, 02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md.

**Implement:** Follow 02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md. For step 2, implement the three plans in that phase plans document in order: Vehicles → Contacts → Deals. Each of the three plans uses two batches (data layer then UI); see the individual plan files (Section 6 and Section 6a) for verification steps.

---

## 3. 03-IMAGES/10-PLAN-ADD-IMAGES.md

**Purpose:** Images app—Image model (name, file with upload_to under media/images/, stable URL via uuid), CRUD (list with URL column, add, edit with current image and optional replacement, delete with file cleanup). MEDIA_ROOT/MEDIA_URL, serve media in dev. Pillow required.

**Design:** 03-IMAGES/DESIGN-IMAGES.md. **Knowledge:** GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md.

**Implement:** Batch 1 (apps.images, media config, model, migrations) then Batch 2 (forms with file upload, views, URLs, templates, sidebar, optional admin). Single "Add image" button in header only—no duplicate below table when empty. See 03-IMAGES/10-PLAN-ADD-IMAGES.md Section 6 and Section 6a.

---

## 4. 04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md

**Purpose:** Data schema and deal data interface—apps.schema with `get_schema()`, `get_paths()`, `get_deal_data(deal)`. Schema viewer page, Debug Data page (deal list with View JSON modal). Foundation for dynamic document templates (mapping, context builder).

**Design:** 04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md. **Knowledge:** GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md (§4 — schema and deal data as single source for documents).

**Implement:** Batch 1 (app, services.py, schema discovery and get_deal_data, URL routing), Batch 2 (schema viewer view, template, sidebar), Batch 3 (Debug Data list, JSON endpoint, modal with Copy). See 04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md Section 7 and Section 7a.

---

## Setup: wkhtmltopdf (before Document Features)

**Purpose:** Dynamic document generation (PHASE-PLANS-DOCS, plan 4 — Document Sets) requires **wkhtmltopdf** on the system and **pdfkit** in the Python environment. Do this setup **after** plans 1–4 and **before** starting PHASE-PLANS-DOCS so that when you implement PLAN-ADD-DOCUMENT-SETS, the HTML-to-PDF pipeline is ready.

**Implement:** Follow **05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md**: run the “already installed” check (Section 3.0); if wkhtmltopdf is not installed, run Batches 1–2 (install wkhtmltopdf, then ensure pdfkit is present and `manage.py check` passes). Do not duplicate steps that are already covered by PLAN-ADD-DOCUMENT-SETS (e.g. pip install of requirements). See 05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md for when to skip each batch. **Enabler docs:** Data interface (DESIGN-DATA-INTERFACE, PLAN-DATA-INTERFACE), Images (DESIGN-IMAGES, PLAN-ADD-IMAGES; KNOWLEDGE-FILE-ASSETS-MEDIA), HTML-to-PDF (SETUP-WKHTMLTOPDF, KNOWLEDGE-HTML-TO-PDF).

---

## Summary Table

| Order | Plan                       | App(s)           | Key deliverables                                                                 |
|-------|----------------------------|------------------|-----------------------------------------------------------------------------------|
| 1     | 01-BASELINE/10-PLAN-BASELINE.md           | apps.users       | Auth, profile, base templates, karl user                                          |
| 2     | 02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md  | vehicles, contacts, deals | Vehicles, Contacts, Deals (see phase plans for sequence and deliverables)        |
| 3     | 03-IMAGES/10-PLAN-ADD-IMAGES.md         | apps.images      | Image upload, list with URL, edit with replacement                               |
| 4     | 04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md     | apps.schema      | Schema viewer, Debug Data page, get_schema/get_paths/get_deal_data                |

*Then:* **05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md** (wkhtmltopdf + pdfkit for dynamic document generation) — before Document Features.

**Phase plans** (group related plans into a single sequence):
- **02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md** — Vehicles, Contacts, Deals (implementation order).
- **06-DOCS/PHASE-PLANS-DOCS.md** — Document templates and document sets (see Next Steps: Document Features).
- **07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md** — SIGNiX submit flow (see Next Steps: SIGNiX Submit).
- **09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md** — Push, sync, download, transaction detail (see Next Steps: Dashboard, Sync, and Download).

---

## Next Steps: Document Features

Once plans 1–4 above are completed, complete **05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md** (if not already done) so wkhtmltopdf and pdfkit are available for dynamic document generation. Then proceed to **06-DOCS/PHASE-PLANS-DOCS.md** for document-related features (Static Document Templates, Dynamic Document Templates, Document Set Templates, Document Sets with Generate/Regenerate and Send for Signature stub). See 06-DOCS/PHASE-PLANS-DOCS.md for the implementation sequence. PHASE-PLANS-DOCS item 5 (SIGNiX integration) is superseded by the next step.

---

## Next Steps: SIGNiX Submit

Once PHASE-PLANS-DOCS plans 1–4 are completed (Document Sets includes the Send for Signature stub), proceed to **07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md** for the SIGNiX submit flow: configuration, signer identification, transaction packager, Send for Signature (replace stub), signature transactions dashboard, and related transactions on Deal View. Implement the nine plans (PLAN-SIGNiX-CONFIG through PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS) in the order defined in 07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md.

---

## When ready: ngrok for push notifications

When you are ready to implement SIGNiX **push notifications** (webhooks), follow **08-NGROK/10-PLAN-NGROK.md**. That plan covers installing ngrok (if needed), claiming or using your ngrok domain, and **all codebase changes** required for the app to work through the tunnel (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, PDF_IMAGE_BASE_URL, health endpoint, launch config, scripts). Use it for from-scratch builds as well: a different developer on a different machine substitutes their ngrok domain and authtoken; the code changes stay the same.

---

## Next Steps: Dashboard, Sync, and Download

**Completed.** **09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md** has now been implemented end-to-end: push-driven status, the push listener, the push URL in SubmitDocument, the Signers column on the dashboard and Deal View, downloading signed documents plus audit trail and certificate when transactions complete, and the signature transaction detail page (including artifact viewing).

---

*To recreate this app from scratch: implement plan 1 (PLAN-BASELINE), then the plans in 02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md (Vehicles, Contacts, Deals) in order, then plans 3–4 (Images, Data Interface), following each plan's implementation order and verification steps. Then complete 05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md (wkhtmltopdf + pdfkit) so dynamic document generation is ready. Then implement the plans in 06-DOCS/PHASE-PLANS-DOCS.md (plans 1–4). Then implement the plans in 07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md (plans 1–9). When you are ready to implement SIGNiX push notifications, follow 08-NGROK/10-PLAN-NGROK.md (ngrok tunnel and codebase changes). Then implement the plans in 09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md (plans 1–6) for push-driven status, the push listener, push URL in SubmitDocument, Signers column, download on complete (including audit trail and certificate), and signature transaction detail page (viewing artifacts). This dashboard/sync track is complete in the current codebase.*

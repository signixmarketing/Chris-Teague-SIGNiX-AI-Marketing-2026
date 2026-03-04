# Plan SIGNiX Submit Master — Implementation Order

This document defines the order in which to implement the **submit flow** from **DESIGN-SIGNiX-SUBMIT.md**: configuration, signer identification, transaction packager (build body, send, persist), Send for Signature on Deal detail, and signature-transaction tracking (dashboard and Deal View table). Each plan covers a specific feature or layer; dependencies are implemented first so that testing can progress incrementally.

**Usage:** Implement each plan below in sequence. Within each plan, follow its Implementation Order and Batches/Verification. Do not skip ahead—later plans depend on earlier ones.

**Source of truth:** DESIGN-SIGNiX-SUBMIT.md. Refer to it for data sourcing (Section 6.1.1), validation rules, and UI placement. KNOWLEDGE-SIGNiX.md for Flex API structure and field notes.

---

## Prerequisites

- **PLAN-MASTER** plans 1–6 are implemented (Baseline, Vehicles, Contacts, Deals, Images, Data Interface). Deals includes Deal Type and the deal detail page (View/Edit split). Data Interface provides `get_deal_data(deal)`.
- **PLAN-DOCS-MASTER** plans 1–4 are implemented: Static Document Templates, Dynamic Document Templates, Document Set Templates, **Document Sets** (Generate/Regenerate/Delete, Documents section on Deal detail, **Send for Signature stub**). The stub is replaced in Plan 7 below.

---

## 1. PLAN-SIGNiX-CONFIG.md

**Purpose:** SIGNiX configuration—model and administrative UI so credentials and submitter information are stored and available to the transaction packager. No submit flow yet; only the ability to create/edit one configuration record.

**Deliverables:** `SignixConfig` model (singleton or single-record: sponsor, client, user_id, password, workgroup; demo_only; delete_documents_after_days; default_email_content; submitter_first_name, submitter_middle_name, submitter_last_name, submitter_email, submitter_phone). Migrations. Administrative UI (SIGNiX Configuration page): credentials, submitter fields, demo only, delete documents after, default email content. Access restricted (e.g. staff). Validation: submitter email required when used for submit (can be enforced in this plan or in the submit view).

**Dependencies:** None (foundation for all SIGNiX submit features).

**Implement:** Batches as defined in the plan (e.g. model + migration, then UI). Verification: config can be saved and loaded; submit flow will read from it later.

---

## 2. PLAN-SIGNiX-SIGNATURE-TRANSACTION.md

**Purpose:** Local record for each transaction submitted to SIGNiX—model and relations so the app can persist DocumentSetID, first-signing URL, status, and link to Deal and Document Set.

**Deliverables:** `SignatureTransaction` model in `apps.deals` (deal, document_set, signix_document_set_id, transaction_id, status, first_signing_url, submitted_at, completed_at). Migration. Deal relation (`related_name='signature_transactions'`). No list/detail UI yet; that comes in Plans 8 and 9.

**Dependencies:** None (model only; DocumentSet exists from PLAN-ADD-DOCUMENT-SETS).

**Implement:** Batches as defined in the plan. Verification: model can be created and queried; Deal detail can prefetch/filter signature_transactions.

---

## 3. PLAN-SIGNiX-SIGNER-SERVICE.md

**Purpose:** Signer identification and slot→person resolution—service layer that the Signers table and transaction packager both use. No UI in this plan.

**Deliverables:**  
- **`get_signers_for_document_set_template(document_set_template)`** — Returns ordered list of signer slot numbers (e.g. `[1, 2]`) from the template’s items and their `tagging_data` `member_info_number` values.  
- **Slot→person resolution** — Given a deal and a slot number, return the person (first_name, middle_name, last_name, email, phone as needed). Convention: slot 1 = lease officer (User/LeaseOfficerProfile), slot 2 = first contact (deal.contacts ordered by id; first contact). Same convention used by Signers table and packager.  
- Module location: e.g. `apps.deals.signix` or `apps.documents.signix` (per design open issue).  
- Unit tests: signer slots from template; slot→person for deal with lease officer and contact.

**Dependencies:** Document Set Templates and document templates (Static/Dynamic) with `tagging_data`; Deal, Contact, User/LeaseOfficerProfile. No dependency on SignixConfig or SignatureTransaction.

**Implement:** Batches: (1) get_signers_for_document_set_template and tests, (2) slot→person resolution and tests. Verification: service returns correct slots and resolved person data for a known deal/template.

---

## 4. PLAN-SIGNiX-SIGNERS-TABLE.md

**Purpose:** Signer order and authentication storage, and the Signers table on Deal View—so users can see who will sign, reorder them, and set authentication per signer before submitting.

**Deliverables:**  
- **Storage for signer order and authentication** — Store on **Deal** (Design Section 9.6): add fields `signer_order`, `signer_authentication` (JSONFields). Default order from `get_signers_for_document_set_template`; default auth: user → SelectOneClick, contact → SMSOneClick.  
- **Signers table on Deal View** — Placement (e.g. above or below deal summary). Columns: Order, Role, Name, Email, (optional phone), Authentication (dropdown: SelectOneClick, SMSOneClick). Data from signer service + slot→person. Reorder (persist order), change auth (persist per slot). When to show: when deal has a deal type with a document set template (if deal has document set, use its template; else template for deal_type).  
- Views/forms/URLs to load and save order and authentication.

**Dependencies:** Plan 3 (signer service and slot→person resolution). Deal detail page and Document Sets exist.

**Implement:** Batches: (1) storage fields + migration and read/write helpers, (2) Signers table UI and reorder/auth POST. Verification: table shows correct signers; reorder and auth change persist and are used later by packager.

---

## 5. PLAN-SIGNiX-BUILD-BODY.md

**Purpose:** Build the SubmitDocument request body (XML) from deal, document set, and configuration—without sending to SIGNiX. Enables unit testing of payload and debugging (e.g. dump XML).

**Deliverables:**  
- **`build_submit_document_body(deal, document_set, ...)`** — Returns full SubmitDocument XML string (and optionally metadata e.g. TransactionID). Uses SignixConfig (CustInfo, submitter, Data-level defaults), signer order and authentication (Plan 4), slot→person (Plan 3), document_set instances and latest version PDFs, template tagging_data for Form structure. All data sourcing per DESIGN-SIGNiX-SUBMIT Section 6.1.1.  
- Django template (DTL) for the request XML; data dict built from config + deal + document_set + signers.  
- Validation helper used by this function: document set belongs to deal; instances present; latest version has file; all signer slots resolved to a person; SignixConfig present with submitter email.  
- Unit tests: assert on structure and key values in built XML (no HTTP). Optional: management command or debug view to dump body without sending.

**Dependencies:** Plans 1 (SignixConfig), 3 (signer service, slot→person), 4 (signer order/auth storage). Plan 2 (SignatureTransaction) not required for building body but needed for the next plan. Document Sets with instances and versions (PLAN-ADD-DOCUMENT-SETS).

**Implement:** Batches: (1) data dict builder and validation, (2) template and build_submit_document_body, (3) tests and optional dump command. Verification: for a fixture deal/document_set/config, built XML contains expected CustInfo, Data (TransactionID, DocSetDescription, Submitter*), MemberInfo count and order, Form count.

---

## 6. PLAN-SIGNiX-SEND-AND-PERSIST.md

**Purpose:** Send the built body to SIGNiX (POST), parse response, call GetAccessLink if needed, create SignatureTransaction, and update DocumentInstanceVersion status to “Submitted to SIGNiX”.

**Deliverables:**  
- **Send function** — e.g. `send_submit_document(body, endpoint_url, credentials)` or `post_to_signix(body)`; POST to Webtest or Production per SignixConfig.demo_only; parse response with ElementTree; extract DocumentSetID and first-signer link if present.  
- **GetAccessLink** — If response does not include first-signing URL, call GetAccessLink for the first signer; use returned URL for first_signing_url.  
- **Orchestrator** — Validates (reuse validation from Plan 5), calls build_submit_document_body, (optionally logs/stores body), calls send, parses response, GetAccessLink if needed, creates SignatureTransaction (deal, document_set, signix_document_set_id, transaction_id, status=Submitted, first_signing_url, submitted_at), updates latest DocumentInstanceVersion per instance to status “Submitted to SIGNiX”. Returns SignatureTransaction and first_signing_url.  
- Error handling: validation errors → no HTTP; SIGNiX API errors → no create/update; user-facing message and log.  
- Integration tests: mock HTTP to SIGNiX; assert SignatureTransaction created and version status updated.

**Dependencies:** Plans 1, 2, 3, 4, 5. Document Sets with version status field.

**Implement:** Batches: (1) send + parse + GetAccessLink, (2) orchestrator + persistence, (3) error handling and tests. Verification: end-to-end with mocked SIGNiX returns success and correct DB state.

---

## 7. PLAN-SIGNiX-SEND-FOR-SIGNATURE.md

**Purpose:** Replace the Send for Signature stub on Deal detail—wire the button to the transaction packager and open the first signer’s signing URL in a separate window.

**Deliverables:**  
- **Replace stub** — POST to same URL (or renamed) calls orchestrator (Plan 6). On success: create transaction, return first_signing_url; front end opens URL in new window (e.g. `window.open(first_signing_url)` or link `target="_blank"`). On failure: show error message, stay on deal detail.  
- **Button visibility** — Show when document set exists with at least one instance, SignixConfig present, and validation would pass (all signer slots resolved, submitter email configured). Disable or show message when config missing.  
- Optional: server redirect to a small “Sign in new window” page that opens the URL via script (alternative to returning URL to front end).

**Dependencies:** Plan 6 (orchestrator). Plan 4 (Signers table) so user can see and adjust signers before submit; validation uses signer service and config.

**Implement:** Batches: (1) view + response (return URL or redirect), (2) front-end open in new window, (3) button visibility logic and tests. Verification: submit from deal detail creates SignatureTransaction and opens signing URL in new window.

---

## 8. PLAN-SIGNiX-DASHBOARD.md

**Purpose:** Signature transactions dashboard—main menu item and list view of all submitted transactions, with Delete Transaction History (all) for testing.

**Deliverables:**  
- **Main menu** — e.g. “Signature transactions” or “Signatures”; URL `/signatures/` or `/deals/signatures/`.  
- **List view** — Table: Deal (link), description/label (e.g. Deal #N – template name), SIGNiX DocumentSetID, Status, Submitted at, optional “Open link” if first signer and status Submitted/In progress.  
- **Delete Transaction History** — Button with confirmation; deletes all SignatureTransaction records. For testing.  
- Access: authenticated users only.

**Dependencies:** Plan 2 (SignatureTransaction model). Transactions are created by Plan 6/7.

**Implement:** Batches: (1) view, URL, template, sidebar link, (2) Delete all + confirmation. Verification: list shows transactions; delete clears all.

---

## 9. PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md

**Purpose:** Related signature transactions on Deal View—table under the Documents section and Delete Transaction History for this deal.

**Deliverables:**  
- **Placement** — Below Documents section as a **separate card** (Design 7.5, Plan 9). Subsection "Signature transactions" or "Related signature transactions".  
- **Table** — Columns: Submitted at, SIGNiX DocumentSetID, Status, link to “Open signing” if applicable. Link to full dashboard (“View all signature transactions”).  
- **Delete Transaction History (for this deal)** — Button with confirmation; deletes all SignatureTransaction records for this deal. Separate deal-scoped URL (GET confirm, POST delete, redirect to deal detail). For testing.  
- Deal detail template and view: add `signature_transactions` to context (or `_deal_detail_context`); ensure every path that renders deal detail, including Plan 7 re-render, includes it.

**Dependencies:** Plan 2 (SignatureTransaction, Deal relation). Plan 8 optional for “View all” link.

**Implement:** Batches: (1) table on Deal detail, (2) Delete for deal + confirmation. Verification: Deal detail shows related transactions; delete removes only this deal’s transactions.

---

## Summary Table

| Order | Plan | Key deliverables |
|-------|------|------------------|
| 1 | PLAN-SIGNiX-CONFIG.md | SignixConfig model, SIGNiX Configuration admin UI (credentials, submitter, demo_only, etc.) |
| 2 | PLAN-SIGNiX-SIGNATURE-TRANSACTION.md | SignatureTransaction model, Deal relation |
| 3 | PLAN-SIGNiX-SIGNER-SERVICE.md | get_signers_for_document_set_template, slot→person resolution, unit tests |
| 4 | PLAN-SIGNiX-SIGNERS-TABLE.md | signer_order/signer_authentication storage, Signers table on Deal View (reorder, auth dropdown) |
| 5 | PLAN-SIGNiX-BUILD-BODY.md | build_submit_document_body, validation, XML template, unit tests |
| 6 | PLAN-SIGNiX-SEND-AND-PERSIST.md | send to Flex, parse response, GetAccessLink, create SignatureTransaction, update version status |
| 7 | PLAN-SIGNiX-SEND-FOR-SIGNATURE.md | Replace Send for Signature stub, open first signer URL in new window, button visibility |
| 8 | PLAN-SIGNiX-DASHBOARD.md | Signature transactions list view, Delete Transaction History (all) |
| 9 | PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md | Related signature transactions table on Deal View (separate card), Delete for deal (deal-scoped URL), context on all deal-detail paths |

---

## Dependency Overview

```
Plan 1 (Config)          Plan 2 (SignatureTransaction model)
        \                          /
         \                        /
          v                      v
        Plan 3 (Signer service + slot→person)
                    |
                    v
        Plan 4 (Signers table + order/auth storage)
                    |
        +-----------+-----------+
        v           v           v
   Plan 5 (Build body)    [Plan 2 required for Plan 6]
        |           |
        v           v
        Plan 6 (Send + persist)
                    |
                    v
        Plan 7 (Send for Signature button)
                    |
        +-----------+-----------+
        v                       v
   Plan 8 (Dashboard)    Plan 9 (Deal View table)
```

Plans 1 and 2 have no dependencies on each other and can be implemented in either order (1 then 2 is recommended so config exists before any packager code). Plan 3 depends only on document templates and deals. Plan 4 depends on 3. Plan 5 depends on 1, 3, 4 (and 2 for persistence in 6). Plan 6 depends on 1, 2, 3, 4, 5. Plan 7 depends on 6 (and 4 for validation/UX). Plans 8 and 9 depend on 2 and are independent of each other; they are placed after 7 so the full submit flow is implemented and testable before adding list/dashboard UI.

---

## Relation to PLAN-DOCS-MASTER

**PLAN-DOCS-MASTER** item 5 (SIGNiX integration) has been replaced by a reference to this master and the nine plans above; implement document features as DOCS plans 1–4 only, then this master. DESIGN-SIGNiX-SUBMIT.md scopes the first phase to **submit only** (no push, no DownloadDocument/ConfirmDownload). This master covers that scope. Full integration (push, download, confirm) can be a later master or extension.

---

*To implement the SIGNiX submit flow: ensure PLAN-MASTER 1–6 and PLAN-DOCS-MASTER 1–4 are complete, then implement plans 1–9 above in order, following each plan’s batches and verification.*

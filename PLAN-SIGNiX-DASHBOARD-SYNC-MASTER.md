# Plan SIGNiX Dashboard and Sync Master — Implementation Order

This document defines the order in which to implement the **dashboard, event sync, download, and transaction artifact viewing** features from **DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md**: model changes for push and per-signer progress (including fields for storing the audit trail and certificate of completion), the push notification listener, including the push URL in SubmitDocument (and setting signer_count at create), the Signers column on the dashboard and Deal View, **proactively** downloading signed documents plus the audit trail and certificate when transactions complete and storing them on the transaction, and a **signature transaction detail page** (with row action from the tables) so users can view signed documents, the audit trail, and the certificate of completion. Each plan builds on the previous so that status updates and per-signer progress work before the download flow, and the download flow stores all artifacts before the detail page serves them.

**Usage:** Implement each plan below in sequence. Within each plan, follow its Implementation Order and Batches/Verification. Do not skip ahead—later plans depend on earlier ones. **Testing note:** unit tests and mocked integration tests can run without ngrok, but any manual or end-to-end verification that depends on **real SIGNiX push notifications** requires the Django app and **ngrok to be running in parallel** so the submitted callback URL is reachable from SIGNiX.

**Source of truth:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md. Refer to it for status values, action→status mapping, idempotency rules, push handler behavior, SubmitDocument client preferences, download mapping (including audit trail and certificate storage), data model (Section 7.4, 7.5), and signature transaction detail page (Section 8). KNOWLEDGE-SIGNiX.md for push format, DownloadDocument/ConfirmDownload, and Flex API details.

**Flow from design:** The plans below are derived from the design: Plan 1 adds the data model (Section 7) and event model (7.5); Plan 2 implements the listener (Section 4) and creates events per push; Plan 3 adds the push URL and submitted event (Section 5, 11); Plan 4 adds dashboard columns (Section 3); Plan 5 implements download and storage (Section 6, 7.4); Plan 6 implements the detail page (Section 8). Each plan’s implementation order uses **batches** that build on one another—complete each batch and run its verification before starting the next. Not all plan documents may be written in full yet; where a plan is summarized here, implement per the master deliverables and the design sections cited until the dedicated plan file is available.

---

## Prerequisites

- **PLAN-SIGNiX-SUBMIT-MASTER** plans 1–9 are implemented: SignixConfig, SignatureTransaction model, signer service, Signers table, build body, send and persist, Send for Signature button, signature transactions dashboard (list view), and related transactions on Deal View. The dashboard and Deal View tables exist but do not yet show live status from push or the Signers column.
- **PLAN-NGROK** has been applied so the app is reachable at an HTTPS URL (e.g. ngrok tunnel). The push listener will be called by SIGNiX at that URL.
- **Implementation testing requirement:** when running any verification that expects **real** SIGNiX callbacks (for example, sending a transaction and waiting for SIGNiX to call `/signix/push/`), keep **Django and ngrok running in parallel**. Without the active tunnel, the application will not receive the push notifications. Pure unit tests and mocked tests do not require ngrok.

---

## 1. PLAN-SIGNiX-SYNC-MODEL.md

**Purpose:** Add the model fields and status value required for push-driven status and per-signer progress. No listener or UI yet; this plan only adds the schema and migrations.

**Deliverables:**
- **SignatureTransaction** — Add **signer_count** (PositiveSmallIntegerField, nullable); **signers_completed_refids** (JSONField, list of strings, default=list); **signers_completed_count** (PositiveSmallIntegerField, default=0); **status_last_updated** (DateTimeField, nullable). Add **Expired** to the status choices if not already present (allowed values: Submitted, In Progress, Complete, Suspended, Cancelled, Expired). Add **audit_trail_file** and **certificate_of_completion_file** (FileField, blank=True, upload_to e.g. `"signature_transactions/%Y/%m/"`) so that when a transaction completes, Plan 5 can store the audit trail and certificate of completion PDFs on the transaction; the signature transaction detail page (Plan 6) then serves these already-stored files with no on-demand fetch.
- **SignixConfig** — Add **push_base_url** (CharField or URLField, nullable, blank=True). When set, SubmitDocument will include TransactionClientNotifyURL; when blank, client preferences are omitted. The app can **derive** the push base URL from the request when submit is triggered from a view (see DESIGN-SIGNiX-DASHBOARD-AND-SYNC Section 5.2), so this field is an **optional override** (e.g. for headless submit); no admin field is required for typical use.
- **SignatureTransactionEvent** — New model (DESIGN Section 7.5) for **event history** per transaction: so the detail page can show a chronological timeline (Transaction submitted → push events → Transaction completed) and "when each signer signed" from party_complete events. Plan 2 creates an event for each push; Plan 3 creates the initial **submitted** event when the transaction is created.
- Migrations for all of the above. No changes to views or submit flow in this plan.

**Dependencies:** PLAN-SIGNiX-SUBMIT-MASTER (SignatureTransaction and SignixConfig already exist).

**Implement:** Batches: (1) SignatureTransaction fields + Expired status, migration and data backfill; (2) SignixConfig.push_base_url, migration; (3) SignatureTransactionEvent model, migration. Verification after each batch: migrations run; new fields nullable/defaulted so existing data and submit flow remain valid.

---

## 2. PLAN-SIGNiX-PUSH-LISTENER.md

**Purpose:** Implement the push notification endpoint that SIGNiX calls when events occur (Send, partyComplete, complete, suspend, cancel, expire). **The system listens to these push notifications and updates the number of signers who have completed whenever SIGNiX notifies it** (on partyComplete or complete), so the dashboard Signers column stays in sync. Update transaction status and per-signer progress; return 200 OK quickly; for action=complete, trigger the download flow asynchronously (implemented in Plan 5; this plan wires the trigger or a no-op stub).

**Deliverables:**
- **URL and view** — GET **/signix/push/** (no auth). Parse query parameters: action, id, extid; optional pid, refid, ts. Use **get_signature_transaction_for_push(id, extid)** to look up SignatureTransaction; if None, log and return 200 OK with body "OK". Use **apply_push_action(transaction, action, refid=..., pid=..., ts=...)** then save; return 200 OK "OK".
- **Status update** — (In **apply_push_action**.) Map action to status per design (Section 3.1); apply idempotently (do not overwrite terminal states). Set **status_last_updated** and completed_at when action=complete (from ts or now). Set **status_last_updated** whenever the helper mutates status, signer progress, or completed_at (to event time: ts or now).
- **Record event** — After saving the transaction, **create a SignatureTransactionEvent** (DESIGN Section 7.5) for this push: event_type from action (Send→send, partyComplete→party_complete, complete→complete, suspend→suspend, cancel→cancel, expire→expire), occurred_at from push ts or now, refid and pid when present. So the detail page can show the full event timeline and "when each signer signed."
- **Per-signer progress** — (In **apply_push_action**.) For action=partyComplete: if refid (or pid if refid absent) not in signers_completed_refids, append it and set signers_completed_count = len(signers_completed_refids); update status to In Progress if not terminal. For action=complete: set signers_completed_count = signer_count if not already equal.
- **Response** — Return HTTP 200 with body exactly "OK". Respond within a few hundred milliseconds.
- **Async trigger for complete** — For action=complete, after responding, call **download_signed_documents_on_complete(transaction)** asynchronously (Plan 5 implements it; this plan may call a stub that Plan 5 will replace). Do not block the GET handler.
- **CSRF** — Exempt the push view from CSRF (GET is typically not checked; if the app applies CSRF to all views, exempt this one).
- URL routing (e.g. in apps.deals or a dedicated signix URLconf).

**Dependencies:** Plan 1 (model fields exist).

**Implement:** Batches: (1) add **get_signature_transaction_for_push**, **get_event_time_for_push**, **push_action_to_event_type**, and **apply_push_action** (DESIGN 4.4), push view that parses params, calls them, saves, **creates SignatureTransactionEvent per push**, returns 200 OK; (2) CSRF exempt, async call to download_signed_documents_on_complete (stub until Plan 5). Verification: GET with action=complete&id=...&extid=... updates transaction and returns 200 OK; duplicate push does not overwrite terminal status; event created for push. **For any end-to-end verification with real SIGNiX pushes, Django and ngrok must both be running and the callback URL must point at the active ngrok domain.**

---

## 3. PLAN-SIGNiX-SUBMIT-PUSH-URL.md

**Purpose:** Include the push notification URL in every SubmitDocument request (so SIGNiX can send webhooks to this app) and set signer_count when creating a SignatureTransaction. Requires the listener (Plan 2) to be in place so SIGNiX can reach the endpoint once we send the URL.

**Deliverables:**
- **SignixConfig** — Add **push_base_url** to the admin/config UI as an **optional override** (Plan 1 adds the model field). **Preferred:** derive push_base_url from **request.build_absolute_uri('/').rstrip('/')** when the view that triggers submit has a request—no user input needed. **On the config form:** When the page opens, pass get_push_base_url(request) to the template and display it next to the field (e.g. “When blank, app will use: &lt;derived&gt;/signix/push/”) so the user sees the effective default. When push_base_url is still blank after resolution, fallback from settings.SIGNIX_PUSH_BASE_URL or NGROK_DOMAIN if present.
- **build_submit_document_body** (or data dict) — Accept optional **push_base_url**. When provided, include ClientPreference UseClientNotifyVersion2=yes and TransactionClientNotifyURL=push_base_url + "/signix/push/" (no double slash). When not provided, do not add these elements.
- **Orchestrator** (or view that calls the packager) — Call get_push_base_url(request) and pass the result into build_submit_document_body (helper in DESIGN Section 5.4). When creating SignatureTransaction, set **signer_count** to the number of signers (e.g. len(signer_order) or number of MemberInfo elements). **Create the initial SignatureTransactionEvent** (event_type=**submitted**, occurred_at=submitted_at). **Ensure** the latest DocumentInstanceVersion per instance is marked status **"Submitted to SIGNiX"** (so the detail page can link to "document as sent"); this is already done in the existing orchestrator per PLAN-SIGNiX-SEND-AND-PERSIST.
- Tests: with push_base_url set, built XML contains the two ClientPreference elements; new SignatureTransaction has signer_count set; transaction has one "submitted" event.

**Dependencies:** Plan 1 (SignixConfig.push_base_url, SignatureTransaction.signer_count). Plan 2 should be deployed so that when new transactions are submitted with the URL, SIGNiX can call the listener. For real callback verification during implementation, the listener must be reachable through an **active ngrok tunnel**.

**Implement:** Batches: (1) add get_push_base_url(request=None) helper (DESIGN 5.4) and body builder accepts push_base_url, adds ClientPreference elements; (2) orchestrator and config form call get_push_base_url(request), sets signer_count on create, creates submitted event, ensures versions "Submitted to SIGNiX". Verification: submit creates transaction with signer_count and one submitted event; built body includes TransactionClientNotifyURL when push_base_url is set. **If verification includes SIGNiX actually calling back after submit, run Django and ngrok in parallel and submit an ngrok-backed callback URL.**

---

## 4. PLAN-SIGNiX-DASHBOARD-SIGNERS.md

**Purpose:** Add the **Signers** column (e.g. "0/2", "1/2", "2/2") and the **Status updated** column (when the current status was last updated, from status_last_updated) to the signature transactions list view and to the Deal View related-transactions table. Status column already exists; it will now be updated by the push listener (Plan 2). This plan adds the Signers and Status updated columns and ensures null-safe display. **Plan 1’s data migration** sets status_last_updated = submitted_at for existing transactions, so migrated rows show a consistent Status updated value; the display helper shows "—" only when status_last_updated is null (edge case).

**Deliverables:**
- **Dashboard list view** — Add **Signers** column: use **get_signers_display(transaction)** (DESIGN 3.4) to show "1/2", "2/2", or "—" when signer_count is null. Add **Status updated** column: show formatted date/time from **status_last_updated** (migrated rows have this set to submitted_at by Plan 1); when null show "—". Column placement per design (e.g. after Status).
- **Deal View related table** — Add same **Signers** and **Status updated** columns; use **get_signers_display(transaction)** and get_status_updated_display(transaction) so formatting is consistent.
- Template and view context: pass the transaction and the display helpers; use get_signers_display(transaction) and get_status_updated_display(transaction) in template.

**Dependencies:** Plan 1 (fields exist; data migration sets status_last_updated = submitted_at for backfilled rows). Plan 2 and 3 populate the fields (listener updates counts; submit sets signer_count). No dependency on Plan 5.

**Implement:** Batches: (1) dashboard list template + view update (Signers and Status updated columns); (2) Deal View table template + context. Verification: list and Deal View show Signers and Status updated columns; legacy transactions (signer_count null) show "—" for Signers; backfilled transactions show Status updated = submitted_at; null status_last_updated shows "—".

---

## 5. PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md

**Purpose:** When a push with action=complete is received, after returning 200 OK, run the download flow asynchronously: call DownloadDocument (requesting the audit trail and optional certificate of completion), map returned signed documents to the transaction's document_set instances, create new DocumentInstanceVersions (status=Final, file=signed PDF), **store the audit trail and certificate of completion PDFs on the SignatureTransaction** (DESIGN Section 6.5a, 7.4), then call ConfirmDownload. Storage is **proactive**—done in this flow so the signature transaction detail page (Plan 6) only serves already-stored files; the system does not retrieve them when the user visits that page. Idempotent: skip if already processed (e.g. Final versions already created for this transaction).

**Deliverables:**
- **download_signed_documents_on_complete(transaction)** — Single callable (DESIGN Section 6) that performs: idempotency check (skip if already processed), DownloadDocument with **IncludeAuditData** and **AuditTrailFormat** (e.g. pdf) and optional certificate-of-completion element (KNOWLEDGE-SIGNiX, Flex API), parse response, map signed documents to document_set.instances by order or RefID per Flex API, create new DocumentInstanceVersion per instance (file=signed PDF bytes, status=Final, version_number=next), **extract audit trail and certificate PDFs from response and save to transaction.audit_trail_file and transaction.certificate_of_completion_file** (Section 6.5a), then ConfirmDownload. Called from the push listener (Plan 2) when action=complete; run asynchronously (e.g. threading.Thread or fire-and-forget). Celery not required.
- **Wire from listener** — Plan 2's async trigger for action=complete invokes this task (replace stub if present).
- **Error handling** — Log DownloadDocument or ConfirmDownload failures; do not retry from the view. If parsing or saving audit trail/certificate fails, log but do not fail the rest of the flow (signed versions and ConfirmDownload still proceed). Document partial mapping behavior if document count does not match.
- KNOWLEDGE-SIGNiX and Flex API documentation for DownloadDocument request/response (signed docs, audit trail, certificate of completion).

**Dependencies:** Plan 1 (SignatureTransaction, including audit_trail_file and certificate_of_completion_file; document_set relation). Plan 2 (listener triggers the task on action=complete). DocumentInstanceVersion model and document_set.instances exist from PLAN-ADD-DOCUMENT-SETS.

**Implement:** Batches: (1) DownloadDocument client call (include audit trail and certificate in request) and response parsing (signed docs + audit trail + certificate); (2) mapping to instances, create DocumentInstanceVersions, save audit_trail_file and certificate_of_completion_file on transaction, ConfirmDownload; (3) **download_signed_documents_on_complete(transaction)** that does all of the above with idempotency check, wire from push listener; (4) async execution (thread or fire-and-forget). Verification: on action=complete, signed documents are stored as new versions with status Final, audit trail and certificate are stored on the transaction when present in the response, and ConfirmDownload is called. **When verifying this flow via real SIGNiX completion pushes, Django and ngrok must both be running so the `complete` callback reaches `/signix/push/`.**

---

## 6. PLAN-SIGNiX-TRANSACTION-DETAIL.md

**Purpose:** Provide a **signature transaction detail page** that is a **living representation** of the transaction (DESIGN Section 8). Users see what was sent to SIGNiX, status and when it was last updated, signers (with who signed and when), documents as sent vs signed, a chronological event timeline, and links to the audit trail and certificate of completion. The audit trail and certificate are **already stored** on the transaction by Plan 5; this plan only adds the page and file-serving views—no on-demand fetch from SIGNiX.

**Deliverables:**
- **Detail page** — URL **`/deals/signatures/<pk>/`**. **Header:** Transaction ID (or fallback), Deal link, document set type, status, last status updated. **Signers table:** order, name, email, authentication, signed, **signed at** (from party_complete events). **Documents table:** document name, **As sent** (link to version with status "Submitted to SIGNiX"), **Signed** (link to Final version or "Pending"). **Events table:** chronological (transaction.events.order_by("occurred_at")) with human-readable labels (Transaction submitted, Sent, Signer completed, Transaction completed, etc.). **Audit trail and certificate:** View/Download links when files present.
- **Table row action** — **View** link on dashboard and Deal View table → detail page.
- **Serving audit trail and certificate** — Views `/deals/signatures/<pk>/audit-trail/` and `/deals/signatures/<pk>/certificate/` that stream the stored PDFs (auth required).

**Dependencies:** Plan 1 (status_last_updated, audit_trail_file, certificate_of_completion_file, **SignatureTransactionEvent**). Plan 2 (events created per push). Plan 3 (submitted event and "Submitted to SIGNiX" versions). Plan 5 (files populated on complete). No dependency on Plan 4 beyond existing table; Plan 6 adds the View link to the same table.

**Implement:** Batches: (1) detail view and template (header, signers, documents, events, audit/certificate sections) and View link; (2) audit-trail and certificate file-serving views. Verification: from list or Deal View, "View" opens detail page; detail page shows full timeline and "signed at"; audit/certificate links work when files present.

---

## Summary Table

| Order | Plan | Key deliverables |
|-------|------|------------------|
| 1 | PLAN-SIGNiX-SYNC-MODEL.md | SignatureTransaction: signer_count, signers_completed_refids, signers_completed_count, **status_last_updated**; Expired status; **audit_trail_file**, **certificate_of_completion_file** (FileField, blank). **SignatureTransactionEvent** model (Section 7.5). SignixConfig: push_base_url. Migrations. |
| 2 | PLAN-SIGNiX-PUSH-LISTENER.md | GET /signix/push/; **get_signature_transaction_for_push**, **apply_push_action** (DESIGN 4.4); set status_last_updated on every update; **create SignatureTransactionEvent per push** (event_type from action, occurred_at, refid/pid); return 200 OK "OK"; async **download_signed_documents_on_complete**. CSRF exempt. |
| 3 | PLAN-SIGNiX-SUBMIT-PUSH-URL.md | build_submit_document_body accepts push_base_url, adds ClientPreference elements; **get_push_base_url(request)** helper in signix (config → request → settings); orchestrator and config form both use it; sets signer_count when creating SignatureTransaction; **creates initial SignatureTransactionEvent (submitted)**; ensures document versions marked "Submitted to SIGNiX." Config form shows derived default via helper. |
| 4 | PLAN-SIGNiX-DASHBOARD-SIGNERS.md | **get_signers_display(transaction)** (DESIGN 3.4); **Signers** and **Status updated** columns on dashboard list and Deal View; null-safe. |
| 5 | PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md | **download_signed_documents_on_complete(transaction)** (DESIGN 6): DownloadDocument (audit trail + certificate in request) → map signed PDFs → new DocumentInstanceVersion per instance (Final) → **store audit_trail_file and certificate_of_completion_file on transaction** (Section 6.5a) → ConfirmDownload. Proactive storage; View page serves stored files only. Wired from push listener. Idempotent. |
| 6 | PLAN-SIGNiX-TRANSACTION-DETAIL.md | **Signature transaction detail page** `/deals/signatures/<pk>/`: **header** (Transaction ID, Deal link, document set type, status, last status updated); **signers table** (order, name, email, authentication, signed, **signed at**); **documents table** (As sent, Signed); **events table** (chronological timeline); View/Download audit trail and certificate when files present. **View** link on dashboard and Deal View table. Audit-trail and certificate file-serving views (auth). DESIGN Section 8. |

---

## Dependency Overview

```
Plan 1 (Sync model: new fields + Expired + push_base_url + audit_trail_file + certificate_of_completion_file + SignatureTransactionEvent)
                    |
                    v
Plan 2 (Push listener: status + per-signer progress + create event per push, 200 OK, async trigger for complete)
                    |
                    v
Plan 3 (SubmitDocument: push URL in body, signer_count at create, submitted event, versions "Submitted to SIGNiX")
                    |
        +-----------+-----------+
        v                       v
Plan 4 (Dashboard Signers column)    Plan 5 (Download on complete: signed docs + audit trail + certificate on transaction)
                                                    |
                                                    v
                                            Plan 6 (Signature transaction detail: header, signers, documents, events, audit/certificate + View link + serve files)
```

Plan 2 must be implemented before Plan 3 so that when new transactions are submitted with the push URL (Plan 3), SIGNiX can already call the listener. Plans 4 and 5 both depend on Plan 1 and Plan 2; Plan 4 also benefits from Plan 3 (signer_count populated on new transactions). Plan 5 is triggered by the listener (Plan 2) and stores signed documents plus audit trail and certificate on the transaction; Plan 6 depends on Plan 5 so the detail page can serve those stored files. The summary order (4, 5, 6) keeps UI column updates before the download flow, then the detail page and viewing artifacts.

---

## Relation to PLAN-SIGNiX-SUBMIT-MASTER and PLAN-MASTER

- **PLAN-SIGNiX-SUBMIT-MASTER** delivers the submit flow and the dashboard/Deal View tables (without push-driven status or Signers column). This master extends that: same dashboard and tables, now with live status from push, Signers column, push URL in SubmitDocument, and download on complete.
- **PLAN-MASTER** should link to this document as the next step after PLAN-SIGNiX-SUBMIT-MASTER and PLAN-NGROK (see PLAN-MASTER.md “Next Steps” or “When ready: dashboard and sync”).

---

*To implement dashboard, sync, download, and transaction artifact viewing: ensure PLAN-SIGNiX-SUBMIT-MASTER plans 1–9 and PLAN-NGROK are complete, then implement plans 1–6 above in order, following each plan’s batches and verification. Keep Django and ngrok running in parallel whenever your verification depends on real SIGNiX push notifications reaching the local app.*


## Open Issues and Recommendations (by Plan)

**Plan 1 (SYNC-MODEL)** — **Decided:** Keep Batch 3 (SignatureTransactionEvent) separate from Batch 1 so SignatureTransaction and SignixConfig can be verified first; then add the event model. Implement in three batches as specified in the plan. Optionally combine into one migration only if you prefer a single makemigrations run.

**Plan 2 (PUSH-LISTENER)** — **Decided:** Implement event creation without dedupe initially. Duplicate events from push retries are acceptable per DESIGN 7.5. Add a unique constraint or skip logic only if duplicate events later cause UX or reporting issues.

**Plan 3 (SUBMIT-PUSH-URL)** — **Decided:** In Plan 3 implementation, verify the version-update step is present in submit_document_set_for_signature (mark latest DocumentInstanceVersion per instance to "Submitted to SIGNiX"). If it was ever removed, restore it so the detail page "document as sent" links work. The plan includes an explicit verification step for this.

**Plan 4 (DASHBOARD-SIGNERS)**
- **Open:** None specific to the enhanced detail page; Plan 4 remains column-only.
- **Recommendation:** No change; implement as written.

**Plan 5 (DOWNLOAD-ON-COMPLETE)**
- **Open:** None introduced by the design/plan updates; audit trail and certificate storage already in design.
- **Recommendation:** No change; ensure DownloadDocument request includes audit trail and certificate so Plan 6 can serve them.

**Plan 6 (TRANSACTION-DETAIL)**
- **Open:** (1) Signed-at matching when refid/pid is absent or multiple party_complete events—match by order of events vs signer order. (2) Content-Disposition for audit/certificate (inline vs attachment). (3) Permission: same as list vs restrict to deal access.
- **Recommendation:** Implement signed_at by order of party_complete events when refid/pid not present; document the rule in code. Choose inline for audit/certificate for consistency with "View"; document in view. Use same permission as signature_transaction_list unless product requires stricter deal-based access.

**Overall**
- Design and plans are consistent: event history (SignatureTransactionEvent), "document as sent" (versions "Submitted to SIGNiX"), and the full detail page (header, signers, documents, events, audit/certificate) are retrofitted into the flow. Implement plans 1–6 in order; address Plan 2 dedupe and Plan 6 open issues during implementation as needed.

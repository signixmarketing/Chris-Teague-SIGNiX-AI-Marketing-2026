# Design: SIGNiX — Dashboard, Event Sync, and Download

This document captures the design for **dashboard status driven by push notifications**, the **push notification listener**, **including the listener URL in SubmitDocument** (so SIGNiX can send webhooks to the app, initially via ngrok), and **downloading signed documents** when transactions complete and storing them as new Document Instance Versions.

**Design references:** [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) (push format, action→status mapping, DownloadDocument, ConfirmDownload, per-transaction push URL). [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) (SignatureTransaction model, dashboard and Deal View tables, submit flow; Section 8 defers push and download to this design). [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) (DocumentInstanceVersion status: Draft → Submitted to SIGNiX → Final). [08-NGROK/10-PLAN-NGROK.md](../08-NGROK/10-PLAN-NGROK.md) (ngrok tunnel and codebase changes so the app is reachable at an HTTPS URL).

**Next step:** After this design is complete, create multiple plan files and a **phase plans document** (e.g. PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md) that defines the order of those plans, then link that document from [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) so there is a clear end-to-end process for implementing dashboard, sync, and download in the correct order.

---

## 1. Scope and Goals

### In scope

- **Dashboard and status** — The signature transactions dashboard (and Deal View related-transactions table) show **ongoing status** of transactions. Status is updated from **push notifications** (Send, partyComplete, complete, suspend, cancel, expire). Design defines the status values, the mapping from push `action` to stored status, and idempotent update rules so retries do not overwrite terminal states.
- **Push notification listener** — A **listener endpoint** that SIGNiX calls (GET with query parameters). Design covers URL, request handling, lookup of the transaction by `id` or `extid`, updating `SignatureTransaction.status` (and optionally `completed_at`), returning 200 OK with body `"OK"` quickly, and performing heavy work (e.g. DownloadDocument) **asynchronously** after responding. **The system listens to push notifications and updates the number of signers who have completed whenever SIGNiX notifies it** (e.g. on **partyComplete** or **complete**), so the dashboard Signers column (e.g. 0/2, 1/2, 2/2) stays in sync with SIGNiX.
- **SubmitDocument including push URL** — Every SubmitDocument request includes the **push notification endpoint URL** so SIGNiX knows where to send webhooks for that transaction. This is done via the two client preferences **UseClientNotifyVersion2** and **TransactionClientNotifyURL**. The **base URL** is initially the **ngrok** tunnel URL (e.g. `https://your-domain.ngrok-free.dev`); design defines where this URL is configured and how it is passed into the SubmitDocument body builder.
- **Download on completion** — When a push with **action=complete** is received, the app calls **DownloadDocument** to retrieve signed PDFs, the **audit trail**, and (optionally) the **certificate of completion**. It creates **new Document Instance Versions** for each document instance in the transaction's document set (status **Final**, file = signed PDF), stores the **audit trail** and **certificate of completion** PDFs on the **SignatureTransaction** (see Section 6.5a and 7.4), then calls **ConfirmDownload** so SIGNiX can apply retention (required when using DelDocsAfter).
- **Per-signer progress on dashboard** — Both the **signature transactions dashboard** (main list) and the **Deal View related-transactions table** show **number of signers** and **number of signers completed** (e.g. “0/2”, “1/2”, “2/2”). At submit we know the total signer count; whenever the app receives a push notification (e.g. partyComplete or complete), it updates the completed count (via refid or pid) so the Signers column reflects current progress and stays idempotent on retries.

- **Viewing audit trail and certificate** — For **complete** transactions, users can view or download the **audit trail** and **certificate of completion** (when present). These files are **proactively** stored when the transaction completes (Section 6.5a); the View page only serves the already-stored files. The design provides a **signature transaction detail page** (link from the table) with deal link, signers, signed documents, and links to open the audit trail and certificate; the dashboard and Deal View tables may also offer a row-level action (e.g. "View" or "Documents") that leads to that detail page or directly to the files.

### Out of scope (or later) (or later)
- **QueryTransactionStatus polling** — As an alternative or supplement to push, the app could poll QueryTransactionStatus; see KNOWLEDGE-SIGNiX. This design focuses on push-driven updates; polling can be a separate plan if desired.
- **Push request validation** — SIGNiX Push Notifications documentation may describe optional validation (e.g. secret, IP). Design notes the requirement to return 200 OK quickly; any validation must not block the response. Implementation can add validation in a later plan if needed.

---

## 2. References

| Document | Use |
|----------|-----|
| [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) | Push notification format (GET, query params: action, id, extid, pid, refid, ts); response 200 OK body "OK"; action→status mapping; idempotency; DownloadDocument, ConfirmDownload; per-transaction push URL (UseClientNotifyVersion2, TransactionClientNotifyURL). |
| [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) | SignatureTransaction model (deal, document_set, signix_document_set_id, transaction_id, status, first_signing_url, submitted_at, completed_at); dashboard list (Section 7.3) and Deal View related table (Section 7.5); submit flow and build_submit_document_body. |
| [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) | Document set, DocumentInstance, DocumentInstanceVersion; status flow Draft → Submitted to SIGNiX → Final. |
| [08-NGROK/10-PLAN-NGROK.md](../08-NGROK/10-PLAN-NGROK.md) | ngrok setup, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, health endpoint, NGROK_DOMAIN; codebase changes so the app is reachable at `https://<ngrok-domain>/...`. |
| [SIGNiX Push Notifications](https://www.signix.com/pndocumentation) | Full parameter list, retry behavior, server requirements. |
| [Flex API](https://www.signix.com/apidocumentation) | DownloadDocument, ConfirmDownload request/response; QueryTransactionStatus. |

---

## 3. Dashboard — What It Shows

The dashboard (and Deal View related-transactions table) already exist per DESIGN-SIGNiX-SUBMIT Sections 7.3 and 7.5. This design defines how **status** is populated, what **status values** are shown, **when that status was last updated** (so users can see when the most recent signer completed and when the transaction was completed), and adds **per-signer progress** columns.

### 3.1 Status values

Store and display the following **status** values on `SignatureTransaction`:

| Status | Meaning | Set when |
|--------|---------|----------|
| **Submitted** | Transaction sent to SIGNiX; signers not yet (or partially) completed. | On create (submit flow); optionally left as-is when push `Send` is received. |
| **In Progress** | At least one signer has completed (partyComplete received). | Push `action=partyComplete`. |
| **Complete** | All signers have signed; signed documents have been (or are being) downloaded. | Push `action=complete`. |
| **Suspended** | Transaction suspended in SIGNiX. | Push `action=suspend`. |
| **Cancelled** | Transaction cancelled. | Push `action=cancel`. |
| **Expired** | Transaction expired. | Push `action=expire`. (Alternatively map to Cancelled; this design allows a distinct Expired value for clarity.) |

**Terminal states:** Complete, Suspended, Cancelled, and Expired are **terminal**. Once a transaction is in one of these states, do not overwrite with a different status (e.g. do not set back to In Progress on a duplicate or out-of-order push). Make updates **idempotent**: e.g. only transition forward in a state machine, or ignore the push if the transaction is already terminal.

### 3.2 Dashboard columns

Per DESIGN-SIGNiX-SUBMIT Section 7.3, plus **per-signer progress** and **status last updated**:

- **Deal** (link to deal detail)
- **Description** (derived from deal id and document set template name; fallback as in submit design)
- **SIGNiX DocumentSetID**
- **Status** (now driven by push as above)
- **Status updated** — **When the current status was last updated** (formatted date/time from **status_last_updated**). Use the **same date/time format as Submitted at** for consistency. Shows when the most recent signer completed (e.g. after partyComplete) and when the transaction was completed (after complete). For **existing transactions migrated in Plan 1**, the data migration sets **status_last_updated = submitted_at** so the column shows a sensible value (the only known "last update" time for those rows). For new transactions, status_last_updated is set by the push listener; null until first push update — show "—" only for edge cases (e.g. a row created after the schema but before any push).
- **Signers** — **Number of signers completed / total signers** (e.g. “0/2”, “1/2”, “2/2”). Total is set at submit time; completed count is updated on each **partyComplete** push (see Section 3.4). For older transactions created before this field existed, total may be null — show “—” or “—/—” in that case. A one-time **data migration** (Plan 1) backfills existing rows: **all existing transactions are treated as complete with all signers having signed** — set status=Complete, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at (to existing completed_at or submitted_at), and **status_last_updated = submitted_at** so the dashboard shows 2/2 and a consistent Status updated value (submit time as the effective "last status update" for migrated rows); only rows that remain null after that (if any) show "—".
- **Submitted at** (formatted date/time)
- **Open link** (when first_signing_url present and status is Submitted or In Progress)

**Column order** (dashboard list and Deal View): after **Status**, show **Signers** then **Status updated**, so users see progress (X/Y) and when it was last updated in that order.

**Deal View related table** (Section 7.5): same columns (or subset); column order after Status: **Signers** then **Status updated**. Include both so users see progress and when status last changed at a glance.

### 3.3 completed_at and status_last_updated

- **completed_at** — When push **action=complete** is processed, set **SignatureTransaction.completed_at** to the event time (from push `ts` parameter if present, or server time). This supports “Completed at” display and reporting (when the transaction reached Complete).
- **status_last_updated** — Whenever the push handler (or any update path) changes the transaction’s **status** or per-signer progress (**signers_completed_refids**, **signers_completed_count**) or **completed_at**, set **status_last_updated** to that event time (push `ts` if present and parseable, else server time). The dashboard and Deal View show this as **Status updated**. For **existing transactions backfilled in Plan 1**, the data migration sets **status_last_updated = submitted_at** so that column has a consistent value (submit time as the effective "last status update" for those rows). For new transactions, null until the first push-driven update; then always set on each update.

### 3.4 Per-signer progress (signer count and completed count)

- **At submit time** — When creating the SignatureTransaction, set **signer_count** to the number of signers in the transaction (e.g. `len(signer_order)` or the number of MemberInfo elements sent). This is the total number of parties that must complete. **signer_count may be 0** when the template has no signers (e.g. get_signer_order_for_deal returns []); the dashboard may display "0/0". No extra validation is required to forbid 0; validate_submit_preconditions already prevents creating transactions with unresolved slots in normal flows.
- **On partyComplete** — When the push handler receives **action=partyComplete**, it receives **refid** (or **pid**) identifying which party completed. To avoid double-counting on retries, store the set of **refids** (or pids) already counted: e.g. **signers_completed_refids** (JSONField, list of strings). If the incoming refid (or pid) is not already in that list, add it and set **signers_completed_count** = length of the list. Then update status to In Progress if not already terminal. This is idempotent: processing the same partyComplete twice does not increment the count twice.
- **Display** — Use two helpers so formatting and null-handling stay in one place. **get_signers_display(transaction) -> str** returns e.g. "0/2", "1/2", "2/2", or **"—"** when signer_count is null (legacy); when signer_count is 0, returns "0/0". **get_status_updated_display(transaction, fallback_to_submitted_at=False) -> str** returns the formatted date/time for status_last_updated (same format as Submitted at), or **"—"** when null; the data migration sets status_last_updated for backfilled rows, so the fallback is only for edge cases. Use both helpers in the dashboard list and the Deal View related table. Implement in `apps.deals.signix` (see Plan 4).
- **Complete** — When **action=complete** is received, all signers have completed; the display will show **signer_count/signer_count** (e.g. "2/2") and status Complete. Optionally, when processing complete, set **signers_completed_count** = **signer_count** if not already equal (so display is correct even if some partyComplete pushes were missed).

---

## 4. Push Notification Listener

### 4.1 Endpoint

- **URL:** Django serves the listener at **`/signix/push/`** (trailing slash per Django convention). In this app’s verified integration, SubmitDocument emits the callback URL as **`<base_url>/signix/push`** (no trailing slash), and SIGNiX successfully followed Django’s redirect to `/signix/push/`. Treat those as the same logical callback endpoint in this design.
- **Method:** **GET** (SIGNiX sends all information in query parameters; no POST body).
- **Authentication:** No authentication required for the request itself (SIGNiX does not send auth headers for push). Optional: future plan may add validation per SIGNiX docs (e.g. secret in query, or IP allowlist); any such check must complete quickly and not block the 200 OK response.

### 4.2 Request handling

1. **Parse query parameters** — Required: **action**, **id** (SIGNiX Document Set ID), **extid** (client TransactionID). Optional (when present): **pid**, **refid**, **ts** (event time). See KNOWLEDGE-SIGNiX and [Push Notifications](https://www.signix.com/pndocumentation). If any of action, id, or extid is missing or empty, log a warning and return 200 OK without looking up the transaction (so SIGNiX does not retry).
2. **Look up transaction** — Use a single helper **get_signature_transaction_for_push(signix_document_set_id=None, transaction_id=None)** that returns the `SignatureTransaction` matching **id** (signix_document_set_id) or **extid** (transaction_id), or None if not found or if both arguments are None/empty (in that case do not run a query). The view calls it; if None, log and return 200 OK anyway.
3. **Update status (synchronous, fast)** — Use a single helper **apply_push_action(transaction, action, refid=None, pid=None, ts=None)** that applies the action→status mapping (Section 3.1), idempotency (no overwrite of terminal states), **status_last_updated** and completed_at for complete, and per-signer progress for partyComplete (Section 3.4). Use a single **event time** (parsed from push `ts` or server time) for both completed_at and status_last_updated when setting them. The helper mutates the transaction in memory; the view then saves it with **update_fields=["status", "completed_at", "status_last_updated", "signers_completed_refids", "signers_completed_count"]**. Whenever the helper changes status, completed_at, or signer progress, it sets **status_last_updated** to that event time. This keeps the view thin and the logic testable without HTTP.
4. **Record event** — After saving the transaction, create a **SignatureTransactionEvent** (Section 7.5) for this push: event_type from action (e.g. send→send, partyComplete→party_complete, complete→complete, suspend→suspend, cancel→cancel, expire→expire), occurred_at from push `ts` or server time, refid and pid when present. So the signature transaction detail page can display the full event timeline and "when each signer signed" from party_complete events.
5. **Return response immediately** — Return **HTTP 200 OK** with response body exactly **"OK"** (no extra content). Respond within a few hundred milliseconds so SIGNiX does not treat the delivery as failed and retry unnecessarily.
6. **Heavy work asynchronously** — For **action=complete**, after sending the response, call **download_signed_documents_on_complete(transaction)** (see Section 6). Run it asynchronously (e.g. background thread or fire-and-forget); do not block the GET handler.

### 4.3 Idempotency and retries

- SIGNiX may send the same push more than once (retries on failure). The handler must be **idempotent**: processing the same event twice must not corrupt data (e.g. do not create duplicate DocumentInstanceVersions; do not overwrite terminal status).
- For **status updates**: only allow transitions from non-terminal to terminal or to In Progress; never overwrite Complete/Cancelled/Suspended/Expired with a different status.
- For **download on complete**: before calling DownloadDocument, check that the transaction status is Complete (or that we have not already created Final versions for this transaction). In this codebase, document instances are reused across multiple SIGNiX transactions for the same deal, so "already processed" must be **transaction-aware**: an older historical `Final` on the document instance must not cause a newer transaction to be skipped. If already processed for this transaction, skip download/ConfirmDownload and log.

### 4.4 Push listener helpers

Implement in `apps.deals.signix` (or a dedicated push module):

- **get_signature_transaction_for_push(signix_document_set_id=None, transaction_id=None) -> SignatureTransaction | None** — Look up by signix_document_set_id first, then by transaction_id. Return None if not found or if **both** arguments are None or empty (do not run a query in that case). Single place for lookup so the view stays thin and tests can call it without HTTP.
- **apply_push_action(transaction, action, refid=None, pid=None, ts=None)** — Apply action→status per Section 3.1; do not overwrite terminal states (idempotent). If action is not one of Send, partyComplete, complete, suspend, cancel, expire: do not change status; log at debug; the view still returns 200 OK. Set **status_last_updated** and completed_at when action is complete (from ts or now). For any mutation (status change, signer progress, or completed_at), set **status_last_updated** to the event time (ts parsed or timezone.now()). For partyComplete: if refid (or pid if refid absent) not in signers_completed_refids, append it and set signers_completed_count = len(signers_completed_refids); set status to In Progress if not terminal. For complete: set signers_completed_count = signer_count if not already equal. Mutates transaction; view saves with update_fields as in Section 4.2.

### 4.5 Errors and logging

- **Missing required params (action, id, extid):** If any is missing or empty, log a warning and return 200 OK with body "OK" without calling the lookup. Do not return 4xx so SIGNiX does not retry.
- **Unknown id/extid:** Log warning; return 200 OK anyway. Log error with transaction id; do not retry from the view (optional: queue for retry in a later plan). Transaction remains Complete; user or support can trigger a manual “re-download” later if desired (out of scope for this design).

---

## 5. SubmitDocument — Including the Push Endpoint URL

To receive push notifications, each SubmitDocument request must tell SIGNiX where to send them. This is done with **per-transaction client preferences**.

### 5.1 Client preferences

Include these in the SubmitDocument request. **Placement (required for correct behavior):** put both elements **inside `<Data>`, immediately after `<SuspendOnStart>` and before the first `<MemberInfo>`**. Order: … SuspendOnStart → UseClientNotifyVersion2, TransactionClientNotifyURL → (optional NotificationSchedule if used) → MemberInfo → Form(s). This order matches working SubmitDocument examples.

- **UseClientNotifyVersion2** — Set to **yes**.
- **TransactionClientNotifyURL** — The full URL of the push listener: **`<base_url>/signix/push`** in the working integration for this app (no trailing slash in the emitted SubmitDocument payload).

Example (conceptual):

```xml
<ClientPreference name="UseClientNotifyVersion2">yes</ClientPreference>
<ClientPreference name="TransactionClientNotifyURL">https://your-ngrok-domain.ngrok-free.dev/signix/push</ClientPreference>
```

### 5.2 Source of the base URL

The **base URL** (e.g. `https://your-ngrok-domain.ngrok-free.dev`) must be known so that TransactionClientNotifyURL points to a reachable listener.

**Preferred: derive from the request.** When SubmitDocument is invoked from a view (e.g. the user clicks "Send for signature"), the app can derive the base URL from the current request: e.g. **`request.build_absolute_uri('/').rstrip('/')`**. That yields:
- **Production:** The public URL the user used (e.g. `https://app.example.com`), which is the correct callback host.
- **Dev with ngrok:** The current ngrok URL from the browser (e.g. `https://abc.ngrok-free.app`), so staff do not need to type or configure the tunnel URL anywhere.

So the application **does not require** a user-supplied push base URL in the common case. A stored value (SignixConfig.push_base_url or settings.SIGNIX_PUSH_BASE_URL) is only needed when:
- Submit is triggered **without** a request (e.g. management command or background job), or
- The callback host must differ from the request host (e.g. rare override).

**Recommended:** Resolve push base URL in this order: (1) **SignixConfig.push_base_url** if set; (2) **request.build_absolute_uri('/').rstrip('/')** when the caller has a request (e.g. the view passes the request into the resolver); (3) **settings.SIGNIX_PUSH_BASE_URL** or **NGROK_DOMAIN** if present. When the resolved value is **empty**, do **not** add the ClientPreference elements. When **set**, build the full URL as **`<push_base_url>/signix/push`** (no double slash, no trailing slash on the emitted callback path).
**HTTPS behind ngrok / proxy:** When deriving the base URL from the request behind ngrok or another HTTPS proxy, Django must trust the forwarded HTTPS scheme or `request.build_absolute_uri('/')` can incorrectly produce `http://...` even though the browser is on HTTPS. In this app’s verified integration, enabling proxy SSL awareness (for example `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`) was necessary so SIGNiX received an `https://...` callback URL.

- **Initial implementation:** The view that calls the orchestrator passes the result of get_push_base_url(request). No admin field is required for typical use; the plan can still add **SignixConfig.push_base_url** as an optional override (e.g. headless submit). **Config form UX:** When the SignixConfig admin or config page is rendered, the app can **derive** the push base URL from the current request (`request.build_absolute_uri('/').rstrip('/')`) and **display it next to** the push_base_url field as read-only text (e.g. “When blank, callback URL will be: &lt;derived&gt;/signix/push” or “Current site URL (used when field is blank): &lt;derived&gt;”). That way the user sees what will be used as the default without having to set the field.

### 5.3 Where it is passed in

- **build_submit_document_body** (or the data dict builder that feeds the template) must accept an optional **push_base_url** (or equivalent). When provided, the template includes the two ClientPreference elements with **TransactionClientNotifyURL** = **push_base_url** + **"/signix/push"**.
- **Single helper:** Use **get_push_base_url(request=None)** (e.g. in `apps.deals.signix`) to resolve the base URL in one place. The **submit path** (orchestrator, with optional request) calls `get_push_base_url(request)` and passes the return value into **build_submit_document_body**. When request is None (e.g. management command or dump), the helper uses config/settings only. The **config form** (admin or config view) calls `get_push_base_url(request)` and passes the return value to the template for the “when blank, app will use …” display. No inline derivation in multiple places.
- **Dump / debugging:** When building the SubmitDocument body for a dump or debug command (e.g. signix_dump_body), call **build_submit_document_body** with **push_base_url=get_push_base_url(None)** so the dumped XML includes the ClientPreference block when config or settings provide a push base URL.

**Data sourcing table addition (for plans):**

| Payload area | Element | Source or rule |
|--------------|--------|----------------|
| **Data** (ClientPreference) | UseClientNotifyVersion2 | **yes** when push_base_url is set. |
| **Data** (ClientPreference) | TransactionClientNotifyURL | **push_base_url + "/signix/push"** when push_base_url is set (no double slash). push_base_url from **get_push_base_url(request)** (helper: config then request then settings; see Section 5.4). |

### 5.4 Helper: get_push_base_url (single place for resolution)

Implement **get_push_base_url(request=None)** in `apps.deals.signix` so resolution logic is not duplicated. **Signature:** `(request=None) -> str`. **Behavior:** (1) If SignixConfig.push_base_url is set and non-empty, return it (strip trailing slash). (2) Elif request is not None, return request.build_absolute_uri('/').rstrip('/'). (3) Elif settings has SIGNIX_PUSH_BASE_URL, return it (strip trailing slash if present). (4) Elif settings has NGROK_DOMAIN: use the value; **if it does not start with "http", prepend "https://"** so the callback URL is valid. (5) Else return "". Callers append "/signix/push" when they need the full callback URL. The **submit path** and the **SignixConfig form** (for the displayed default) both call this helper only; no inline derivation elsewhere. When this helper is fed a real request behind ngrok/proxy, Django must trust the forwarded HTTPS scheme.

---

## 6. Download on Completion

When a push with **action=complete** is received and the transaction is updated to status **Complete**, the app must retrieve the signed documents and store them as **Final** Document Instance Versions. The system **proactively** retrieves and stores the **audit trail** and **certificate of completion** in the same flow, so they are already on the transaction when a user later opens the View Signature Transaction detail page—no on-demand fetch when the user visits that page.

**Single callable:** Implement **download_signed_documents_on_complete(transaction)** (e.g. in `apps.deals.signix`) that performs the full flow: transaction-aware idempotency check (skip only if this transaction’s signed versions were already created), DownloadDocument, map to document_set.instances, create new DocumentInstanceVersions (Final), **store audit trail and certificate on the transaction** (Section 6.5a), ConfirmDownload. The push listener (Section 4) calls it asynchronously after responding 200 OK. One place for the download logic; easy to test and to trigger manually or from a management command later.

### 6.1 Trigger

- **Trigger:** After responding 200 OK to the push, an **asynchronous task** (or background path) runs for that transaction when **action=complete**.
- **Input:** SignatureTransaction (with signix_document_set_id, document_set, deal).

### 6.2 DownloadDocument

- **Call:** Flex API **DownloadDocument** with the transaction’s **DocumentSetID** (signix_document_set_id). Use the same credentials and endpoint (Webtest/Production) as for SubmitDocument (from SignixConfig). Request/response structure per [Flex API documentation](https://www.signix.com/apidocumentation).
- **Request:** Include **IncludeAuditData** (true) and **AuditDataFormat** (e.g. `pdf`) so the response includes the audit trail as a PDF. Include **UseConfirmDownload** when using ConfirmDownload/retention, and include the optional element for **certificate of completion** so the response includes that summary PDF when supported (see KNOWLEDGE-SIGNiX and Flex API). Live verification in this app showed SIGNiX accepted the request when the `<Data>` children were ordered as: `DocumentSetID`, `IncludeAuditData`, `AuditDataFormat`, `UseConfirmDownload`, then `IncludeCertificateOfCompletion` when requested.
- **Response:** Signed PDFs (one per document instance), plus the **audit trail PDF** and (when requested) the **certificate of completion PDF**. Order and identifiers (e.g. RefID) per Flex API—use the documentation to map returned documents to the app’s document instances and to identify the audit trail and certificate sections in the response. Live verification in this app showed signed documents returned as `<Form>` elements under the response `<Data>` block, the audit PDF returned as `<AuditReport>`, and the certificate returned as `<CertificateOfCompletion>`.

### 6.3 Mapping to document instances

- The transaction’s **document_set** has **instances** in a fixed **order** (e.g. `document_set.instances.order_by("order")`). SubmitDocument sends one **Form** per instance in that order; each Form has a **RefID** (e.g. from the template ref_id or a stable identifier like `Form-{instance.order}`).
- **Mapping rule:** Match the documents returned by DownloadDocument to **document_set.instances** by **position** (first returned document = first instance in order) or by **RefID** if the Flex API returns RefID per document. In live verification for this app, SIGNiX returned the signed documents as `<Form>` elements and included `RefID`, so parsers should tolerate that concrete shape in addition to any generic documentation examples. If the count does not match, log an error and create versions for the instances that can be matched; do not fail the whole flow for a single mismatch if partial save is acceptable.
- **Idempotency rule for reused document instances:** In this codebase, the same deal/document instances can be submitted to SIGNiX more than once. Therefore, the download flow must not decide "already processed" just because some historical `Final` version exists on the document instance. Instead, it must determine whether **this transaction** already produced a newer `Final` than the version that was current at `transaction.submitted_at`.

### 6.4 Create new Document Instance Versions

- For each **document instance** in the transaction’s document set (in order), create a **new DocumentInstanceVersion**:
  - **Document instance:** The instance from document_set.instances for that position (or matched by RefID).
  - **File:** The signed PDF bytes from DownloadDocument for that document.
  - **Status:** **Final** (per DESIGN-DOCS: “When the transaction is complete and we download signed PDFs, new Document Instance Versions are created with status ‘Final’”).
  - **Version number:** Next version number for that instance (e.g. increment from latest existing version).
- Store the file in the app’s media storage (same as existing DocumentInstanceVersion file handling). Set **version_number** and any other required fields per the DocumentInstanceVersion model.

### 6.5 ConfirmDownload

- After **all** signed documents have been stored as new DocumentInstanceVersions **and** the audit trail (and certificate of completion, if requested) have been stored on the transaction (Section 6.5a), call **ConfirmDownload** with the same DocumentSetID (and credentials). This is required for SIGNiX retention policies (e.g. when using DelDocsAfter in SubmitDocument). See KNOWLEDGE-SIGNiX.

### 6.5a Store audit trail and certificate on SignatureTransaction

- **Proactive retrieval:** The audit trail and certificate are retrieved and stored **as part of the completion flow** (when **action=complete** triggers **download_signed_documents_on_complete**). The View Signature Transaction detail page only **displays or serves** these already-stored files; the system does **not** call DownloadDocument when the user visits that page.
- **When:** As part of **download_signed_documents_on_complete(transaction)**, after parsing the DownloadDocument response.
- **What:** From the response, extract the **audit trail** PDF and (if present) the **certificate of completion** PDF. Save them on the **SignatureTransaction** using the fields **audit_trail_file** and **certificate_of_completion_file** (Section 7.4). Use the same media storage as for DocumentInstanceVersion (e.g. `upload_to="signature_transactions/%Y/%m/"` or similar).
- **On delete:** When a **SignatureTransaction** is deleted (e.g. via Delete Transaction History or cascade from DocumentSet), the stored **audit_trail_file** and **certificate_of_completion_file** are **removed from media storage** so no orphaned files remain. Implementation uses a **pre_delete** signal on SignatureTransaction that deletes both files from storage before the row is removed. This ensures that "delete transaction history" removes both records and artifacts consistently.
- **Idempotency:** If the download flow runs more than once (e.g. retry or manual re-download), overwriting existing files is acceptable; alternatively, only save when the field is currently empty. For signed document versions, idempotency must be **transaction-aware** in this codebase because document instances are reused across multiple SIGNiX transactions.
- **Failure:** If parsing or saving the audit trail or certificate fails, log the error but do not fail the entire flow: signed document versions and ConfirmDownload should still proceed so retention and document set state remain consistent.

### 6.6 Failure handling

- **DownloadDocument failure:** Log error; do not set transaction status back from Complete. Optionally allow a manual “download again” action in a future plan.
- **ConfirmDownload failure:** Log error; documents are already stored. Retry ConfirmDownload in a later plan if needed for compliance.
- **Partial mapping failure:** If some documents cannot be matched to instances, log and create versions for the ones that match; document the behavior in the plan.
- **Schema / response-shape drift:** Flex API examples and live tenant behavior may differ in element names or ordering. Preserve the live findings verified during this implementation in KNOWLEDGE-SIGNiX and the plan: request uses `AuditDataFormat` before `UseConfirmDownload`; response may use `<Form>` and `<AuditReport>`.

---

## 7. Data Model

### 7.1 SignatureTransaction.status and timestamps

- **Allowed values:** Submitted, In Progress, Complete, Suspended, Cancelled, **Expired** (add **Expired** if not already present in the model). Store as a string (CharField with choices or free-form); validation in the push handler and in the app to allow only the above values.
- **completed_at** — Set when action=complete is processed (from push `ts` or server time). Already in DESIGN-SIGNiX-SUBMIT; no schema change.
- **status_last_updated** — **DateTimeField**, null=True, blank=True. Set whenever the push handler (or any path) updates **status**, **completed_at**, or per-signer progress (**signers_completed_refids**, **signers_completed_count**) to the event time (push `ts` if present and parseable, else server time). Enables the dashboard and Deal View to show **Status updated** (when the current status was last updated), so users can see when the most recent signer completed and when the transaction was completed. Null until the first such update.

### 7.2 Per-signer progress (signer count and completed count)

- **signer_count** — **PositiveSmallIntegerField**, nullable. Set when the SignatureTransaction is created (at submit): total number of signers (e.g. `len(get_signer_order_for_deal(...))` or number of MemberInfo elements). May be **0** when the template has no signers (e.g. get_signer_order_for_deal returns []); dashboard may display "0/0". Null for transactions created before this field exists.
- **signers_completed_refids** — **JSONField**, list of strings (e.g. `default=list`). Stores refid (or pid) for each party that has completed, so the same partyComplete is not counted twice on retry. Prefer **refid** when present (KNOWLEDGE-SIGNiX: "use refid and ignore pid when both are present"); use **pid** when refid is absent.
- **signers_completed_count** — **PositiveSmallIntegerField**, default 0. Number of distinct parties that have completed (length of signers_completed_refids). Updated when a new refid/pid is added on partyComplete; optionally set to signer_count when action=complete is processed so display is correct even if a partyComplete was missed.

### 7.3 SignixConfig (or settings) for push URL

- Add a field or setting for the **push base URL** (e.g. **SignixConfig.push_base_url** or **settings.SIGNIX_PUSH_BASE_URL**). When set, SubmitDocument includes TransactionClientNotifyURL; when blank, omit the client preferences (account-level push URL may apply). For development, this is typically the ngrok root URL (e.g. `https://your-domain.ngrok-free.dev`) with no path component—the `/signix/push` path is appended when building the full callback URL in this app’s working integration. If the value is derived from the current request behind ngrok/proxy, Django must preserve the external `https` scheme.

### 7.4 SignatureTransaction — audit trail and certificate of completion

- **audit_trail_file** — **FileField**, blank=True, upload_to e.g. `"signature_transactions/%Y/%m/"`. Populated by **download_signed_documents_on_complete** when the DownloadDocument response includes the audit trail PDF (Section 6.5a). Enables the app to offer "View audit trail" / "Download audit trail" for completed transactions.
- **certificate_of_completion_file** — **FileField**, blank=True, same upload_to as audit_trail_file. Populated when the DownloadDocument request requests the certificate and the response includes it (Section 6.5a). Enables "View certificate" / "Download certificate" when present.
- **Deletion:** When a SignatureTransaction is deleted (Delete Transaction History or cascade), a **pre_delete** signal removes both files from media storage so no orphaned artifacts remain (Section 6.5a).
- **Access control:** Serve these files only to authenticated users (e.g. view that checks transaction.deal and user permission, or signed/short-lived URL). Implementation plan should define the exact URL pattern and permission (e.g. same as deal detail or signature transaction list).

### 7.5 SignatureTransactionEvent — event history

- **Purpose:** Provide a **living representation** of the transaction on the signature transaction detail page: an ordered list of events from "Transaction submitted" (when the app sent the transaction to SIGNiX) through each push notification (Send, partyComplete, complete, suspend, cancel, expire), ending with "Transaction completed." Event history also supports showing **when each signer signed** (from the partyComplete event’s timestamp and refid/pid).
- **Model:** **SignatureTransactionEvent** — **signature_transaction** (ForeignKey to SignatureTransaction, related_name="events"); **event_type** (CharField: `submitted`, `send`, `party_complete`, `complete`, `suspend`, `cancel`, `expire`); **occurred_at** (DateTimeField); **refid** (CharField, blank=True); **pid** (CharField, blank=True). Ordering: by occurred_at ascending so the detail page displays chronological order. **submitted** is created when the transaction is created (submit flow); all other types are created when the push listener processes the corresponding push (Section 4.2).
- **Idempotency:** SIGNiX may send the same push more than once. Options: (a) create an event row for every push we process (duplicate events possible but simple); (b) deduplicate by (transaction, event_type, refid, occurred_at) so retries do not create duplicate rows. Design leaves the choice to the implementation plan; the detail page displays events in order and duplicate "party_complete" entries for the same refid may be acceptable or deduped in the query.
- **Data sourcing for detail page:** Signer "signed at" = the **occurred_at** of the **party_complete** event whose refid (or pid) can be correlated to that signer using values the app already knows locally (for example email address, slot number, or order index). If push identifiers do not correlate cleanly, matching falls back to the next unmatched **party_complete** event by chronological order (e.g. first unmatched party_complete = first unmatched signer). The implementation plan defines the exact helper, but the design expectation is "best explicit match first, then stable positional fallback."

---

## 8. Signature transaction detail and viewing artifacts

This section defines the **signature transaction detail page** as a **living representation** of the transaction: the information sent to SIGNiX, the current status, signers (with signing status and when they signed), documents (as sent and as signed), a chronological event history, and links to the audit trail and certificate of completion. The audit trail and certificate are **already stored** on the transaction (Section 6.5a); the detail page and file-serving views only **display or stream** those stored files. The system does **not** retrieve them from SIGNiX when the user opens the page. The dashboard and Deal View tables offer a **View** link (or button) per row to open this detail page.

### 8.1 Rationale (useful and practical)

- **Useful:** Users need one place to see what was sent, who signed and when, the documents as sent vs as signed, the full event timeline, and proof (audit trail and certificate). This supports compliance, disputes, and internal review.
- **Practical:** Event history (Section 7.5) is populated as part of the submit and push flows; signer and document data come from existing models (deal signer order, document_set instances and versions). The detail page is a read-only view over that data.

### 8.2 Page structure (consistent with other detail pages)

- **URL:** **`/deals/signatures/<pk>/`** (or equivalent under the deals app). View (e.g. `signature_transaction_detail`); same access control as the signature transaction list (authenticated users).

**Header (top of page, consistent with other detail pages)**

- **Transaction ID** — The client-side identifier (e.g. **SignatureTransaction.transaction_id**). When transaction_id is blank, show SIGNiX Document Set ID or a fallback (e.g. "—") so the header always has a clear identifier.
- **Deal** — Live link to the deal (e.g. "Deal #<id>" linking to deal detail URL). So the user can return to the deal context.
- **Document set type** — The document set template name (e.g. **document_set.document_set_template.name** when present). When the template is null (e.g. set deleted), show "—" or a fallback.
- **Status** — The transaction status (Submitted, In Progress, Complete, Suspended, Cancelled, Expired), shown prominently.
- **Last status updated** — The **status_last_updated** timestamp (formatted like "Submitted at" / "Status updated" on the dashboard). When null, show "—".

**Signers table (below header)**

- **Order** — Signing order (1, 2, …) from the deal's signer order at submit time (e.g. **get_signer_order_for_deal(deal, document_set.document_set_template)**).
- **Name** — Resolved from **resolve_signer_slot(deal, slot_number)** (first_name, last_name or display name).
- **Email** — From the same resolution (email address).
- **Authentication method** — From **get_signer_authentication_for_slot(deal, slot_number)** or the deal's signer_authentication (e.g. SelectOneClick, SMSOneClick).
- **Signed** — Yes if this signer has completed (e.g. refid or pid for this position is in **signers_completed_refids**, or derived from event history).
- **Signed at** — The **occurred_at** of the **party_complete** event that corresponds to this signer (Section 7.5). When refid/pid is stored on the event, first try to match it to locally-known signer values; otherwise match by order of unmatched party_complete events. When not yet signed or no event, show "—".

**Documents table (below signers)**

- **Document** — Name or identifier of each document in the transaction's **document_set** (instances in order). In practice, prefer the source template **ref_id**, then template **description**, then a neutral fallback such as "—" if the source template is gone.
- **As sent** — Link to the **document as sent** in the SubmitDocument call: the **DocumentInstanceVersion** for that instance with status **"Submitted to SIGNiX"** (per DESIGN-DOCS and DESIGN-SIGNiX-SUBMIT step 7; marked when the transaction is created). When no such version exists (edge case), show "—" or "Not available."
- **Signed** — Link to the **signed document** when available: the **DocumentInstanceVersion** with status **"Final"** for that instance (populated by the download-on-complete flow). When not yet downloaded, show "Pending" or "Not yet downloaded."

**Events table (below documents)**

- **Chronological list** of events for this transaction (from **SignatureTransactionEvent**, ordered by **occurred_at** ascending, with **pk** as a deterministic tie-breaker when timestamps are equal).
- **Initial event:** **Transaction submitted** — When the application sent the transaction to SIGNiX (event_type **submitted**, occurred_at = transaction.submitted_at or the event's occurred_at).
- **Subsequent events:** Each push notification received (event_type **send**, **party_complete**, **complete**, **suspend**, **cancel**, **expire**) with **occurred_at** and optional party info (refid/pid). Display with human-readable labels (e.g. "Sent", "Signer completed", "Transaction completed", "Suspended", "Cancelled", "Expired").
- **Goal:** The table reads as a timeline from "Transaction submitted" through to "Transaction completed" (or terminal state), so the user sees a living representation of what happened.

**Audit trail and certificate of completion (below events)**

- **Audit trail** — When **audit_trail_file** is set: expose a "View audit trail" link on the detail page that opens the stored PDF inline. When not set: show "Audit trail not available" or hide the row.
- **Certificate of completion** — When **certificate_of_completion_file** is set: expose a "View certificate" link on the detail page that opens the stored PDF inline. When not set: show "Certificate not available" or hide the row.

**Empty / edge cases**

- If the transaction is not Complete, the page still shows header, signers, documents, and events; audit trail and certificate sections show only when status is Complete and files are present (or "not available" when Complete but missing). Document "As sent" requires that versions were marked "Submitted to SIGNiX" at submit time (DESIGN-SIGNiX-SUBMIT step 7; Plan 3 ensures this).

### 8.3 Table row action (dashboard and Deal View)

- **Mechanism:** On the signature transactions **dashboard** and the **Deal View related-transactions table**, each row includes a **View** link (or button) that links to **`/deals/signatures/<pk>/`** so users can open the detail page.
- **When to show:** Show "View" for **all** transactions so users can always open the detail page.

### 8.4 Serving the files

- **Audit trail and certificate PDFs** — Served via authenticated views at `/deals/signatures/<pk>/audit-trail/` and `/deals/signatures/<pk>/certificate/`. In this app, the working pattern is the same as existing document PDF views: `login_required`, `404` when the file field is empty, and `FileResponse(..., content_type="application/pdf", as_attachment=False)` so the PDF opens inline. Preserve the stored filename in `Content-Disposition` when available.

---

## 9. Security and Validation

- **Listener endpoint** — No Django authentication (no login required) so SIGNiX’s servers can call it. Consider:
  - **CSRF:** Ensure the push URL is exempt from CSRF (GET requests are typically not CSRF-checked; if the app applies CSRF to all views, exempt the push view).
  - **Optional validation:** If SIGNiX documentation specifies a shared secret or token in the query string, validate it and reject invalid requests with 4xx; still respond quickly. If validation is added later, document it in a plan.
- **SubmitDocument** — No change to auth; only the push URL is added to the payload. Credentials remain in CustInfo as today.

---

## 10. Dependencies and Implementation Order

- **Depends on:** DESIGN-SIGNiX-SUBMIT implemented (SignatureTransaction, submit flow, dashboard and Deal View tables per Plans 1–9 in PHASE-PLANS-SIGNiX-SUBMIT). [08-NGROK/10-PLAN-NGROK.md](../08-NGROK/10-PLAN-NGROK.md) applied (tunnel and codebase changes so the app is reachable at an HTTPS URL).
- **Next step:** Create **plan files** (e.g. one for push listener + status updates, one for SubmitDocument URL, one for download + ConfirmDownload, or a different split). Create [PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md](PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md) (or similar) that lists those plans in order and links from [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) so implementers follow the correct end-to-end order.

---

## 11. Open Issues and Decisions

These decisions are resolved here so plan files can implement without re-opening design choices.

1. **Push base URL — where to store**  
   The app can **derive** the push base URL from the **current request** when submit is triggered from a view (`request.build_absolute_uri('/').rstrip('/')`), so staff do not need to supply it in the common case. **SignixConfig.push_base_url** remains useful as an **optional override** (e.g. when submit runs without a request, or when the callback host must differ from the request host). When the resolved push_base_url (from request, then config, then settings) is **blank**, do not add the ClientPreference elements. When **set**, build TransactionClientNotifyURL = push_base_url + "/signix/push" in this app’s verified integration. The admin field for push_base_url is **optional**; the plan can make it available for overrides but need not require users to set it. **Config form display:** When the SignixConfig form (admin or config page) is rendered, call **get_push_base_url(request)** and show the result next to the field as read-only text (e.g. “When blank, app will use: &lt;result&gt;/signix/push”) so the user sees the effective default. Resolution logic lives only in the helper. When deriving from a request behind ngrok/proxy, Django must trust the forwarded HTTPS scheme so the emitted callback remains `https://...`.

2. **Async execution for download-on-complete**  
   Use a **simple asynchronous path** (e.g. a background thread or fire-and-forget helper) so the push view returns 200 OK quickly and DownloadDocument/ConfirmDownload run after the response. **Celery is not required** for the initial implementation; a plan may use `threading.Thread` or a small in-process queue. If the project later standardizes on Celery, the download task can be moved there.

3. **Expired status**  
   Use a **distinct Expired** status (do not map expire to Cancelled). Add **Expired** to the SignatureTransaction status choices if not already present.

4. **On complete: set signers_completed_count**  
   When processing **action=complete**, set **signers_completed_count** = **signer_count** if not already equal, so the Signers column shows e.g. "2/2" even if a partyComplete push was missed. This is recommended so the dashboard is consistent.

5. **Data migration: existing transactions treated as complete**  
   When introducing push-driven status and per-signer progress (Plan 1), **all transactions that already exist** in the database are treated as **complete with all signers having signed**. The Plan 1 data migration sets status=Complete, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at (to existing completed_at or submitted_at), and **status_last_updated = submitted_at**. Using **submitted_at** as the “last status update” for migrated rows is the intended design: we have no push history for those transactions, so the submit timestamp is the only meaningful “when status was last updated” value; the dashboard Status updated column then shows a consistent, logical date for every backfilled row. No legacy rows remain in Submitted or In Progress; the dashboard shows a consistent state. See Section 3.2 (Signers column, Status updated) and Plan 1.

6. **Audit trail and certificate stored on transaction**  
   The **audit trail** and **certificate of completion** PDFs from DownloadDocument are stored on the **SignatureTransaction** (audit_trail_file, certificate_of_completion_file), not as document instances in the document set. This keeps the document set as "deal documents" and the transaction as "proof and artifacts of signing." Users view or download them from the **signature transaction detail page** or via row-level "View" from the dashboard/Deal View table (Section 8).

7. **Event history and "document as sent"**  
   **SignatureTransactionEvent** (Section 7.5) is created when the transaction is created (event_type **submitted**) and when each push is processed (event_type from action). The submit flow (Plan 3) must create the initial **submitted** event and must mark the document set's current versions as status **"Submitted to SIGNiX"** (DESIGN-SIGNiX-SUBMIT step 7) so the detail page can link to "document as sent" and show the full event timeline.

---

## 12. Summary

| Area | Design decision |
|------|-----------------|
| **Dashboard status** | Status values: Submitted, In Progress, Complete, Suspended, Cancelled, Expired. Updated from push; idempotent; terminal states never overwritten. **Status updated** column shows when status was last updated (status_last_updated). |
| **Dashboard Signers column** | signer_count (total, set at submit); signers_completed_refids + signers_completed_count (updated on partyComplete, idempotent). Display "X/Y" (e.g. 0/2, 1/2, 2/2) via **get_signers_display(transaction)**; "—" when signer_count null. **Status updated** column via **get_status_updated_display(transaction)** (same format as Submitted at); "—" when null. Column order after Status: Signers then Status updated. |
| **Listener** | GET `/signix/push/`; parse action, id, extid; if missing params or transaction not found, still return 200 OK "OK"; lookup transaction; update status and per-signer progress (and completed_at for complete) via apply_push_action; save with update_fields; run DownloadDocument/ConfirmDownload asynchronously for action=complete. |
| **SubmitDocument** | Add ClientPreference UseClientNotifyVersion2=yes and TransactionClientNotifyURL=&lt;push_base_url&gt;/signix/push when push_base_url is set. push_base_url derived from request when available; SignixConfig or settings as override. Preserve forwarded HTTPS when deriving from request behind ngrok/proxy. |
| **Download on complete** | **Proactive:** When action=complete, async DownloadDocument (request audit trail + optional certificate) → map signed PDFs to document_set.instances → create new DocumentInstanceVersion per instance (status=Final) → store **audit_trail_file** and **certificate_of_completion_file** on SignatureTransaction (Section 6.5a) → ConfirmDownload. Use the live-verified DownloadDocument shape for this app: request uses `AuditDataFormat` before `UseConfirmDownload`; response may return signed docs as `<Form>` and audit data as `<AuditReport>`. Idempotency must be transaction-aware because document instances are reused across multiple SIGNiX transactions. Audit trail and certificate are stored in this flow so the View Signature Transaction page only serves already-stored files (no on-demand fetch). |
| **Data model** | status includes Expired; completed_at set on complete; **status_last_updated** set on every push-driven update; **signer_count**, **signers_completed_refids**, **signers_completed_count**; **audit_trail_file**, **certificate_of_completion_file** (FileField, blank=True) on SignatureTransaction (Section 7.4); **SignatureTransactionEvent** (Section 7.5) for event history; optional push_base_url on SignixConfig or in settings. |
| **Transaction detail and artifacts** | **Detail page** `/deals/signatures/<pk>/`: **header** (Transaction ID, Deal link, document set type, status, last status updated); **signers table** (order, name, email, authentication, signed, signed at from events); **documents table** (as sent = version "Submitted to SIGNiX", signed = Final when present); **events table** (chronological: submitted then push events); **View/Download audit trail** and **certificate** when files present (Section 8). **Table row:** "View" on dashboard and Deal View table. Serve audit/certificate PDFs via authenticated view (Section 8.4). |
| **Helpers** | **get_push_base_url(request)** (5.4); **get_signature_transaction_for_push**, **apply_push_action** (4.4); **download_signed_documents_on_complete(transaction)** (Section 6); **get_signers_display(transaction)** and **get_status_updated_display(transaction)** (3.4). Single place for each concern. |

---

*End of design. Implementation will follow plan files and the phase plans document (PHASE-PLANS-SIGNiX-DASHBOARD-SYNC). For Flex API and push details, see [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) and the SIGNiX documentation.*

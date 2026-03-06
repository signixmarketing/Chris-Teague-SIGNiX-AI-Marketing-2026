# Plan: SIGNiX Signature Transaction Detail and Viewing Artifacts (Dashboard/Sync Plan 6)

This plan adds a **signature transaction detail page** that provides a **living representation** of the transaction: what was sent to SIGNiX, status and when it was last updated, signers (with who signed and when), documents as sent vs signed, a chronological event timeline, and links to the audit trail and certificate of completion. The audit trail and certificate are **already stored** on the transaction by Plan 5; this plan only adds the page and file-serving views—no on-demand fetch from SIGNiX when the user visits the page.

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 8 (Signature transaction detail and viewing artifacts), **Section 8.2 (page structure: header, signers table, documents table, events table, audit/certificate)**, Section 8.3 (table row action), Section 8.4 (serving the files). PLAN-SIGNiX-DASHBOARD-SYNC-MASTER.md — Plan 6 deliverables.

**Prerequisites:** Plan 1 (SignatureTransaction has status_last_updated, audit_trail_file, certificate_of_completion_file; **SignatureTransactionEvent** exists). Plan 2 (push listener creates events per push). Plan 3 (orchestrator creates **submitted** event and marks document versions "Submitted to SIGNiX"). Plan 5 (download_signed_documents_on_complete stores audit trail and certificate when transaction completes). Dashboard and Deal View tables exist (Plan 4 adds Signers/Status updated; this plan adds a "View" link to the same tables).

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **Detail page** — URL **`/deals/signatures/<pk>/`** (or equivalent under deals app). View (e.g. `signature_transaction_detail`) with same access control as signature transaction list (authenticated users). Content follows DESIGN Section 8.2:
  - **Header:** Transaction ID (or SIGNiX Document Set ID / fallback when blank), Deal (live link to deal detail), document set type (template name), status (prominent), last status updated (formatted timestamp or "—" when null).
  - **Signers table:** Rows in **signing order** (from get_signer_order_for_deal(deal, document_set_template)); columns: order, name, email, authentication method (e.g. get_signer_authentication_for_slot), signed (yes/no from signers_completed_refids or events), **signed at** (occurred_at of party_complete event for this signer, matched by refid/pid or order).
  - **Documents table:** Rows per document instance in the document set; columns: document name/identifier, **As sent** (link to DocumentInstanceVersion with status "Submitted to SIGNiX" for that instance), **Signed** (link to DocumentInstanceVersion with status "Final" when present, else "Pending").
  - **Events table:** Chronological list (transaction.events.order_by("occurred_at")) with human-readable labels: "Transaction submitted" for submitted, then push events (Sent, Signer completed, Transaction completed, Suspended, Cancelled, Expired).
  - **Audit trail and certificate:** Links to View/Download audit trail and certificate when transaction.audit_trail_file and transaction.certificate_of_completion_file are set; otherwise "not available" or hide.
- **Table row action** — On the signature transactions dashboard list and the Deal View related-transactions table, add a **View** link (or button) per row that links to `/deals/signatures/<pk>/` so users can open the detail page from the list.
- **Serving audit trail and certificate** — Two views (e.g. `/deals/signatures/<pk>/audit-trail/` and `/deals/signatures/<pk>/certificate/`) that check authentication and (optionally) that the user has access to the transaction, then stream or return the stored PDF (Content-Disposition: inline or attachment). DESIGN Section 8.4.
- **No on-demand fetch** — This plan does not call DownloadDocument or SIGNiX when the user opens the detail page or clicks audit/certificate links. It only renders data from the database and serves already-stored files from Plan 5.

---

## 2. Detail Page Content (DESIGN Section 8.2)

### 2.1 Header

- **Transaction ID** — SignatureTransaction.transaction_id; when blank, show signix_document_set_id or "—".
- **Deal** — Live link to deal (e.g. "Deal #&lt;id&gt;" → reverse('deals:deal_detail', args=[transaction.deal_id])).
- **Document set type** — transaction.document_set.document_set_template.name when present; "—" when null.
- **Status** — transaction.status, shown prominently (Submitted, In Progress, Complete, Suspended, Cancelled, Expired).
- **Last status updated** — get_status_updated_display(transaction) or formatted status_last_updated; "—" when null.

### 2.2 Signers table

- **Data source:** Signing order from **get_signer_order_for_deal(deal, document_set.document_set_template)** (slot numbers); for each slot, **resolve_signer_slot(deal, slot)** for name and email; **get_signer_authentication_for_slot(deal, slot)** for authentication method.
- **Signed:** True if this signer's refid or pid is in transaction.signers_completed_refids, or derived from party_complete events (match by refid/pid or by order of party_complete events).
- **Signed at:** The **occurred_at** of the **party_complete** event that corresponds to this signer. Match signer position to event by refid/pid when present on the event; otherwise match by order of party_complete events (first party_complete = first signer, etc.). When not signed or no matching event, show "—".

### 2.3 Documents table

- **Rows:** transaction.document_set.instances.order_by('order') (or document set's instance order).
- **Document:** Instance identifier or template document name.
- **As sent:** Link to the **DocumentInstanceVersion** for that instance with status **VERSION_STATUS_SUBMITTED_TO_SIGNIX** ("Submitted to SIGNiX"). Use the version that was current when the transaction was created (same version marked in Plan 3). When no such version exists, show "—" or "Not available."
- **Signed:** Link to the **DocumentInstanceVersion** with status **Final** for that instance (created by download_signed_documents_on_complete). When not yet present, show "Pending" or "Not yet downloaded."

### 2.4 Events table

- **Data source:** transaction.events.order_by("occurred_at").
- **Display:** For each event, show occurred_at (formatted) and a human-readable label from event_type: submitted → "Transaction submitted"; send → "Sent"; party_complete → "Signer completed" (optionally show refid/pid); complete → "Transaction completed"; suspend → "Suspended"; cancel → "Cancelled"; expire → "Expired".
- **Goal:** Timeline from "Transaction submitted" through to terminal state so the user sees a living representation of what happened.

### 2.5 Audit trail and certificate

- When transaction.audit_trail_file: link "View audit trail" / "Download audit trail" → `/deals/signatures/<pk>/audit-trail/`. When not set: "Audit trail not available" or hide.
- When transaction.certificate_of_completion_file: link "View certificate" / "Download certificate" → `/deals/signatures/<pk>/certificate/`. When not set: "Certificate not available" or hide.

### 2.6 Edge cases

- Transaction not Complete: page still shows header, signers, documents, and events; audit/certificate show only when files are present (or "not available" when Complete but files missing).
- Legacy transactions (no submitted event): events list may be empty or only push events; header and signers/documents still render from existing fields.
- Document "As sent" requires versions marked "Submitted to SIGNiX" at submit time (Plan 3 / existing orchestrator).

---

## 3. Table Row Action

- **Dashboard list** — Add a column or cell **View** (or use an icon/link on an existing column). Link target: reverse('deals:signature_transaction_detail', args=[transaction.pk]) or equivalent.
- **Deal View related table** — Same: **View** link per row → signature transaction detail page.
- Show for **all** transactions so users can always open the detail page.

---

## 4. Serving Audit Trail and Certificate

- **URLs** — e.g. `path("signatures/<int:pk>/audit-trail/", views.signature_transaction_audit_trail, name="signature_transaction_audit_trail")` and `path("signatures/<int:pk>/certificate/", views.signature_transaction_certificate, name="signature_transaction_certificate")`.
- **View logic** — Resolve SignatureTransaction by pk; check user is authenticated; optionally check access (e.g. user can see the deal). If transaction.audit_trail_file (or certificate_of_completion_file) is empty, return 404. Stream the file: FileResponse(transaction.audit_trail_file.open('rb'), as_attachment=False) for inline or as_attachment=True for download. Set Content-Type: application/pdf and Content-Disposition per design.
- **Permission** — Same as signature transaction list (authenticated) or restrict to users who can access the deal; design leaves exact rule to implementation.

---

## 5. Implementation Order (Checklist)

### Batch 1 — Detail view and template (steps 1–5)

1. **URL route** — Add path for signature transaction detail, e.g. `path("signatures/<int:pk>/", views.signature_transaction_detail, name="signature_transaction_detail")` in apps.deals.urls.

2. **View signature_transaction_detail** — Get SignatureTransaction by pk (or 404). Check user is authenticated. Build context:
   - **Header:** transaction_id (or fallback), deal, document_set_template name, status, status_last_updated (formatted or "—").
   - **Signers:** Use a **helper get_signers_detail_for_transaction(transaction)** in `apps.deals.signix` (or a small transaction_detail module) that returns a list of dicts: for each slot in get_signer_order_for_deal(deal, document_set.document_set_template), resolve name/email (resolve_signer_slot), authentication (get_signer_authentication_for_slot), signed (from signers_completed_refids or party_complete events), signed_at (occurred_at of matching party_complete event). This keeps the view thin and the logic testable.
   - **Documents:** For each instance in document_set.instances.order_by('order'), version_as_sent (version with status VERSION_STATUS_SUBMITTED_TO_SIGNIX), version_signed (version with status Final or None).
   - **Events:** transaction.events.order_by("occurred_at"); map each event_type to a human-readable label via **get_event_type_display(event_type)** in the same module (e.g. submitted→"Transaction submitted", send→"Sent", party_complete→"Signer completed", complete→"Transaction completed", etc.).
   - **Audit/certificate:** presence of audit_trail_file and certificate_of_completion_file.
   Render template.

3. **Template** — Create templates/deals/signature_transaction_detail.html with sections: **header** (Transaction ID, Deal link, document set type, status, last status updated); **signers table** (columns: order, name, email, authentication, signed, signed at); **documents table** (columns: document, As sent link, Signed link or "Pending"); **events table** (columns: date/time, event label); **audit trail** (link if file present else "not available"); **certificate** (link if file present else "not available").

4. **Verification (Batch 1)** — Open `/deals/signatures/<pk>/` for a transaction with submitted event and push events; confirm header, signers (with signed at when party_complete exists), documents (as sent and signed when applicable), events timeline, and audit/certificate sections render correctly.

5. **View link on dashboard and Deal View** — In signature_transaction_list.html and deal_detail.html (signature transactions table), add a **View** column or link: `<a href="{% url 'deals:signature_transaction_detail' t.pk %}">View</a>`. Update colspan for empty state if needed.

### Batch 2 — Audit trail and certificate file views (steps 6–8)

6. **URLs for audit-trail and certificate** — Add path("signatures/<int:pk>/audit-trail/", ...) and path("signatures/<int:pk>/certificate/", ...).

7. **Views signature_transaction_audit_trail and signature_transaction_certificate** — Resolve transaction; require login; if file field empty return 404; return FileResponse with transaction.audit_trail_file or certificate_of_completion_file, Content-Type application/pdf, Content-Disposition inline (or attachment per product preference).

8. **Verification (Batch 2)** — From detail page, click "View audit trail" and "View certificate" when files exist; confirm PDF opens or downloads. For transaction without files, confirm detail page shows "not available" and direct visit to audit-trail URL returns 404.

---

## 5a. Implementation Batches and Verification

### Batch 1 — Detail page and View link

**Includes:** signature_transaction_detail view and template (header, signers table, documents table, events table, audit trail and certificate sections); URL routing; View link on dashboard list and Deal View table.

**How to test:** Open detail page from list; confirm header (Transaction ID, Deal link, document set type, status, last status updated), signers table (order, name, email, authentication, signed, signed at), documents table (as sent link, signed link or Pending), events table (chronological with labels), audit trail and certificate (links when files present, "not available" when absent). Confirm View link appears on each row in list and Deal View table. **Run unit tests (Section 6):** `python manage.py test apps.deals.tests.test_signature_transaction_detail` — all pass.

### Batch 2 — File-serving views

**Includes:** signature_transaction_audit_trail and signature_transaction_certificate views; URL routes; permission check and FileResponse.

**How to test:** Click "View audit trail" / "View certificate" from detail page; confirm PDF is returned. Unauthenticated or missing file returns 404 or 403 as designed. **Run unit tests (Section 6):** test_signature_transaction_audit_trail_returns_404_when_file_empty, test_signature_transaction_audit_trail_returns_pdf_when_file_set, and certificate equivalents.

---

## 6. Unit Tests (add to apps.deals.tests)

Create **apps/deals/tests/test_signature_transaction_detail.py** (or add to an existing deals test module). Use the same test setup as other deals tests (Deal, DocumentSet, User, SignatureTransaction; staff user for views that require it).

### 6.1 Detail view

- **test_signature_transaction_detail_returns_200_for_valid_pk** — Create a SignatureTransaction (with deal, document_set, signix_document_set_id, status). As an authenticated user, GET the detail URL (e.g. reverse('deals:signature_transaction_detail', args=[tx.pk])). Assert response.status_code == 200. Assert response contains key content: e.g. transaction id or signix_document_set_id, status text, "Signers" or "Documents" (section headings), or deal link.
- **test_signature_transaction_detail_returns_404_for_invalid_pk** — GET detail URL with a non-existent pk (e.g. 99999). Assert response.status_code == 404.

### 6.2 Audit trail and certificate file views

- **test_signature_transaction_audit_trail_returns_404_when_file_empty** — Transaction with audit_trail_file empty (default). As authenticated user, GET the audit-trail URL for that transaction. Assert response.status_code == 404.
- **test_signature_transaction_audit_trail_returns_pdf_when_file_set** — Transaction with audit_trail_file set (e.g. save a small PDF ContentFile to the field). GET the audit-trail URL. Assert response.status_code == 200, response['Content-Type'] == 'application/pdf' (or contains 'application/pdf'), and response content is non-empty.
- **test_signature_transaction_certificate_returns_404_when_file_empty** — Same as audit trail: transaction with certificate_of_completion_file empty; GET certificate URL; assert 404.
- **test_signature_transaction_certificate_returns_pdf_when_file_set** — Same as audit trail: transaction with certificate_of_completion_file set; GET certificate URL; assert 200 and Content-Type application/pdf.

### 6.3 List and Deal View links (optional)

- **test_list_and_deal_view_contain_link_to_detail** — GET signature_transaction_list; assert response contains a link to the detail URL for at least one transaction (e.g. reverse('deals:signature_transaction_detail', args=[tx.pk]) or "View"). GET deal_detail for a deal that has a signature transaction; assert the signature transactions table contains a link to that transaction’s detail page.

---

## 7. Data Sourcing Summary

| Section    | Source |
|-----------|--------|
| Header    | transaction.transaction_id, .deal, .document_set.document_set_template.name, .status, .status_last_updated; get_status_updated_display(transaction). |
| Signers   | **get_signers_detail_for_transaction(transaction)** (in signix or transaction_detail module): uses get_signer_order_for_deal, resolve_signer_slot, get_signer_authentication_for_slot; signed from signers_completed_refids or party_complete events; signed_at from transaction.events.filter(event_type="party_complete") matched by refid/pid or order. |
| Documents | document_set.instances.order_by('order'); per instance: version with status VERSION_STATUS_SUBMITTED_TO_SIGNIX (as sent), version with status Final (signed). |
| Events    | transaction.events.order_by("occurred_at"); **get_event_type_display(event_type)** for human-readable label. |
| Audit/certificate | transaction.audit_trail_file, transaction.certificate_of_completion_file. |

---

## 8. File Summary

| Item | Value |
|------|--------|
| App | `apps.deals` |
| Views | signature_transaction_detail, signature_transaction_audit_trail, signature_transaction_certificate |
| Templates | templates/deals/signature_transaction_detail.html; updates to signature_transaction_list.html and deal_detail.html (View link) |
| URLs | signatures/<pk>/; signatures/<pk>/audit-trail/; signatures/<pk>/certificate/ |
| Helpers (recommended) | **get_signers_detail_for_transaction(transaction)** and **get_event_type_display(event_type)** in apps.deals.signix (or apps.deals.services.transaction_detail) so the view stays thin and logic is reusable/testable. |
| Tests | apps/deals/tests/test_signature_transaction_detail.py — detail view (200/404, key content), audit trail and certificate (404 when empty, 200+PDF when set), optional list/deal link tests |

---

## 9. Open Issues / Implementation Decisions

- **Content-Disposition:** Use inline so the PDF opens in the browser, or attachment so it downloads. Design leaves choice to implementation; document in view or config.
- **Permission:** Detail page and file views can use the same permission as signature_transaction_list (e.g. login_required). Optionally restrict to users who have access to the transaction's deal (e.g. staff or deal.lease_officer); design Section 8.4 leaves exact pattern to implementation.
- **Signed at matching:** When multiple party_complete events exist, match to signer order by refid/pid when present on the event; when refid/pid is absent or ambiguous, match by order of party_complete events (first event = first signer in order). Implementation can add a helper that returns (signer_index, signed_at) per signer from transaction.events and signers_completed_refids.

---

*End of plan. Implementation completes the dashboard/sync feature set from DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md Section 8.*

# Plan: SIGNiX Download on Complete (Dashboard/Sync Plan 5)

When a push with **action=complete** is received, the app runs the download flow asynchronously: call **DownloadDocument** (requesting the audit trail and optional certificate of completion), map returned signed documents to the transaction's document_set instances, create new **DocumentInstanceVersion**s (status=Final), **store the audit trail and certificate of completion PDFs on the SignatureTransaction**, then call **ConfirmDownload**. Storage is **proactive**—done in this flow so the signature transaction detail page (Plan 6) only serves already-stored files; the system does not retrieve them when the user visits that page.

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 6 (Download on Completion), Section 6.5a (Store audit trail and certificate on SignatureTransaction), Section 7.4 (audit_trail_file, certificate_of_completion_file). KNOWLEDGE-SIGNiX.md — DownloadDocument request/response (signed PDFs, audit trail, certificate of completion). PLAN-SIGNiX-DASHBOARD-SYNC-MASTER.md — Plan 5 deliverables.

**Prerequisites:** Plan 1 (PLAN-SIGNiX-SYNC-MODEL) is implemented: SignatureTransaction has audit_trail_file and certificate_of_completion_file. Plan 2 (push listener) triggers download_signed_documents_on_complete on action=complete. DocumentInstanceVersion and document_set.instances exist (PLAN-ADD-DOCUMENT-SETS or equivalent). **For real end-to-end verification driven by SIGNiX completion pushes, Django and ngrok must be running in parallel** so the `complete` callback reaches the local app.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **download_signed_documents_on_complete(transaction)** — Single callable (DESIGN Section 6) that: (1) idempotency check (skip if already processed, e.g. Final versions exist for this transaction’s document_set); (2) call **DownloadDocument** with same endpoint/credentials as SubmitDocument, **including IncludeAuditData** and **AuditTrailFormat** (e.g. pdf) and optional certificate-of-completion element per Flex API; (3) parse response: signed PDFs (one per document), audit trail PDF, certificate of completion PDF (when present); (4) map signed documents to document_set.instances by order or RefID; (5) create new DocumentInstanceVersion per instance (file=signed PDF bytes, status=Final, version_number=next); (6) **save audit trail PDF to transaction.audit_trail_file and certificate PDF to transaction.certificate_of_completion_file** (Section 6.5a); (7) call **ConfirmDownload**. Run asynchronously from the push view (e.g. threading.Thread or fire-and-forget). Celery not required.
- **Proactive storage** — Audit trail and certificate are retrieved and stored **in this completion flow**, not when the user opens the View Signature Transaction page. Plan 6 only displays or streams the already-stored files.
- **Error handling** — Log DownloadDocument or ConfirmDownload failures; do not retry from the view. If parsing or saving audit trail/certificate fails, log the error but do not fail the rest of the flow (signed document versions and ConfirmDownload still proceed). Document partial-mapping behavior when document count does not match.
- **Out of scope this plan:** Signature transaction detail page and View link (Plan 6). No push or SubmitDocument changes.

---

## 2. DownloadDocument Request and Response

### 2.1 Request (Flex API)

- **CustInfo** — Same credentials as SubmitDocument (from SignixConfig).
- **DocumentSetID** — transaction.signix_document_set_id.
- **IncludeAuditData** — true (element and value per Flex API) so the response includes the audit trail.
- **AuditTrailFormat** — e.g. `pdf` (required when IncludeAuditData is true).
- **Certificate of completion** — Include the optional element per Flex API so the response includes the certificate-of-completion summary PDF when supported.
- **UseConfirmDownload** — true when using retention (DelDocsAfter); required for ConfirmDownload to apply.

Exact element names and structure per [Flex API — DownloadDocument](https://www.signix.com/apidocumentation) and KNOWLEDGE-SIGNiX.md.

### 2.2 Response parsing

- **Signed documents** — One PDF per Form submitted; order matches document_set.instances order (or match by RefID if API returns it per document). Map to document_set.instances (e.g. by position: first returned doc = first instance in order).
- **Audit trail** — Separate section in the response (per Flex API); decode Base64 and save to transaction.audit_trail_file (same media storage as DocumentInstanceVersion; upload_to e.g. "signature_transactions/%Y/%m/").
- **Certificate of completion** — Separate section when requested and present; decode and save to transaction.certificate_of_completion_file.
- **Idempotency** — If the flow runs again (e.g. retry or manual re-download), overwriting existing audit_trail_file and certificate_of_completion_file is acceptable; or only save when the field is currently empty. Document the choice in implementation.

---

## 3. Flow Summary

1. **Idempotency check** — If transaction already processed (e.g. all document_set.instances have at least one DocumentInstanceVersion with status=Final), skip and log.
2. **DownloadDocument** — Request with DocumentSetID, IncludeAuditData, AuditTrailFormat, optional certificate element.
3. **Parse response** — Signed PDFs list, audit trail PDF bytes, certificate PDF bytes (if present).
4. **Map and create versions** — For each document_set.instances (in order), create new DocumentInstanceVersion with file=signed PDF bytes, status=Final, version_number=next.
5. **Store audit trail and certificate** — Save audit trail bytes to transaction.audit_trail_file, certificate bytes to transaction.certificate_of_completion_file; transaction.save(update_fields=[...]).
6. **ConfirmDownload** — Call with same DocumentSetID and credentials.

---

## 4. Helpers and Location

- **download_signed_documents_on_complete(transaction)** — In `apps.deals.signix`. Signature: `(transaction: SignatureTransaction) -> None`. Replaces the stub from Plan 2. Perform full flow above; catch exceptions, log, and do not raise so the push view is not affected.
- **DownloadDocument client** — Reuse same transport and credentials as SubmitDocument (SignixConfig, endpoint Webtest or Production). Build request XML per Flex API; parse response XML (ElementTree or lxml) to extract document elements and audit trail/certificate sections.

---

## 5. Implementation Order (Checklist)

### Batch 1 — DownloadDocument call and response parsing (steps 1–4)

1. **DownloadDocument request builder** — In signix.py (or a dedicated module), implement a function that builds the DownloadDocument request XML: CustInfo, DocumentSetID, IncludeAuditData=true, AuditTrailFormat=pdf, optional certificate element, UseConfirmDownload=true. Reuse credential loading from submit.

2. **DownloadDocument client call** — POST to same endpoint as SubmitDocument with method=DownloadDocument and request=...; parse response XML; check StatusCode; extract list of document elements (signed PDFs), audit trail element (Base64 data), certificate element (if present).

3. **Map documents to instances** — document_set.instances.order_by("order"); match first response document to first instance, etc. (or by RefID if API returns it). Handle count mismatch: log error; create versions for matched only; do not fail entire flow for single mismatch if partial save is acceptable.

4. **Verification (Batch 1)** — Unit test: mock HTTP response with sample XML (signed doc + audit trail section); assert parsing yields correct number of documents and audit trail bytes.

### Batch 2 — Create versions, store audit/certificate, ConfirmDownload (steps 5–9)

5. **Create DocumentInstanceVersion per instance** — For each mapped (instance, signed_pdf_bytes), create DocumentInstanceVersion(document_instance=instance, version_number=next_version(instance), status="Final", file=ContentFile(signed_pdf_bytes)). Save file to storage (FileField.save() with name and content).

6. **Save audit trail and certificate on transaction** — Assign audit trail bytes to transaction.audit_trail_file (e.g. ContentFile(audit_trail_bytes); save with a filename like "audit_trail.pdf"). Same for certificate_of_completion_file when present. transaction.save(update_fields=["audit_trail_file", "certificate_of_completion_file"]).

7. **ConfirmDownload** — Build ConfirmDownload request per Flex API (DocumentSetID, CustInfo); POST; log failure but do not raise.

8. **download_signed_documents_on_complete(transaction)** — Implement full flow: idempotency check, steps 2–7. Replace Plan 2 stub. Ensure async invocation from push view (Plan 2) is already in place.

9. **Verification (Batch 2)** — Integration test or manual: trigger action=complete for a completed transaction (or call download_signed_documents_on_complete directly with a transaction that has signix_document_set_id and document_set); assert DocumentInstanceVersions created with status Final, transaction.audit_trail_file and transaction.certificate_of_completion_file are set when response contains them, ConfirmDownload was called. **If this verification depends on a real SIGNiX `complete` push, keep Django and ngrok running in parallel for the full callback/download flow.**

---

## 5a. Implementation Batches and Verification

### Batch 1 — DownloadDocument client and parsing

**Includes:** DownloadDocument request XML builder; HTTP call and response parsing; extraction of signed docs list, audit trail bytes, certificate bytes.

**How to test:** Mock response XML; assert parsed documents count and audit trail/certificate presence.

### Batch 2 — Mapping, versions, audit/certificate storage, ConfirmDownload, wire-up

**Includes:** Map response docs to document_set.instances; create DocumentInstanceVersion per instance; save audit_trail_file and certificate_of_completion_file on transaction; ConfirmDownload call; download_signed_documents_on_complete(transaction) implementing full flow; Plan 2 stub replaced.

**How to test:** With a transaction and document_set (and mocked or real DownloadDocument response), call download_signed_documents_on_complete(transaction); assert versions created, transaction.audit_trail_file and certificate_of_completion_file set when present in response, ConfirmDownload invoked. Mocked tests do not require ngrok. Real end-to-end verification through SIGNiX does require Django and ngrok running in parallel so the `complete` callback reaches Plan 2’s listener and triggers this flow.

---

## 6. Unit Tests

Create **apps/deals/tests/test_signix_download_on_complete.py** (or add to existing signix tests).

### 6.1 Parsing (no HTTP)

- **test_parse_download_document_response_extracts_documents_and_audit_trail** — Use **canned DownloadDocument response XML** (no HTTP call): pass the XML string to the response-parsing helper (or a function that parses the same structure the real client uses). Assert: (1) parsed document count matches the number of document elements in the canned XML; (2) audit trail bytes are extracted (e.g. Base64 decode of the audit trail element) and length/content-type as expected; (3) optionally certificate bytes when the canned XML includes the certificate element. This tests parsing logic in isolation so implementation can refactor HTTP without breaking parsing tests.
- **test_parse_download_document_response_certificate_optional_when_absent** — Canned XML without the certificate-of-completion element. Assert parsing succeeds and certificate bytes are None or absent; document count and audit trail still extracted.
- **test_parse_download_document_response_document_count_mismatch** — (Optional.) Canned XML with more or fewer document elements than document_set.instances.count(). Assert parsing returns the correct list lengths; document behavior when count mismatches (e.g. partial mapping, log and continue) is asserted in integration tests or documented.

### 6.2 download_signed_documents_on_complete (integration)

- **test_download_signed_documents_on_complete_skips_when_already_processed** — Transaction whose document_set already has Final versions for all instances; call download_signed_documents_on_complete(transaction); assert DownloadDocument not called (mock) or no new versions created.
- **test_download_signed_documents_on_complete_creates_versions_and_stores_audit_certificate** — Mock DownloadDocument response (signed PDFs + audit trail + certificate); call download_signed_documents_on_complete(transaction); assert new DocumentInstanceVersions with status=Final, transaction.audit_trail_file and transaction.certificate_of_completion_file are set.
- **test_download_signed_documents_on_complete_calls_confirm_download** — Mock DownloadDocument and ConfirmDownload; after download_signed_documents_on_complete(transaction), assert ConfirmDownload was called with same DocumentSetID.
- **test_audit_trail_failure_does_not_fail_flow** — Mock response where audit trail parsing fails (e.g. missing element); assert signed document versions are still created and ConfirmDownload still called; transaction may have empty audit_trail_file.

---

## 7. File Summary

| Item | Value |
|------|--------|
| App / module | `apps.deals.signix` (and possibly views if async trigger lives there) |
| New/updated | **download_signed_documents_on_complete(transaction)** (replaces Plan 2 stub); DownloadDocument request/response helpers |
| Model usage | SignatureTransaction.audit_trail_file, certificate_of_completion_file (Plan 1); document_set.instances; DocumentInstanceVersion |
| Tests | apps/deals/tests/test_signix_download_on_complete.py |

---

## 8. Open Issues / Implementation Decisions

- **Idempotency:** "Already processed" can be defined as: every document_set.instances has at least one DocumentInstanceVersion with status=Final. Alternatively, a flag on SignatureTransaction (e.g. documents_downloaded=True) set after first successful run. Design leaves choice to implementation; document in code.
- **Audit/certificate save failure:** If saving audit_trail_file or certificate_of_completion_file fails (e.g. disk full), log and continue; signed versions and ConfirmDownload still run. DESIGN Section 6.5a.
- **Certificate optional:** API may not return certificate if not requested or not supported; check response for presence before saving certificate_of_completion_file.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-TRANSACTION-DETAIL.md (Plan 6).*

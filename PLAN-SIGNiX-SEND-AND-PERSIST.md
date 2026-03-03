# Plan: Send to SIGNiX and Persist (Plan 6)

This document outlines how to **send** the built SubmitDocument body to SIGNiX (POST), parse the response, call GetAccessLink when needed to obtain the first signer's URL, create a `SignatureTransaction` record, and update `DocumentInstanceVersion` status to "Submitted to SIGNiX". The orchestrator ties together validation (Plan 5), body building (Plan 5), send, and persistence so the view (Plan 7) can call a single entry point.

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — Section 6 (Transaction Packager), Section 6.1 (Responsibilities), Section 6.3 (Error handling), Section 6.4 (Separation of body construction and send). KNOWLEDGE-SIGNiX.md — endpoints (Webtest/Production), SubmitDocument response, GetAccessLink, response parsing (ElementTree).

**Prerequisites:** Plans 1 (SignixConfig, get_signix_config), 2 (SignatureTransaction model), 3 (signer service), 4 (signer order/auth), and 5 (validate_submit_preconditions, build_submit_document_body) are implemented. Document Sets with `DocumentInstanceVersion` and a `status` field (e.g. Draft, Submitted to SIGNiX, Final) exist from PLAN-ADD-DOCUMENT-SETS.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Send function** — POST the SubmitDocument XML body to the SIGNiX endpoint (Webtest or Production per SignixConfig.demo_only). Use the transport and content type required by the Flex API (e.g. `application/x-www-form-urlencoded` with the request XML in a designated parameter; see Flex API documentation). Parse the response with ElementTree; extract **DocumentSetID** and, if present, the **first-signer signing URL**.
- **GetAccessLink** — If the SubmitDocument response does **not** include the first-signing URL, call **GetAccessLink** for the **first signer** (DocumentSetID from SubmitDocument response; member reference for first signer per Flex API). Use the returned URL as `first_signing_url`.
- **Orchestrator** — Single entry point used by the view (Plan 7): (1) validate via `validate_submit_preconditions(deal, document_set)`; (2) call `build_submit_document_body(deal, document_set)` to get `(body, metadata)`; (3) optionally log or store the body for debugging; (4) call the send function; (5) parse response; (6) call GetAccessLink if first-signing URL not in response; (7) create `SignatureTransaction` (deal, document_set, signix_document_set_id, transaction_id from metadata, status=Submitted, first_signing_url, submitted_at); (8) update the **latest** `DocumentInstanceVersion` for each instance in the document set to status **"Submitted to SIGNiX"**; (9) return `(SignatureTransaction, first_signing_url)`.
- **Error handling** — Validation errors (SignixValidationError): do not perform HTTP; surface errors to caller (e.g. for view to show a message). SIGNiX API errors (HTTP 4xx/5xx or error element in response): do **not** create SignatureTransaction; do **not** update version status; return a structured failure (e.g. exception or result object) with a user-facing message and log the response for debugging.
- **Integration tests** — Mock HTTP to SIGNiX (e.g. `responses` or `unittest.mock.patch` on `requests.post`); assert that on success a SignatureTransaction is created with correct fields and that the latest DocumentInstanceVersion for each instance has status "Submitted to SIGNiX"; assert that on API error no transaction is created and no version is updated.
- **Out of scope:** Send for Signature button and front-end (Plan 7); dashboard or Deal View transaction list (Plans 8, 9).

---

## 2. Endpoints and Transport

- **Webtest:** `https://webtest.signix.biz/sdd/b2b/sdddc_ns.jsp` (KNOWLEDGE-SIGNiX).
- **Production:** `https://signix.net/sdd/b2b/sdddc_ns.jsp` (KNOWLEDGE-SIGNiX).
- **Selection:** Use **SignixConfig.demo_only**: when True → Webtest; when False → Production.
- **Transport (resolved from Flex API):** POST with **Content-Type application/x-www-form-urlencoded**. Form parameters (lowercase, case-sensitive): **`method`** = web method name (outer request element with "Rq" removed, e.g. `SubmitDocument`); **`request`** = full request XML. Same URL for all methods. Credentials are inside the request XML (CustInfo). See KNOWLEDGE-SIGNiX — Transport, SubmitDocument response, GetAccessLink-Signer.

---

## 3. Send Function

**Signature:** `send_submit_document(body: str, endpoint_url: str, config: SignixConfig) -> SendSubmitDocumentResult`

- **Inputs:** `body` = full SubmitDocument request XML string; `endpoint_url` = Webtest or Production URL; `config` = SignixConfig (used only for endpoint selection; credentials are already inside the request XML in CustInfo, so no separate auth for the POST). POST with `data={"method": "SubmitDocument", "request": body}` and Content-Type application/x-www-form-urlencoded.
- **Behavior:** Parse the response with ElementTree. Check **StatusCode** first (0 = success; non-zero = error — raise SignixApiError with message from StatusDesc). On success, extract **DocumentSetID** and, if present, the **first-party pickup link** (element name per Flex API schema; see KNOWLEDGE-SIGNiX — SubmitDocument response). If the response includes that URL, use it as first_signing_url; otherwise leave as None for the orchestrator to call GetAccessLink.
- **Return:** A result type: `document_set_id: str`, `first_signing_url: str | None`. On HTTP error (4xx/5xx) or StatusCode non-zero, **raise** SignixApiError (message, http_status, response_text). Do not return a partial result on failure.

**Recommendation:** Define `SignixApiError(Exception)` with attributes such as `message`, `http_status`, `response_text` (or `response_element`). The orchestrator catches it and does not create or update any records.

---

## 4. GetAccessLink

- **When:** Only when the SubmitDocument response does **not** include the first-signer signing URL (i.e. `first_signing_url` is None after parsing).
- **Endpoint:** Same URL as SubmitDocument; same transport (POST, form parameters `method` and `request`). Method name = outer request element with "Rq" removed (e.g. `GetAccessLinkSigner` — confirm exact name in Flex API doc for the Signer variant).
- **Request (resolved from Flex API):** CustInfo (same as SubmitDocument: Sponsor, Client, UserId, Pswd, Workgroup from config). Data: **DocumentSetID** (from SubmitDocument response), **MemberInfoNumber** = **1** for the first signer (integer; 1 = first party, 2 = second, etc.). Optional: PermanentLink=true for a long-standing link. Build the request XML per Flex API schema; exact element names in [Flex API — GetAccessLink](https://www.signix.com/apidocumentation).
- **Response:** On StatusCode 0, response contains the signer URL (exact element name per schema). Return that URL. On failure, raise SignixApiError.
- **Signature:** `get_access_link_signer(document_set_id: str, config: SignixConfig, member_info_number: int = 1) -> str`. Use `member_info_number=1` for the first signer.

---

## 5. Orchestrator

**Signature:** `submit_document_set_for_signature(deal, document_set) -> tuple[SignatureTransaction, str]`

- **Inputs:** `deal` (Deal), `document_set` (DocumentSet). The deal must own the document set; validation enforces this.
- **Behavior:**
  1. **Validate:** Call `validate_submit_preconditions(deal, document_set)`. On `SignixValidationError`, re-raise or convert to a result type so the view can show `exception.errors` without making any HTTP call.
  2. **Build body:** Call `build_submit_document_body(deal, document_set)`. Receives `(body, metadata)`. Use `metadata["transaction_id"]` for persistence.
  3. **Optional:** Log the body at DEBUG level or store to a debug path (avoid logging credentials at INFO).
  4. **Send:** Call `send_submit_document(body, endpoint_url, config)`. On `SignixApiError`, do **not** create SignatureTransaction; do **not** update any DocumentInstanceVersion; return or raise so the view can show a generic message (e.g. "SIGNiX request failed; try again or contact support.") and log the exception details.
  5. **GetAccessLink (if needed):** If the send result's `first_signing_url` is None, call `get_access_link_signer(document_set_id, config, member_info_number=1)` to obtain the URL (MemberInfoNumber 1 = first signer per Flex API). On failure: **Decided** — still create the transaction (step 6) with `first_signing_url=""` so we do not leave SIGNiX with a transaction that has no local record; log the GetAccessLink failure.
  6. **Persist transaction:** `SignatureTransaction.objects.create(deal=deal, document_set=document_set, signix_document_set_id=result.document_set_id, transaction_id=metadata.get("transaction_id"), status=SignatureTransaction.STATUS_SUBMITTED, first_signing_url=first_signing_url or "")`. `submitted_at` is set by `auto_now_add=True` on the model.
  7. **Update version status:** For each instance in `document_set.instances.all()`, get the latest version (e.g. `instance.versions.order_by("-version_number").first()`), and set `version.status = "Submitted to SIGNiX"` and `version.save(update_fields=["status"])`. Use the literal string **"Submitted to SIGNiX"** to match DESIGN-DOCS and the model help text.
  8. **Return:** `(signature_transaction, first_signing_url)` so the view can open the URL in a new window (Plan 7).

**Location:** Same module as send and GetAccessLink, e.g. `apps.deals.signix`.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Send and parse (steps 1–4)

1. **SignixApiError and send_submit_document**
   - In `apps/deals/signix.py`, define `SignixApiError(Exception)` with `message`, `http_status` (optional), `response_text` (optional). Implement `send_submit_document(body, endpoint_url, config)` that POSTs the body (transport per Flex API doc), parses response with ElementTree, extracts DocumentSetID and first-signing URL if present. On HTTP error or error in response, raise SignixApiError. Return a small result object (e.g. dataclass) with `document_set_id`, `first_signing_url` (optional), and optionally `raw_response_text`.

2. **Endpoint URL helper**
   - Add a helper, e.g. `get_signix_submit_endpoint(config: SignixConfig) -> str`, that returns the Webtest or Production SubmitDocument URL based on `config.demo_only`. Use the same base for GetAccessLink if the path differs (or a separate helper per API call).

3. **Response parsing**
   - Implement response parsing per Flex API SubmitDocument response schema. Document the expected element path for DocumentSetID and first-signing URL (or leave as implementation note to align with docs). Handle namespace if the response uses xmlns.

4. **Verification (Batch 1)**
   - Unit test with mocked HTTP: mock a successful response XML; call send_submit_document; assert result has document_set_id and optionally first_signing_url. Mock a 500 response; assert SignixApiError is raised and no result returned.

### Batch 2 — GetAccessLink and orchestrator (steps 5–9)

5. **GetAccessLink**
   - Implement `get_access_link_signer(document_set_id, config, member_info_number=1)`. Build request XML per Flex API (CustInfo, Data/DocumentSetID, Data/MemberInfoNumber). POST to same endpoint with `method` = GetAccessLink Signer method name and `request` = XML. Parse response; extract URL when StatusCode is 0. See KNOWLEDGE-SIGNiX — GetAccessLink Signer.

6. **Orchestrator**
   - Implement `submit_document_set_for_signature(deal, document_set)`. Call validate_submit_preconditions (catch SignixValidationError); build_submit_document_body; send_submit_document; GetAccessLink if needed; create SignatureTransaction; update latest DocumentInstanceVersion per instance to "Submitted to SIGNiX"; return (transaction, first_signing_url). Use transaction_id from metadata.

7. **Version status constant (optional)**
   - Define a constant for the version status string, e.g. in `apps.documents.models` or in signix module: `VERSION_STATUS_SUBMITTED_TO_SIGNIX = "Submitted to SIGNiX"` so it can be reused and kept in sync. Optional; literal string is acceptable.

8. **Error handling in orchestrator**
   - On SignixValidationError: re-raise (view will catch and display errors). On SignixApiError: **log at ERROR** with message and optionally **truncated** response_text (e.g. first 500 chars); **do not** log password or full request XML. Re-raise so the view can show a generic message.

9. **Verification (Batch 2)**
   - Integration test: with mocked HTTP (SubmitDocument success, optional GetAccessLink success), call submit_document_set_for_signature with a fixture deal and document_set. Assert SignatureTransaction created with correct deal, document_set, signix_document_set_id, transaction_id, first_signing_url; assert each instance's latest version has status "Submitted to SIGNiX". With mocked SubmitDocument failure, assert no SignatureTransaction created and no version status updated.

### Batch 3 — Tests and edge cases (steps 10–12)

10. **Integration tests**
    - Tests: (1) Full success path: mocked SubmitDocument returns DocumentSetID and first_signing_url; assert transaction created, versions updated. (2) SubmitDocument returns DocumentSetID but no first_signing_url; mock GetAccessLink to return URL; assert transaction created with that URL, versions updated. (3) SubmitDocument returns 4xx; assert SignixApiError raised, no transaction, no version update. (4) Validation failure (e.g. wrong deal): assert SignixValidationError, no HTTP call (verify mock not called or call count zero).

11. **Edge cases**
    - Empty document set is already rejected by validate_submit_preconditions. **GetAccessLink failure after SubmitDocument success:** **Decided** — Create the transaction and persist DocumentSetID and transaction_id; set first_signing_url to empty; log the GetAccessLink failure. User sees the transaction and can contact support or retry; we avoid leaving SIGNiX with a transaction that has no local record.

12. **Verification (Batch 3)**
    - Run full test suite for signix and integration tests. All pass.

---

## 6a. Implementation Batches and Verification

**Batch 1 — Send and parse**

**Includes:** SignixApiError, send_submit_document(body, endpoint_url, config), endpoint URL helper, response parsing (DocumentSetID, optional first_signing_url).

**How to test after Batch 1:**

1. Mock successful SubmitDocument response XML (with DocumentSetID); call send_submit_document; assert result.document_set_id matches. Mock 500; assert SignixApiError raised.
2. Unit tests for send_submit_document with mocked requests.

**Batch 2 — GetAccessLink and orchestrator**

**Includes:** get_access_link_signer (or equivalent), submit_document_set_for_signature(deal, document_set), version status update to "Submitted to SIGNiX", error handling (re-raise validation and API errors).

**How to test after Batch 2:**

1. Integration test: submit_document_set_for_signature with mocked SubmitDocument (and GetAccessLink if needed); assert SignatureTransaction created, versions updated.
2. Assert on transaction_id from metadata, signix_document_set_id from response, first_signing_url from response or GetAccessLink.

**Batch 3 — Tests and edge cases**

**Includes:** Additional integration tests for failure paths, GetAccessLink-failure policy (document choice).

**How to test after Batch 3:**

1. All tests pass. Document any GetAccessLink-failure policy in Open issues.

---

## 7. File Summary

| Item | Value |
|------|--------|
| Module | `apps.deals.signix` |
| Exceptions | `SignixValidationError` (Plan 5), `SignixApiError` (this plan) |
| Functions | `send_submit_document(body, endpoint_url, config)`, `get_access_link_signer(document_set_id, config, member_info_number=1)`, `submit_document_set_for_signature(deal, document_set) -> tuple[SignatureTransaction, str]` |
| Helpers | Endpoint URL from config (Webtest vs Production) |
| Version status | `"Submitted to SIGNiX"` (literal or constant in documents app) |
| Tests | Integration tests with mocked HTTP (SubmitDocument, GetAccessLink) |

---

## 8. Open Issues / Implementation Decisions

- **SubmitDocument response element names:** KNOWLEDGE-SIGNiX now documents that the response has Status (StatusCode, StatusDesc), DocumentSetID, and optionally a first-party pickup link. **Exact XML element names** (e.g. for the pickup link) may vary by schema; implement parsing using the Flex API schema or annotated examples and add a short comment in code (e.g. "DocumentSetID / first-party link path per Flex API SubmitDocument response").

- **GetAccessLink method and element names:** **Resolved:** Same endpoint as SubmitDocument; method = outer request element with "Rq" removed (e.g. GetAccessLinkSigner). Request: CustInfo + Data/DocumentSetID + Data/MemberInfoNumber (integer 1 for first signer). Confirm exact request root name (GetAccessLinkSignerRq vs GetAccessLinkRq) and response URL element from Flex API schema when implementing.

- **Transport and parameter name:** **Resolved:** POST, application/x-www-form-urlencoded; form parameters **`method`** (lowercase) and **`request`** (full XML). See KNOWLEDGE-SIGNiX — Transport.

- **GetAccessLink failure after SubmitDocument success:** **Decided:** Create the transaction with empty first_signing_url; persist DocumentSetID and transaction_id; log the GetAccessLink failure. User sees the transaction; we avoid leaving SIGNiX with no local record.

- **First signer reference for GetAccessLink:** **Resolved:** Use **MemberInfoNumber = 1** (integer). 1 = first party, 2 = second, etc. Per Flex API GetAccessLink-Signer request.

- **Logging:** **Decided:** Log request body at DEBUG only. Log SignixApiError at ERROR with message and truncated response_text (e.g. first 500 chars); do not log password or full XML with credentials.

- **Version status constant:** **Decided:** Use literal `"Submitted to SIGNiX"` for simplicity; refactor to a constant in apps.documents later if status values are centralized.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-SEND-FOR-SIGNATURE.md (Plan 7).*

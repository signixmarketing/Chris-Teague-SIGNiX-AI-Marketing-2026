# Plan: Send for Signature — Deal Detail (Plan 7)

This document outlines how to **replace the Send for Signature stub** on the Deal detail page: wire the button to the Plan 6 orchestrator, open the first signer’s signing URL in a separate window on success, and control button visibility using the same validation used for submit.

**Design reference:** [DESIGN-SIGNiX-SUBMIT.md](DESIGN-SIGNiX-SUBMIT.md) — Section 7.1 (Deal detail — Send for Signature), Section 7.2 (First signer signing experience). PLAN-ADD-DOCUMENT-SETS — Send for Signature stub at `POST /deals/<pk>/documents/send-for-signature/`, deal detail Documents section.

**Prerequisites:** Plan 6 (orchestrator `submit_document_set_for_signature`, SignixValidationError, SignixApiError) is implemented. Plans 1–5 (SignixConfig, SignatureTransaction, signer service, signers table, validate_submit_preconditions, build_submit_document_body) are in place. The stub view and button exist (POST to `deals:deal_send_for_signature_stub`, URL `/deals/<pk>/documents/send-for-signature/`).

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Replace stub** — The Send for Signature button currently POSTs to the stub view and shows “SIGNiX integration will be available in a future release.” Replace with real behavior: POST calls the Plan 6 orchestrator `submit_document_set_for_signature(deal, document_set)`. On success: create SignatureTransaction, update version status, and **open the first signer’s signing URL in a separate window** so the user stays on the Deal detail page. On failure: show an error message and stay on deal detail (no redirect away on error).
- **Opening the signing URL** — After a successful submit, the user must be able to sign in a **separate window/tab** without leaving the Lease app. Options: (A) Redirect back to deal detail with the URL stored in session; the deal detail template includes a script that opens the URL in a new window and clears the session key. (B) Redirect to a dedicated “Sign in new window” page that opens the URL via script and then redirects to deal detail. See Section 4.
- **Button visibility** — Show the Send for Signature button when a document set exists with at least one instance **and** validation would pass (SignixConfig present with submitter email, all signer slots resolved, etc.). When validation would not pass (e.g. no SignixConfig, missing submitter email, unresolved signer), **disable** the button and show a clear reason (e.g. tooltip or inline message). Reuse `validate_submit_preconditions(deal, document_set)` to determine if the button should be enabled and to get the reason when disabled.
- **Error handling** — **SignixValidationError:** Show the validation errors (e.g. first error or bullet list) so the user knows what to fix. **SignixApiError:** Show a generic message (e.g. “SIGNiX request failed; try again or contact support.”). Do not expose API details or credentials.
- **Empty first_signing_url** — When the orchestrator succeeds but returns an empty `first_signing_url` (GetAccessLink failure case), still show success and redirect to deal detail; do not open a new window. Optionally include a message that the signing link could not be retrieved and the user can check the transaction or contact support.
- **Out of scope:** Signature transactions dashboard (Plan 8), Related signature transactions table on Deal View (Plan 9). This plan only replaces the stub and wires the button.

---

## 2. Current State

- **URL:** `POST /deals/<pk>/documents/send-for-signature/` — name `deals:deal_send_for_signature_stub`.
- **View:** `deal_send_for_signature_stub(request, pk)` in `apps/deals/views.py` — only redirects to deal detail with `messages.info(..., "SIGNiX integration will be available in a future release.")`.
- **Template:** `templates/deals/deal_detail.html` — Inside the `{% if document_set %}` block, a form POSTs to the stub URL; button label “Send for Signature”. The button is shown whenever a document set exists (no check yet for SignixConfig or validation).
- **Deal detail context:** Built by `_deal_detail_context(deal, document_set, can_generate)`; includes `cannot_generate_reason` when Generate Documents is disabled. No “can send for signature” or “cannot send reason” yet.

---

## 3. View Behavior

**Rename and replace the stub.** Use a single view that handles POST and delegates to the orchestrator.

**Signature / name:** `deal_send_for_signature(request, pk)` — URL name can remain `deal_send_for_signature_stub` for backward compatibility (same action URL) or be renamed to `deal_send_for_signature`; update the template to use the chosen name.

**Behavior:**

1. **GET or non-POST:** Redirect to `deals:deal_detail` with `pk`.
2. **POST:**
   - Load **deal** (with `select_related` / `prefetch_related` as needed for document_set and signers).
   - Get **document_set** = `deal.document_sets.first()`. If no document set, set `messages.error(request, "No document set to send.")` and redirect to deal detail.
   - Call **`submit_document_set_for_signature(deal, document_set)`** (Plan 6).
   - **On success:** `(signature_transaction, first_signing_url)` is returned. Set a success message (e.g. “Documents sent for signature.”). Store `first_signing_url` for the “open in new window” step (see Section 4). Redirect to deal detail (or to the opener page if using the alternative).
   - **On SignixValidationError:** Do not call SIGNiX. Show the validation errors (e.g. `messages.error(request, exception.errors[0])` or join with “; ”). Re-render deal detail with the same context so the user stays on the page and sees the message.
   - **On SignixApiError:** Show a generic user-facing message (e.g. “SIGNiX request failed; try again or contact support.”). Redirect to deal detail or re-render with error. (Orchestrator already logs the exception.) Optionally include the SIGNiX error message in the flash (e.g. in parentheses) for debugging.
   - **Empty first_signing_url:** If success but `first_signing_url` is empty, optionally add a message (e.g. “Transaction created; signing link could not be retrieved. You can check the transaction or contact support.”). Do not store a URL to open; redirect to deal detail without opening a window.

**Location:** `apps/deals/views.py`. Import orchestrator and exceptions from `apps.deals.signix` (or the module where Plan 6 lives).

---

## 4. Opening the Signing URL in a New Window

Two approaches; choose one for implementation.

**Option A — Session + script on deal detail (recommended; implemented)**

- On success (and when `first_signing_url` is non-empty), store the URL in the session, e.g. `request.session['signix_open_signing_url'] = first_signing_url`, then redirect to deal detail with a success message.
- Deal detail view (GET) pops `signix_open_signing_url` from session, passes it to the template as `open_signing_url`, and clears the key. The template runs a script that opens the URL in a new window (`window.open(..., '_blank', 'noopener,noreferrer')`).
- **Pros:** No extra URL or view; user lands back on deal detail and a new tab opens automatically. **Cons:** Requires deal detail view to read session and clear key; template needs a small script block.

**Option B — Dedicated “Sign in new window” page**

- On success, redirect to a new URL, e.g. `/deals/<pk>/documents/sign-in-new-window/`, with the URL stored in session (or a signed/one-time token in the query string). That view renders a minimal page: “Opening signing window… You can close this tab and return to the deal.” and a script that opens the URL in a new window and then redirects the current tab to deal detail.
- **Pros:** Clear UX for “opener” behavior; no change to deal detail template. **Cons:** Extra URL and view; user sees an intermediate page briefly.

**Decision:** Plan recommends **Option A** for fewer moving parts; implement Option B if the team prefers a dedicated opener page. Document the choice in Section 8.

---

## 5. Button Visibility and “Cannot Send” Reason

- **When to show the button:** Only when a **document set exists** (current behavior already restricts the button to `{% if document_set %}`). Within that, **enable** the button only when submit preconditions would pass; otherwise **disable** it and show a reason.
- **How to compute:** In the **deal detail view** (and any other view that renders the deal detail template with the Documents section), when `document_set` is not None, call **`validate_submit_preconditions(deal, document_set)`** in a try/except. If it **raises** `SignixValidationError`, set `can_send_for_signature = False` and `cannot_send_for_signature_reason = exception.errors[0]` (or join `exception.errors` with “; ” for a longer message). If it **does not raise**, set `can_send_for_signature = True` and `cannot_send_for_signature_reason = None`.
- **Template:** Pass `can_send_for_signature` and `cannot_send_for_signature_reason` in the deal detail context. For the Send for Signature button: if `can_send_for_signature` is False, add `disabled` and e.g. `title="{{ cannot_send_for_signature_reason }}"`. Optionally show the reason inline (e.g. a small muted span next to the button when disabled). When there is no document set, the button is not shown (current behavior).
- **SignixConfig missing:** If `get_signix_config()` creates a default row with empty submitter email, `validate_submit_preconditions` will raise with an error like “SIGNiX configuration missing submitter email” (or similar per Plan 5). So no separate “config missing” check is required if validation covers it.
- **Initial version:** Do **not** disable the button based on how many SignatureTransactions already exist for this document set (Design 7.1). Multiple transactions can be created for testing.

---

## 6. Implementation Order (Checklist)

### Batch 1 — View and response (steps 1–4)

1. **Replace the stub view**
   - Rename or replace `deal_send_for_signature_stub` with `deal_send_for_signature`. Update `apps/deals/urls.py`: keep URL path `/deals/<int:pk>/documents/send-for-signature/`; set `name='deal_send_for_signature'` (or keep `deal_send_for_signature_stub` for backward compatibility; plan uses `deal_send_for_signature` in template going forward).
   - Implement POST logic: load deal and document_set; if no document_set, error and redirect. Call `submit_document_set_for_signature(deal, document_set)`. On success: set success message, store first_signing_url for opener (Section 4), redirect to deal detail. On SignixValidationError: add error message(s) to messages, re-render deal detail with context. On SignixApiError: add generic error message, redirect to deal detail (or re-render). When first_signing_url is empty, do not store URL; optionally add info message about link not retrieved.

2. **Deal detail context for “can send”**
   - In `deal_detail` (and in any view that renders deal detail after an error, e.g. after SignixValidationError), when `document_set` is not None, call `validate_submit_preconditions(deal, document_set)` in try/except. Add `can_send_for_signature` and `cannot_send_for_signature_reason` to `_deal_detail_context` (or compute in the view and pass). When document_set is None, set `can_send_for_signature = False` and `cannot_send_for_signature_reason = None` (button not shown anyway).

3. **Session and opener (Option A)**
   - After successful submit with non-empty first_signing_url, set `request.session['signix_open_signing_url'] = first_signing_url`, then redirect to deal detail. In the **deal detail view** (GET), if `request.session.get('signix_open_signing_url')` is set, add it to context as `open_signing_url` and remove the key from the session (so the script runs once). Ensure the redirect after POST goes to deal detail so the next GET is the deal detail view.

4. **Verification (Batch 1)**
   - Manual or test: POST to send-for-signature with a valid deal/document_set (mocked SIGNiX in tests); assert redirect to deal detail, success message, and session set then cleared. With validation failure, assert re-render with error message. With SignixApiError (mocked), assert generic message and redirect.

### Batch 2 — Template and button (steps 5–8)

5. **Update deal detail template**
   - Change the form action from `deal_send_for_signature_stub` to `deal_send_for_signature` (if URL name was changed).
   - Add `{% if open_signing_url %}` block: script that opens `open_signing_url` in a new window (`window.open(..., '_blank', 'noopener,noreferrer')`) and does not navigate the current page. Place at end of content block or in a block that runs after load.

6. **Button disable and reason**
   - On the Send for Signature button: when `can_send_for_signature` is False, add `disabled` and `title="{{ cannot_send_for_signature_reason }}"`. Optionally show `cannot_send_for_signature_reason` as a muted span when disabled. Ensure the button is only rendered when `document_set` exists (unchanged).

7. **Success message when URL empty**
   - When orchestrator succeeds but first_signing_url is empty, ensure the success message or an info message tells the user the transaction was created but the signing link could not be retrieved (optional wording per Design).

8. **Verification (Batch 2)**
   - With valid preconditions, submit and confirm a new tab opens with the signing URL and deal detail stays in place. With invalid preconditions (e.g. no submitter email), confirm button is disabled and reason is visible. With empty first_signing_url (mock), confirm no new window opens and success message is shown.

### Batch 3 — Tests and cleanup (steps 9–10)

9. **Tests**
   - View tests: (1) POST with no document set → error, redirect. (2) POST with valid deal/document_set (mock orchestrator success) → redirect to deal detail, success message, session has then clears open_signing_url. (3) POST with validation failure (mock SignixValidationError) → re-render deal detail with error message, no redirect. (4) POST with SignixApiError → generic message, redirect to deal detail. (5) GET send-for-signature → redirect to deal detail. (6) Deal detail context: when document_set exists and validation passes, can_send_for_signature True; when validation fails, can_send_for_signature False and reason set.
   - Optional: integration test with real orchestrator mocked (Plan 6) to assert full flow.

10. **Cleanup**
    - Remove or update any references to “stub” in comments or docstrings. Ensure PLAN-ADD-DOCUMENT-SETS or DESIGN-DOCS is updated to state that Send for Signature is implemented (no longer a stub).

---

## 6a. Implementation Batches and Verification

**Batch 1 — View and response**

**Includes:** Replace stub with `deal_send_for_signature`, call orchestrator, handle SignixValidationError and SignixApiError, store first_signing_url in session and redirect to deal detail, deal detail context extended with can_send_for_signature and cannot_send_for_signature_reason, session read/clear for open_signing_url.

**How to test after Batch 1:**

1. POST to send-for-signature with valid deal/document_set; expect redirect to deal detail, success message, and (if first_signing_url present) session key set then cleared when deal detail loads.
2. POST with invalid data (e.g. wrong deal or missing submitter email); expect error message and re-render or redirect with message.
3. Deal detail GET with document_set and valid preconditions: context has can_send_for_signature True. With invalid preconditions: can_send_for_signature False and reason set.

**Implementation notes (Batch 1):** Replaced stub with `deal_send_for_signature`. View loads deal with same prefetch as deal_detail. No document_set → messages.error and redirect. On success: store first_signing_url in session when non-empty, redirect; when empty add messages.info. SignixValidationError → re-render deal detail with _deal_detail_context(can_send_for_signature=False, reason). SignixApiError → generic message, redirect. Option A: deal_detail GET pops signix_open_signing_url from session, passes open_signing_url to context; template script opens URL in new window. _deal_detail_context computes can_send via validate_submit_preconditions when document_set exists (or accepts overrides). URL name deal_send_for_signature; template form action, button disabled/title, opener script. Tests: test_send_for_signature_views (GET redirects, POST no document set, deal detail can_send).

**Completed (Batch 1):** View, context, session opener, template updates, 3 view tests. All 60 deals tests pass.

**Manual testing (after Batch 1):** Deal with no document set → POST yields "No document set to send." and redirect. Deal with document set and valid config → Send for Signature → redirect, success message, new tab opens with signing URL. Button disabled when preconditions fail (e.g. no submitter email); tooltip shows reason.

**Batch 2 — Template and button**

**Includes:** Template form action (URL name), script to open signing URL when open_signing_url is in context, button disabled and title when can_send_for_signature is False, optional message when first_signing_url is empty.

**How to test after Batch 2:**

1. Submit successfully; confirm new tab opens with signing URL and deal detail remains.
2. Load deal detail with disabled Send button (e.g. no submitter email); confirm button is disabled and tooltip/message shows reason.

**Batch 3 — Tests and cleanup**

**Includes:** View tests for all branches, optional integration test, stub references removed.

**How to test after Batch 3:**

1. All tests pass. Manual smoke test: enable Send, submit, sign in new tab, return to deal.

**Completed (Batch 3):** View tests added in `test_send_for_signature_views.py`: (1) POST no document set → error, redirect. (2) POST with valid deal/document_set (mock orchestrator success) → redirect, success message, session `signix_open_signing_url` set then cleared on deal detail GET. (3) POST with mock SignixValidationError → re-render deal detail (200) with error message. (4) POST with mock SignixApiError → redirect to deal detail with generic message. (5) GET send-for-signature → redirect (existing). (6) Deal detail context: without document set → can_send False; with document set and valid config → can_send True; with document set and unresolved signer → can_send False and reason set. Cleanup: PLAN-ADD-DOCUMENT-SETS updated to state Send for Signature is implemented (Plan 7); no stub references left in code. All 8 Plan 7 tests pass.

---

## 7. File Summary

| Item | Value |
|------|--------|
| View | `deal_send_for_signature(request, pk)` in `apps/deals/views.py` |
| URL | `POST /deals/<pk>/documents/send-for-signature/` — name `deal_send_for_signature` (or keep stub name) |
| Template | `templates/deals/deal_detail.html` — form action, button disabled/reason, optional open_signing_url script |
| Context (deal detail) | `can_send_for_signature`, `cannot_send_for_signature_reason`, `open_signing_url` (when returning from successful submit) |
| Session key | `signix_open_signing_url` (Option A) — set after success, read and cleared by deal detail GET |
| Imports | `submit_document_set_for_signature`, `SignixValidationError`, `SignixApiError` from `apps.deals.signix` (or Plan 6 module) |

---

## 8. Open Issues / Implementation Decisions

- **URL name:** **Decided:** Prefer renaming to `deal_send_for_signature` and updating the template; no backward compatibility requirement for the old name. If the project prefers to keep `deal_send_for_signature_stub` to avoid changing the template, that is acceptable.

- **Opening the URL (Option A vs B):** **Decided:** Recommend **Option A** (session + script on deal detail). Implement Option B (dedicated “Sign in new window” page) only if the team prefers a separate opener page. Document the choice in code or in this plan after implementation.

- **Re-render vs redirect on SignixValidationError:** **Decided:** Re-render deal detail with error message so the user sees the form and the validation errors without losing context. Use the same context as normal deal detail (including can_send_for_signature and cannot_send_for_signature_reason). Ensure document_set and deal are reloaded so the view has the same prefetches as the normal deal detail view.

- **Re-render vs redirect on SignixApiError:** **Decided:** Redirect to deal detail with a generic error message (e.g. `messages.error`). The orchestrator already logs the exception; no need to re-render.

- **Empty first_signing_url message:** Optional. If the orchestrator returns success with empty first_signing_url, add an info message (e.g. “Transaction created; signing link could not be retrieved. You can check the transaction or contact support.”). Implementation choice.

- **Button reason length:** When multiple validation errors exist, use the first error for the button tooltip to keep the UI clean; optionally show all errors in the messages after a failed POST. No need to show a long list in the disabled button title.

- **Deal detail prefetch for validation:** `validate_submit_preconditions` needs document_set with instances, versions, and document_set_template; deal with signer_order/signer_authentication and lease_officer/contacts. **Decided:** Both `deal_detail` and `deal_send_for_signature` should load deal with the same prefetch (e.g. `prefetch_related('document_sets__instances__versions', 'document_sets__document_set_template')` and `select_related('lease_officer', 'deal_type')`) so that computing can_send_for_signature and re-rendering after validation errors do not trigger N+1 queries. Add `document_sets__document_set_template` if not already present.

- **Re-render context after SignixValidationError:** When the send view re-renders deal detail after a validation error, it must pass the **full** deal detail context (deal, document_set, can_generate, cannot_generate_reason, can_send_for_signature, cannot_send_for_signature_reason). **Decided:** Extend `_deal_detail_context` to accept optional `can_send_for_signature` and `cannot_send_for_signature_reason` (or compute them inside the helper when document_set is not None). Then `deal_detail` always calls the helper with deal, document_set, can_generate and the helper computes can_send when document_set exists; `deal_send_for_signature` when re-rendering calls the same helper with `can_send_for_signature=False` and `cannot_send_for_signature_reason` set from the exception. That way both views stay in sync.

- **Authentication:** **Decided:** Keep `@login_required` on the send-for-signature view (same as the stub and other deal views). No change to permission model in this plan.

---

*End of plan. Proceed to implementation only after review. Next: [80-PLAN-SIGNiX-DASHBOARD.md](80-PLAN-SIGNiX-DASHBOARD.md) (Plan 8).*

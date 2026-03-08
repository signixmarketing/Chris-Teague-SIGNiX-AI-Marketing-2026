# Plan: SIGNiX Push Listener (Dashboard/Sync Plan 2)

This plan implements the **push notification listener** that SIGNiX calls when events occur (Send, partyComplete, complete, suspend, cancel, expire). It updates `SignatureTransaction` status and per-signer progress via two helpers, returns 200 OK quickly, and for **action=complete** triggers the download flow asynchronously (Plan 5 implements the real download; this plan wires a stub).

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 4 (Push Notification Listener), Section 4.2 (record event), Section 4.4 (helpers), Section 7.5 (SignatureTransactionEvent); Section 3.1 (status values), Section 3.4 (per-signer progress). ../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md — push request format, action→status mapping, idempotency.

**Prerequisites:** Plan 1 (PLAN-SIGNiX-SYNC-MODEL) is implemented: SignatureTransaction has signer_count, signers_completed_refids, signers_completed_count, **status_last_updated**, and STATUS_EXPIRED; **SignatureTransactionEvent** model exists; migrations applied. **For real end-to-end testing with SIGNiX callbacks, PLAN-NGROK must also be active and both Django and ngrok must be running in parallel** so SIGNiX can reach the callback URL emitted by Plan 3. If Plan 3 derives the callback from the request host behind ngrok, Django must trust the forwarded HTTPS scheme so the generated URL is `https://...`, not `http://...`.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **GET /signix/push/** — Unauthenticated endpoint that SIGNiX calls with query parameters (action, id, extid; optional pid, refid, ts). Parse params, look up transaction via **get_signature_transaction_for_push**, apply updates via **apply_push_action**, save, **create a SignatureTransactionEvent for this push** (event_type from action, occurred_at from ts, refid/pid when present), return HTTP 200 with body `"OK"`. If transaction not found, log and still return 200 OK. **The system listens to push notifications and updates the number of signers who have completed whenever SIGNiX notifies it** (on partyComplete or complete), so the dashboard Signers column (e.g. 1/2, 2/2) stays in sync. In this codebase, SubmitDocument emits the callback URL as `/signix/push` (no trailing slash); Django’s listener route remains `/signix/push/`, and live verification showed SIGNiX successfully followed Django’s redirect from the bare path to the slash form.
- **Helpers** — **get_signature_transaction_for_push(signix_document_set_id=None, transaction_id=None)** returns the SignatureTransaction or None. **apply_push_action(transaction, action, refid=None, pid=None, ts=None)** applies action→status mapping, idempotency (no overwrite of terminal states), **status_last_updated** and completed_at for complete, and per-signer progress for partyComplete/complete. Whenever the helper mutates the transaction (status, completed_at, or signer progress), it sets **status_last_updated** to the event time (ts or now). **For event creation:** use a small helper **push_action_to_event_type(action)** that returns the event_type string (Send→send, partyComplete→party_complete, etc.) so the view does not duplicate the mapping; use **get_event_time_for_push(ts)** (parse ts or return timezone.now()) so the view and apply_push_action share the same event time for consistent occurred_at. All helpers in `apps.deals.signix` (or a dedicated push module) so the view stays thin and logic is testable without HTTP.
- **Async trigger for complete** — After responding 200 OK, for **action=complete** call **download_signed_documents_on_complete(transaction)** asynchronously (e.g. threading.Thread or fire-and-forget). This plan implements a **stub** that logs and returns; Plan 5 replaces it with the real download flow.
- **CSRF** — Exempt the push view from CSRF so SIGNiX’s GET requests are not rejected.
- **Out of scope this plan:** SubmitDocument with push URL (Plan 3), dashboard Signers column (Plan 4), real DownloadDocument/ConfirmDownload and storage of audit trail and certificate on the transaction (Plan 5). No push request validation (secret/token) unless SIGNiX docs require it.

---

## 2. Endpoint and Behavior

### 2.1 URL and method

- **URL:** `/signix/push/` (trailing slash; register at project root so full URL is e.g. `https://your-domain.com/signix/push/`).
- **Callback URL note:** Plan 3’s SubmitDocument payload uses the no-trailing-slash form `https://your-domain.com/signix/push`. The listener route in Django can still remain `/signix/push/`; in live verification, requests to the bare path were redirected to the slash form and processed successfully.
- **Method:** GET only. All payload in query string per SIGNiX.

### 2.2 Query parameters

| Parameter | Required | Meaning |
|-----------|----------|---------|
| **action** | Yes | Event type: Send, partyComplete, complete, suspend, cancel, expire (and others per SIGNiX; this plan handles the listed ones). |
| **id** | Yes | SIGNiX Document Set ID; map to `SignatureTransaction.signix_document_set_id`. |
| **extid** | Yes | Client Transaction ID; map to `SignatureTransaction.transaction_id`. |
| **pid** | No | Party ordinal (e.g. P01, P02); used for partyComplete when refid absent. |
| **refid** | No | RefId of the party; prefer over pid for partyComplete. |
| **ts** | No | Event time; use for completed_at when action=complete (format per SIGNiX; parse or use now() if missing/invalid). |

### 2.3 Response

- **Success:** HTTP 200 with response body exactly the string `"OK"` (no extra whitespace or JSON). Content-Type can be text/plain or omitted.
- **Unknown id/extid:** Log a warning (include id and extid); still return 200 OK with body "OK".
- **Any exception:** Log and still return 200 OK with body "OK" so SIGNiX does not retry unnecessarily (optional: in a later plan you may return 5xx for true server errors; design prefers always 200 for this endpoint).

### 2.4 Action → status mapping (in apply_push_action)

| action | New status | Notes |
|--------|------------|-------|
| Send | (no change or leave Submitted) | Optionally leave as-is. |
| partyComplete | In Progress | After updating signers_completed_refids. |
| complete | Complete | Set completed_at and **status_last_updated** (from ts or now). Set signers_completed_count = signer_count if not already equal. |
| suspend | Suspended | |
| cancel | Cancelled | |
| expire | Expired | Use STATUS_EXPIRED. |
| (other) | (no change) | Log unknown action; do not change status. |

**Terminal states:** Complete, Suspended, Cancelled, Expired. If the transaction is already in a terminal state, do **not** overwrite with a different status (idempotent).

### 2.5 Per-signer progress (in apply_push_action)

- **partyComplete:** Let key = refid if present, else pid. If key is not in signers_completed_refids, append it and set signers_completed_count = len(signers_completed_refids). Then set status to In Progress if not terminal.
- **complete:** Set signers_completed_count = signer_count if signer_count is not None and signers_completed_count != signer_count.

### 2.6 completed_at and status_last_updated

- When action is **complete**, set transaction.completed_at and **transaction.status_last_updated** from **ts** if present: parse with `datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")`; on ValueError or missing ts use `timezone.now()`. If `USE_TZ` is True, ensure the value is timezone-aware (e.g. `timezone.make_aware(parsed)` if parsed is naive, or use `timezone.now()` as fallback).
- For **every** action where apply_push_action mutates the transaction (status change, signer progress, or completed_at), set **status_last_updated** to the same event time (parsed ts or timezone.now()). This supports the dashboard "Status updated" column (when the most recent signer completed, when the transaction was completed).

---

## 3. Helpers (implementation detail)

### 3.1 get_signature_transaction_for_push(signix_document_set_id=None, transaction_id=None)

- **Returns:** SignatureTransaction or None.
- **Logic:** If both signix_document_set_id and transaction_id are None or empty string, return None immediately (no query). Otherwise try lookup by signix_document_set_id (if provided and non-empty) and/or transaction_id (if provided and non-empty). Use a single query with Q(signix_document_set_id=id) | Q(transaction_id=extid) when both provided, or one filter otherwise; return .first() or None.
- **Location:** `apps.deals.signix`.

### 3.2 apply_push_action(transaction, action, refid=None, pid=None, ts=None)

- **Returns:** None. Mutates **transaction** in memory (status, completed_at, **status_last_updated**, signers_completed_refids, signers_completed_count).
- **Logic:** Resolve **event_time** via **get_event_time_for_push(ts)** (see 3.3) at the start so the same time is used for status_last_updated and completed_at. Then:
  - If transaction.status is terminal (Complete, Suspended, Cancelled, Expired), return without changing status (idempotent).
  - If action is not one of Send, partyComplete, complete, suspend, cancel, expire: do not change status; log at debug (e.g. "Unknown push action: %s") and return.
  - Map action to new_status per table above; for Send leave status unchanged.
  - For partyComplete: set key = refid or pid; if key and key not in signers_completed_refids, append key and set signers_completed_count = len(signers_completed_refids); set status to In Progress if not terminal. Set **status_last_updated** = event_time whenever you mutate (status or signer progress).
  - For complete: set completed_at and **status_last_updated** = event_time. Set signers_completed_count = signer_count if signer_count is not None; set status = Complete.
  - For suspend/cancel/expire: set status = Suspended/Cancelled/Expired; set **status_last_updated** = event_time.
- **Location:** `apps.deals.signix`.

### 3.3 push_action_to_event_type(action) and get_event_time_for_push(ts)

- **push_action_to_event_type(action) -> str** — Returns the event_type for SignatureTransactionEvent: Send→"send", partyComplete→"party_complete", complete→"complete", suspend→"suspend", cancel→"cancel", expire→"expire". For unknown action, return a safe value (e.g. "unknown") or the lowercased action. Keeps the view from duplicating the mapping; testable in isolation.
- **get_event_time_for_push(ts=None) -> datetime** — Parses ts with strptime `%Y-%m-%dT%H:%M:%S`; on ValueError or missing ts returns timezone.now(). If USE_TZ is True, ensures the result is timezone-aware. Use in both apply_push_action (for status_last_updated and completed_at) and in the view when creating the event so occurred_at is consistent.
- **Location:** `apps.deals.signix`.

### 3.4 download_signed_documents_on_complete(transaction) — stub

- **Signature:** Same as Plan 5 (transaction only). This plan: implement a stub that logs “download_signed_documents_on_complete called (stub)” and returns. Plan 5 replaces it with the full implementation (DownloadDocument, map to instances, create Final versions, store audit trail and certificate on the transaction, ConfirmDownload).
- **Invocation:** From the push view, after sending the 200 response, start a thread (or use a fire-and-forget helper) that calls this function so the GET handler returns quickly.

---

## 4. CSRF exemption

- The push view must be exempt from CSRF. If the project uses Django’s CsrfViewMiddleware and does not exempt GET by default, decorate the view with `@csrf_exempt` (from django.views.decorators.csrf import csrf_exempt). GET requests are often not CSRF-checked; confirm and exempt this view so SIGNiX is not blocked.

---

## 5. Implementation Order (Checklist)

### Batch 1 — Helpers and view (steps 1–5)

1. **Add get_signature_transaction_for_push**
   - In `apps/deals/signix.py`, implement `get_signature_transaction_for_push(signix_document_set_id=None, transaction_id=None)`. Use SignatureTransaction.objects.filter(...).first() with Q on signix_document_set_id and/or transaction_id; return None if both args are empty or no match.

2. **Add apply_push_action**
   - In `apps/deals/signix.py`, implement `apply_push_action(transaction, action, refid=None, pid=None, ts=None)`. Use **get_event_time_for_push(ts)** at the start for event_time. Import SignatureTransaction status constants and use them for terminal check and new status. Mutate transaction in place; do not call save() inside the helper.

2b. **Add push_action_to_event_type and get_event_time_for_push**
   - In `apps/deals/signix.py`, implement **push_action_to_event_type(action)** (returns event_type string per Section 3.3) and **get_event_time_for_push(ts)** (parses ts or returns timezone.now(); timezone-aware when USE_TZ). Use get_event_time_for_push in apply_push_action and in the view when creating the event.

3. **Add download_signed_documents_on_complete stub**
   - In `apps/deals/signix.py`, implement `download_signed_documents_on_complete(transaction)` that logs at info or debug and returns. Plan 5 will replace this.

4. **Add push view**
   - Create a view function (e.g. in `apps/deals/views.py` or `apps/deals/signix_views.py`) that: (a) reads request.GET for action, id, extid, pid, refid, ts; (b) if action, id, or extid is missing or empty, log a warning (e.g. "Push request missing required param") and return HttpResponse("OK", status=200); (c) call get_signature_transaction_for_push(id, extid); (d) if transaction is None, log warning (include id, extid) and return HttpResponse("OK", status=200); (e) else call apply_push_action(transaction, action, refid=refid, pid=pid, ts=ts); (f) save with transaction.save(update_fields=[...]); (g) **create SignatureTransactionEvent**: event_type = **push_action_to_event_type(action)**; occurred_at = **get_event_time_for_push(ts)**; set refid/pid from request when present; event.signature_transaction = transaction; event.save(); (h) if action == "complete", start a **daemon** thread: `thread = threading.Thread(target=download_signed_documents_on_complete, args=(transaction,), daemon=True); thread.start()`; (i) return HttpResponse("OK", status=200, content_type="text/plain").

5. **Wire URL and CSRF exempt**
   - In `config/urls.py`, add path `signix/push/`, view (with @csrf_exempt if needed). Ensure the view is not behind login_required.
  - **Codebase note:** In this repo, the listener should live at the **project root URLconf** (`config/urls.py`), not `apps.deals.urls`, because the public callback path is `/signix/push` / `/signix/push/` rather than `/deals/...`.

### Batch 2 — Async trigger and verification (steps 6–8)

6. **Ensure async does not block**
   - Use `threading.Thread(target=download_signed_documents_on_complete, args=(transaction,), daemon=True)` and call `thread.start()`. Do not join the thread; return 200 immediately. Daemon=True ensures the process can exit without waiting for the stub (and later for Plan 5’s download).

7. **Verification (Batch 1–2)**
   - Run `python manage.py check`. **Primary:** Run unit tests (Section 6): `python manage.py test apps.deals.tests.test_push_listener` — all pass. Treat this as sufficient for Batch 1–2 verification.
   - **No schema change in Batch 1:** No migration should be required for the helper/view/URL work in this batch; `python manage.py migrate` should report no new migrations to apply.
   - **Optional (manual):** Create a SignatureTransaction in shell, then GET /signix/push/?action=complete&id=<signix_document_set_id>&extid=<transaction_id>; assert 200 and body "OK"; reload transaction and assert status is Complete and completed_at is set.

8. **Idempotency check**
   - Same transaction, send the same complete push again; reload transaction and assert status is still Complete (not overwritten). Covered by unit test **test_push_view_complete_idempotent** (Section 6).

---

## 5a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps and tests listed.

### Batch 1 — Helpers and view

**Includes:** get_signature_transaction_for_push, apply_push_action, download_signed_documents_on_complete (stub), push view, URL routing, CSRF exempt.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — no new migrations to apply for this batch.
3. **Unit tests (primary):** `python manage.py test apps.deals.tests.test_push_listener` — all tests pass. This is sufficient to verify Batch 1 logic locally; ngrok is not required for these tests.
4. **Real callback verification requirement:** If you want to verify the listener with **actual SIGNiX push notifications**, keep **`python manage.py runserver` and ngrok running in parallel** and ensure SIGNiX is configured to call the current ngrok URL for `/signix/push/`. Without the active tunnel, the application will not receive the push notifications.
5. **Optional — local 200 and body:** From browser or curl: `GET /signix/push/?action=complete&id=unknown&extid=unknown`. Expect HTTP 200 and response body exactly "OK". Check logs for warning about unknown id/extid.
6. **Optional — local known transaction:** In Django shell create a SignatureTransaction (e.g. deal, document_set, signix_document_set_id="DS-PUSH-1", transaction_id="tx-001", status=STATUS_SUBMITTED). Then request `GET /signix/push/?action=complete&id=DS-PUSH-1&extid=tx-001`. Expect 200 OK. Reload the transaction; assert status == STATUS_COMPLETE, completed_at is not None, **status_last_updated is not None**.
7. **Optional — local partyComplete:** Create a transaction with signer_count=2, signers_completed_refids=[], signers_completed_count=0. GET with action=partyComplete&id=...&extid=...&refid=P01. Reload; assert signers_completed_refids contains "P01", signers_completed_count == 1, status == In Progress. Send again with same refid=P01; assert count still 1 (idempotent).
8. **Optional — local terminal not overwritten:** Transaction in Complete. Send GET with action=partyComplete&id=...&extid=.... Reload; assert status still Complete.

### Batch 2 — Async and edge cases

**Includes:** Async invocation of download_signed_documents_on_complete (thread or fire-and-forget); any logging improvements; optional ts parsing for completed_at.

**How to test after Batch 2:**

1. **Async thread started:** Prefer a unit test that patches `apps.deals.views.threading.Thread` and asserts it was constructed with `target=download_signed_documents_on_complete`, `args=(transaction,)`, and `daemon=True`, then that `start()` was called exactly once. This is a stronger Batch 2 verification than relying only on the stub log line.
2. **Duplicate complete:** Send two complete pushes for the same transaction; both return 200; transaction remains Complete; no exception.
3. **Expire:** GET with action=expire&id=...&extid=... for a Submitted transaction; assert status becomes Expired.
4. **Real SIGNiX verification:** If you verify with actual SIGNiX callbacks rather than direct local GETs, Django and ngrok must both be running. Submit or configure the callback against the active ngrok domain and confirm requests appear in ngrok before diagnosing listener logic.

Batch 2 is complete when the above pass.

---

## 6. Unit Tests (add to apps.deals.tests)

Create **apps/deals/tests/test_push_listener.py** with the following. Use the same test setup as other deals tests (Deal, DocumentSet, User; get_signix_config() if needed). Create SignatureTransaction instances with signix_document_set_id and transaction_id for lookup tests.

### 6.1 get_signature_transaction_for_push

- **test_lookup_by_signix_document_set_id** — Create a transaction with signix_document_set_id="DS-A", transaction_id="ext-1". Call get_signature_transaction_for_push(signix_document_set_id="DS-A", transaction_id=None). Assert result is that transaction.
- **test_lookup_by_transaction_id** — Same transaction; call get_signature_transaction_for_push(signix_document_set_id=None, transaction_id="ext-1"). Assert result is that transaction.
- **test_lookup_returns_none_when_not_found** — get_signature_transaction_for_push(signix_document_set_id="nonexistent", transaction_id="none"). Assert result is None.
- **test_lookup_returns_none_when_both_empty** — get_signature_transaction_for_push(None, None) or ("", ""). Assert result is None (or first() returns None if no generic match).

### 6.2 apply_push_action

- **test_complete_sets_status_and_completed_at** — Transaction in Submitted. apply_push_action(tx, "complete", ts=None). Assert tx.status == STATUS_COMPLETE, tx.completed_at is not None, **tx.status_last_updated is not None**. (Do not save; assert in-memory.)
- **test_complete_sets_signers_completed_count_to_signer_count** — Transaction with signer_count=2, signers_completed_count=0. apply_push_action(tx, "complete"). Assert signers_completed_count == 2.
- **test_party_complete_appends_refid_and_sets_in_progress** — Transaction Submitted, signers_completed_refids=[], signers_completed_count=0. apply_push_action(tx, "partyComplete", refid="P01"). Assert "P01" in signers_completed_refids, signers_completed_count == 1, status == In Progress, **status_last_updated is not None**.
- **test_party_complete_idempotent** — Same transaction, signers_completed_refids=["P01"], signers_completed_count=1. apply_push_action(tx, "partyComplete", refid="P01"). Assert signers_completed_refids == ["P01"], signers_completed_count == 1 (no duplicate).
- **test_terminal_not_overwritten** — Transaction status = Complete. apply_push_action(tx, "partyComplete", refid="P02"). Assert tx.status still Complete.
- **test_expire_sets_expired_status** — Transaction Submitted. apply_push_action(tx, "expire"). Assert tx.status == STATUS_EXPIRED, **tx.status_last_updated is not None**.
- **test_suspend_sets_suspended** — Transaction Submitted. apply_push_action(tx, "suspend"). Assert tx.status == STATUS_SUSPENDED, **tx.status_last_updated is not None**.
- **test_cancel_sets_cancelled** — Transaction Submitted. apply_push_action(tx, "cancel"). Assert tx.status == STATUS_CANCELLED, **tx.status_last_updated is not None**.

### 6.3 push_action_to_event_type and get_event_time_for_push

- **test_push_action_to_event_type_send** — push_action_to_event_type("Send") returns "send".
- **test_push_action_to_event_type_party_complete** — push_action_to_event_type("partyComplete") returns "party_complete".
- **test_push_action_to_event_type_complete** — push_action_to_event_type("complete") returns "complete".
- **test_push_action_to_event_type_suspend_cancel_expire** — push_action_to_event_type("suspend") returns "suspend"; same for "cancel", "expire".
- **test_get_event_time_for_push_valid_ts** — get_event_time_for_push("2025-03-15T14:30:00") returns a timezone-aware datetime matching that instant (or naive if USE_TZ=False). Assert year/month/day/hour/minute/second as expected.
- **test_get_event_time_for_push_invalid_ts** — get_event_time_for_push("not-a-date") or get_event_time_for_push("") returns timezone.now() (or equivalent; assert a datetime is returned and no exception).
- **test_get_event_time_for_push_none** — get_event_time_for_push(None) returns timezone.now() (or equivalent).

### 6.4 Push view (integration)

- **test_push_view_returns_200_and_ok_body** — Client GET to /signix/push/?action=complete&id=unknown&extid=unknown. Assert response.status_code == 200, response.content == b"OK".
- **test_push_view_updates_transaction_and_returns_200** — Create transaction with signix_document_set_id="DS-V1", transaction_id="ext-v1", status=STATUS_SUBMITTED. Patch `apps.deals.views.threading.Thread`. GET /signix/push/?action=complete&id=DS-V1&extid=ext-v1. Assert response.status_code == 200, response.content == b"OK". Reload transaction; assert status == STATUS_COMPLETE, completed_at is not None, **status_last_updated is not None**. Assert **transaction.events.filter(event_type="complete").exists()** (one event created for this push). Also assert the thread was created with `target=download_signed_documents_on_complete`, `args=(transaction,)`, and `daemon=True`, and that `start()` was called.
- **test_push_view_creates_party_complete_event_with_refid** — Create transaction. GET with action=partyComplete&id=...&extid=...&refid=P01. Assert transaction.events.count() >= 1; one event has event_type="party_complete" and refid="P01".
- **test_push_view_unknown_id_logs_and_returns_200** — Use a logger mock or caplog; GET with unknown id/extid; assert 200 and that a warning was logged.
- **test_push_view_csrf_exempt** — If the test client enforces CSRF, ensure the push view does not require CSRF token for GET (no 403).
- **test_push_view_complete_idempotent** — Create a transaction with signix_document_set_id and transaction_id, status=STATUS_SUBMITTED. GET /signix/push/?action=complete&id=...&extid=... twice. Assert both responses are 200 with body "OK". Reload transaction; assert status is still STATUS_COMPLETE, completed_at and status_last_updated are set, and no duplicate or erroneous state (e.g. events may have two "complete" events from retries; transaction state must remain idempotent).
- **test_push_view_expire_updates_transaction** — Create transaction with signix_document_set_id and transaction_id, status=STATUS_SUBMITTED. GET /signix/push/?action=expire&id=...&extid=.... Assert response is 200 with body "OK". Reload transaction; assert status == STATUS_EXPIRED, **status_last_updated is not None**, and **transaction.events.filter(event_type="expire").exists()**.

---

## 7. File Summary

| Item | Value |
|------|--------|
| App / module | `apps.deals` (signix.py for helpers; views or signix_views for push view) |
| New helpers | get_signature_transaction_for_push, apply_push_action, **push_action_to_event_type**, **get_event_time_for_push**, download_signed_documents_on_complete (stub) in signix.py |
| New view | Push listener view (GET only, returns 200 "OK"; creates SignatureTransactionEvent per push) |
| URL | path("signix/push/", view) in config/urls.py |
| Tests | apps/deals/tests/test_push_listener.py |
| CSRF | @csrf_exempt on push view |

---

## 8. Open Issues / Implementation Decisions

All of the following are **decided** for this plan; implement as specified in the sections above.

- **ts parsing:** Parse ts with strptime and "%Y-%m-%dT%H:%M:%S"; on ValueError or missing ts use timezone.now(). When USE_TZ is True, ensure completed_at is timezone-aware (see Section 2.6 and 3.2).
- **Thread:** Use threading.Thread with daemon=True so the process can exit without waiting for the download stub or Plan 5 implementation.
- **update_fields:** After apply_push_action, call transaction.save(update_fields=["status", "completed_at", "status_last_updated", "signers_completed_refids", "signers_completed_count"]) (Section 5 step 4).
- **Unknown action:** If action is not one of Send, partyComplete, complete, suspend, cancel, expire, do not change status; log at debug and return from apply_push_action (Section 3.2). View still returns 200 OK.
- **Missing action/id/extid:** View validates required params; if any of action, id, or extid is missing or empty, log a warning and return 200 OK without calling get_signature_transaction_for_push. get_signature_transaction_for_push returns None when both id and extid are None or empty (Section 3.1).
- **Stub signature:** download_signed_documents_on_complete(transaction) — single argument only, so Plan 5 can replace the body without changing callers.
- **Event creation:** After saving the transaction, create SignatureTransactionEvent with event_type from action (map: Send→send, partyComplete→party_complete, complete→complete, suspend→suspend, cancel→cancel, expire→expire). Use the same event_time as in apply_push_action (parsed ts or timezone.now()). **Decided:** No dedupe initially; duplicate events on retries are acceptable per DESIGN 7.5. Add dedupe (e.g. unique constraint or skip logic) only if duplicate events later cause UX or reporting issues.

---

## 9. Implementation Notes

- **Terminal check:** In apply_push_action, at the start, if transaction.status in (STATUS_COMPLETE, STATUS_SUSPENDED, STATUS_CANCELLED, STATUS_EXPIRED), return without modifying (idempotent).
- **Unknown action:** Before terminal check, if action not in ("Send", "partyComplete", "complete", "suspend", "cancel", "expire"), log at debug and return without changing the transaction.
- **refid/pid for partyComplete:** Use refid if present and non-empty string, else pid. Normalize to string (e.g. str(pid)) so list membership works. Only append if the chosen key is not already in signers_completed_refids.
- **Stub:** download_signed_documents_on_complete(transaction) logs at info: e.g. logger.info("download_signed_documents_on_complete called (stub), transaction_id=%s", transaction.pk).
- **URL placement:** The design says `/signix/push/`. The project has signix config at `signix/config/`. Adding `signix/push/` at the project root keeps push separate from the config UI and matches the design.
- **Bare-path callback from SIGNiX:** Live verification in this app showed SIGNiX calling `/signix/push` (no trailing slash) when that exact URL was emitted by SubmitDocument. Django redirected that request to `/signix/push/`, and SIGNiX followed it successfully. **Decided:** keep the Django listener at `/signix/push/`, but document that Plan 3 emits `/signix/push` in the SubmitDocument payload.
- **No migration expected for Batch 1:** This batch adds helpers, a view, URL routing, and tests only. If `makemigrations` suggests a schema change, double-check that you did not accidentally modify models while implementing the listener.
- **Missing params in view:** If request.GET has missing or empty action, id, or extid, log a warning (e.g. "Push request missing required parameter") and return HttpResponse("OK", status=200) without calling get_signature_transaction_for_push.

---

## 10. Manual Testing (Details)

Use the following to verify the listener without SIGNiX. Run the dev server (`python manage.py runserver`) and use curl or a browser. For **real** push verification with SIGNiX, also run **ngrok in parallel** and use the active ngrok callback URL; otherwise SIGNiX cannot reach the local app.

**1. Unknown transaction (must return 200 OK)**  
```bash
curl -i "http://127.0.0.1:8000/signix/push/?action=complete&id=unknown-id&extid=unknown-extid"
```
Expect: HTTP 200, body `OK`. Server logs should show a warning about unknown id/extid.

**2. Known transaction — complete**  
In Django shell create a transaction:
```python
from apps.deals.models import SignatureTransaction
deal = Deal.objects.first()
doc_set = deal.document_sets.first()  # or DocumentSet.objects.filter(deal=deal).first()
tx = SignatureTransaction.objects.create(
    deal=deal, document_set=doc_set,
    signix_document_set_id="DS-MANUAL-1", transaction_id="manual-tx-1",
    status=SignatureTransaction.STATUS_SUBMITTED
)
```
Then:
```bash
curl -i "http://127.0.0.1:8000/signix/push/?action=complete&id=DS-MANUAL-1&extid=manual-tx-1"
```
Expect: 200 OK. In shell: `tx.refresh_from_db(); print(tx.status, tx.completed_at, tx.status_last_updated)` → status Complete, completed_at set, status_last_updated set.

**3. Idempotency**  
Send the same complete request again; reload tx and confirm status is still Complete.

**4. partyComplete**  
Create another tx (e.g. signix_document_set_id="DS-MANUAL-2", transaction_id="manual-tx-2") with signer_count=2. Then:
```bash
curl -i "http://127.0.0.1:8000/signix/push/?action=partyComplete&id=DS-MANUAL-2&extid=manual-tx-2&refid=P01"
```
Reload tx: signers_completed_refids should contain "P01", signers_completed_count=1, status In Progress. Call again with same refid=P01; count should remain 1.

**5. Expire**  
For a Submitted tx: `curl -i "http://127.0.0.1:8000/signix/push/?action=expire&id=<id>&extid=<extid>"`. Reload; status should be Expired.

Use your runserver URL (or ngrok URL for production-like testing) in place of `http://127.0.0.1:8000` if different. When testing with SIGNiX itself, prefer the ngrok URL and keep both the tunnel and Django server running for the full test.

---

*End of plan. Proceed to implementation only after review. Next: 30-PLAN-SIGNiX-SUBMIT-PUSH-URL.md (Plan 3).*

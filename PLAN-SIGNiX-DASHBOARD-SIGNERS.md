# Plan: SIGNiX Dashboard — Signers and Status Updated Columns (Dashboard/Sync Plan 4)

This plan adds the **Signers** column (e.g. "0/2", "1/2", "2/2") and the **Status updated** column (when the current status was last updated) to the signature transactions list view and to the Deal View related-transactions table. Status is already driven by the push listener (Plan 2); this plan adds the two new columns and ensures **null-safe** display. **Plan 1’s data migration** sets **status_last_updated = submitted_at** for all existing transactions, so migrated rows have a consistent Status updated value (submit time as the effective “last status update”); the display helper shows "—" only when status_last_updated is null (edge case).

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 3.2 (Dashboard columns), Section 3.4 (get_signers_display), Section 3.3 (status_last_updated). PLAN-SIGNiX-DASHBOARD-SYNC-MASTER.md — Plan 4 deliverables.

**Prerequisites:** Plan 1 (PLAN-SIGNiX-SYNC-MODEL) is implemented: SignatureTransaction has signer_count, signers_completed_count, status_last_updated. Plan 2 (push listener) and Plan 3 (submit with signer_count) populate these fields. No dependency on Plan 5.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **Signers column** — Show **completed / total** signers (e.g. "0/2", "1/2", "2/2"). Use a single helper **get_signers_display(transaction) -> str** so formatting and null-handling live in one place. When **signer_count** is null (legacy transaction), show **"—"** (or "—/—" per design).
- **Status updated column** — Show when the current status was last updated (formatted date/time from **status_last_updated**). **Plan 1’s data migration** sets status_last_updated = submitted_at for all backfilled transactions, so migrated rows show a consistent value (submit time). For any row where status_last_updated is still null (edge case), show **"—"**; the helper may optionally accept **fallback_to_submitted_at** for display-only fallback. Use a single helper **get_status_updated_display(transaction, fallback_to_submitted_at=False) -> str** so format and null handling are consistent.
- **Dashboard list** — Add **Signers** and **Status updated** columns to the signature transactions list (templates/deals/signature_transaction_list.html). Column order per design: after Status (e.g. Status → Signers → Status updated → Submitted at → Open link).
- **Deal View related table** — Add the same **Signers** and **Status updated** columns to the Deal detail page's "Signature transactions" table (templates/deals/deal_detail.html). Use the same helpers so behavior is identical.
- **Out of scope:** Plan 5 (download on complete). No change to status values or push logic.

---

## 2. Helpers (implementation detail)

### 2.1 get_signers_display(transaction) -> str

- **Signature:** `(transaction: SignatureTransaction) -> str`
- **Returns:** `"{signers_completed_count}/{signer_count}"` when signer_count is not None (e.g. "0/2", "1/2", "2/2"). When **signer_count is None** (legacy row), return **"—"** (design also allows "—/—"; "—" is shorter and consistent with Status updated null).
- **Logic:** If transaction.signer_count is None, return "—". Else use transaction.signers_completed_count (default 0 if None) and transaction.signer_count; return f"{completed}/{total}".
- **Location:** `apps.deals.signix` (alongside other signix helpers). Use in both list template and Deal View template so formatting stays in one place.

### 2.2 get_status_updated_display(transaction, fallback_to_submitted_at=False) -> str

- **Signature:** `(transaction: SignatureTransaction, fallback_to_submitted_at: bool = False) -> str`
- **Returns:** Formatted date/time string when status_last_updated (or fallback) is set; otherwise **"—"**.
- **Logic:** Prefer transaction.status_last_updated. If None and fallback_to_submitted_at is True, use transaction.submitted_at. Format with a single format string used everywhere (e.g. `"M j, Y g:i A"` to match "Submitted at"). If the chosen value is None, return "—". Use Django's date template filter equivalent in Python: `date_format(value, "M j, Y g:i A")` from django.utils.formats or format the datetime with strftime.
- **Location:** `apps.deals.signix`. Use in both list template and Deal View template.
- **Recommendation:** Default fallback_to_submitted_at=False. **Plan 1’s data migration** already sets status_last_updated = submitted_at for all backfilled rows, so the Status updated column will have a value for migrated transactions without any display fallback. Use the fallback only if product wants to show submitted_at for any remaining nulls (e.g. rows created after schema but before any push).

---

## 3. Column Placement and Copy

### 3.1 Dashboard list (signature_transaction_list.html)

- **Current columns (order):** Deal, Description, SIGNiX DocumentSetID, Status, Submitted at, Open link.
- **New columns:** Insert **Signers** and **Status updated** after **Status**. Final order: Deal, Description, SIGNiX DocumentSetID, **Status**, **Signers**, **Status updated**, Submitted at, Open link.
- **Empty state:** Colspan for the "no transactions" row must include the new columns (e.g. colspan="8").

### 3.2 Deal View related table (deal_detail.html)

- **Current columns:** Submitted at, SIGNiX DocumentSetID, Status, Open signing.
- **New columns:** Add **Signers** and **Status updated** after **Status**. Final order: Submitted at, SIGNiX DocumentSetID, **Status**, **Signers**, **Status updated**, Open signing.
- Keep the same table styling (table-sm, etc.).

---

## 4. View Context

- **signature_transaction_list view** — Pass **get_signers_display** and **get_status_updated_display** (the callables from signix) in the template context so the template can call `get_signers_display(t)` and `get_status_updated_display(t)` for each row. No need to precompute per row in the view.
- **Deal detail context** — In **_deal_detail_context**, add **get_signers_display** and **get_status_updated_display** to the context dict so deal_detail.html can use them in the signature transactions table. All callers of _deal_detail_context (deal_detail, deal_send_for_signature re-render, etc.) then get the helpers automatically.

---

## 5. Implementation Order (Checklist)

### Batch 1 — Helpers and dashboard list (steps 1–4)

1. **Add get_signers_display**
   - In `apps/deals/signix.py`, implement `get_signers_display(transaction) -> str`. If transaction.signer_count is None, return "—". Else return f"{transaction.signers_completed_count or 0}/{transaction.signer_count}".

2. **Add get_status_updated_display**
   - In `apps/deals/signix.py`, implement `get_status_updated_display(transaction, fallback_to_submitted_at=False) -> str`. Use status_last_updated; if None and fallback_to_submitted_at, use submitted_at. Format with Django's date_format or strftime to match "M j, Y g:i A" (e.g. `date_format(dt, "DATETIME_FORMAT")` or a fixed format). Return "—" when the chosen datetime is None.

3. **Update dashboard list template and view**
   - In `templates/deals/signature_transaction_list.html`: add `<th>Signers</th>` and `<th>Status updated</th>` after Status; in each row add `<td>{{ get_signers_display(t) }}</td>` and `<td>{{ get_status_updated_display(t) }}</td>`. Update the empty-state colspan to 8.
   - In `signature_transaction_list` view: add to context `"get_signers_display": get_signers_display, "get_status_updated_display": get_status_updated_display` (import from .signix).

4. **Verification (Batch 1)**
   - Run `python manage.py check`. Run unit tests: `python manage.py test apps.deals.tests.test_dashboard_signers` (Section 6). Manual: open Signature transactions list; confirm Signers and Status updated columns appear; for a transaction with signer_count=2, signers_completed_count=1, expect "1/2"; for null signer_count expect "—".

### Batch 2 — Deal View table and tests (steps 5–7)

5. **Update _deal_detail_context**
   - In `apps/deals/views.py`, in _deal_detail_context, add to ctx: `"get_signers_display": get_signers_display, "get_status_updated_display": get_status_updated_display`. Import get_signers_display and get_status_updated_display from .signix.

6. **Update deal_detail.html signature transactions table**
   - Add `<th>Signers</th>` and `<th>Status updated</th>` after Status in the table header. In each row add `<td>{{ get_signers_display(t) }}</td>` and `<td>{{ get_status_updated_display(t) }}</td>`.

7. **Verification (Batch 2)**
   - Open a Deal detail page that has signature transactions. Confirm the table shows Signers and Status updated columns and values match the list view. Run tests (Section 6) including Deal View tests.

---

## 5a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps and tests below.

### Batch 1 — Helpers and dashboard list

**Includes:** get_signers_display(transaction), get_status_updated_display(transaction) in signix.py; signature_transaction_list template adds Signers and Status updated columns; signature_transaction_list view passes helpers in context.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Unit tests:** `python manage.py test apps.deals.tests.test_dashboard_signers` — all pass (Section 6).
3. **Dashboard list:** Log in, open **Signature transactions**. Table has columns Signers and Status updated. Create a transaction with signer_count=2, signers_completed_count=0 (or 1); confirm "0/2" or "1/2". Transaction with signer_count=None shows "—" in Signers; null status_last_updated shows "—" in Status updated.
4. **Existing tests:** `python manage.py test apps.deals.tests.test_signature_transaction_dashboard` — still pass (no regression).

### Batch 2 — Deal View and polish

**Includes:** _deal_detail_context adds get_signers_display and get_status_updated_display; deal_detail.html signature transactions table adds Signers and Status updated columns.

**How to test after Batch 2:**

1. **Deal detail:** Open a deal that has signature transactions. Table shows Signers and Status updated with same values as on the list view.
2. **Full test suite:** `python manage.py test apps.deals.tests.test_signature_transaction_dashboard apps.deals.tests.test_deal_view_signature_transactions apps.deals.tests.test_dashboard_signers` — all pass.

---

## 6. Unit Tests (add to apps.deals.tests)

Create **apps/deals/tests/test_dashboard_signers.py** (Plan 4: Signers and Status updated columns). Use the same test setup as test_signature_transaction_dashboard (Deal, DocumentSet, User, SignatureTransaction).

### 6.1 get_signers_display

- **test_signers_display_normal** — Transaction with signer_count=2, signers_completed_count=1. get_signers_display(transaction) returns "1/2".
- **test_signers_display_zero_of_two** — signer_count=2, signers_completed_count=0. Returns "0/2".
- **test_signers_display_all_complete** — signer_count=2, signers_completed_count=2. Returns "2/2".
- **test_signers_display_null_signer_count** — signer_count=None (legacy). Returns "—".
- **test_signers_display_null_completed_count_treated_as_zero** — signer_count=2, signers_completed_count=None. Returns "0/2" (or ensure helper uses 0 when None).
- **test_signers_display_zero_signers** — signer_count=0, signers_completed_count=0. Returns "0/0" (per Plan 3 decided behavior).

### 6.2 get_status_updated_display

- **test_status_updated_display_with_value** — transaction.status_last_updated set to a known datetime (timezone-aware). get_status_updated_display(transaction) returns the formatted string (e.g. "Mar 15, 2025 2:30 PM" or equivalent for the app's locale).
- **test_status_updated_display_null_returns_dash** — status_last_updated=None, fallback_to_submitted_at=False. Returns "—".
- **test_status_updated_display_fallback_to_submitted_at** — status_last_updated=None, submitted_at set, fallback_to_submitted_at=True. Returns formatted submitted_at.
- **test_status_updated_display_null_and_no_fallback** — status_last_updated=None, submitted_at set, fallback_to_submitted_at=False. Returns "—".

### 6.3 Dashboard list view (integration)

- **test_list_includes_signers_and_status_updated_columns** — GET signature_transaction_list. Assert response contains "Signers", "Status updated" (column headers). Assert response contains "0/2" or "—" for a created transaction with signer_count=2 or signer_count=None.
- **test_list_signers_column_value** — Create transaction with signer_count=2, signers_completed_count=1. GET list. assertContains(resp, "1/2").
- **test_list_status_updated_shows_dash_when_null** — Create transaction with status_last_updated=None. GET list. Assert the cell for Status updated shows "—" (e.g. assertContains(resp, "—") in the table body; may need to assert structure or use a more specific check).
- **test_list_empty_state_colspan** — GET list with no transactions. Assert empty row has colspan="8" (or the number of columns including Signers and Status updated).

### 6.4 Deal View (integration)

- **test_deal_detail_signature_table_has_signers_and_status_updated** — Deal with one signature transaction (signer_count=2). GET deal_detail. assertContains "Signers", "Status updated", "0/2" or "1/2" as appropriate.
- **test_deal_detail_signers_null_safe** — Transaction with signer_count=None. GET deal_detail. Assert "—" appears in the signature transactions table for Signers.
- **test_deal_detail_context_includes_helper_callables** — Call _deal_detail_context(deal, request) (or the helper that builds deal detail context). Assert the returned context dict contains keys **get_signers_display** and **get_status_updated_display** and that they are callable (e.g. call each with a transaction and get a string). Ensures the detail template can render Signers and Status updated columns.

---

## 7. File Summary

| Item | Value |
|------|--------|
| App / module | `apps.deals` (signix.py for helpers; views.py for context) |
| New helpers | get_signers_display(transaction), get_status_updated_display(transaction, fallback_to_submitted_at=False) in signix.py |
| Modified view | signature_transaction_list — add get_signers_display, get_status_updated_display to context |
| Modified context builder | _deal_detail_context — add get_signers_display, get_status_updated_display to context |
| Templates | signature_transaction_list.html (add Signers, Status updated columns; colspan 8); deal_detail.html (add Signers, Status updated to signature transactions table) |
| Tests | apps/deals/tests/test_dashboard_signers.py |

---

## 8. Open Issues / Implementation Decisions

- **Status updated null display:** When status_last_updated is null, show **"—"** by default. **Plan 1’s data migration** sets status_last_updated = submitted_at for all backfilled transactions, so migrated rows have a value and no display fallback is needed for migration. The fallback_to_submitted_at option remains for edge cases (e.g. rows created after the schema but before any push). **Decided for this plan:** Use fallback_to_submitted_at=False in templates; the migration is the primary mechanism for a consistent Status updated value on existing transactions.
- **Date format for Status updated:** Use the same format as "Submitted at" (e.g. `"M j, Y g:i A"`) so the two columns are visually consistent. In Python use `django.utils.formats.date_format(dt, "SHORT_DATETIME_FORMAT")` or a fixed strftime; ensure timezone-aware datetimes are formatted correctly when USE_TZ is True.
- **Signers column header label:** Use **"Signers"** (design). Alternative "Progress" or "Signers (X/Y)"; this plan uses "Signers" with cell content "0/2", etc.
- **Colspan for empty state:** Dashboard list has 8 columns after this plan; the "No signature transactions yet" row must use colspan="8". Deal View table has 6 columns; no empty row in that table (it shows "No signature transactions for this deal" outside the table), so no colspan change there.
- **Helper location:** Helpers live in **signix.py** (not a separate dashboard module) so all SIGNiX-related display logic stays in one app and can be imported by views without circular imports. If the codebase later splits "signix services" vs "signix display," the helpers can move to a small signix_display or signix_utils module; for now signix.py is acceptable.

---

## 9. Implementation Notes

- **Existing Plan 8/9 tests:** test_signature_transaction_dashboard and test_deal_view_signature_transactions should still pass after adding columns (they assert on content and status codes; add new assertions in test_dashboard_signers.py for the new columns rather than overloading existing tests).
- **Import in views:** Add to views.py: `from .signix import (..., get_signers_display, get_status_updated_display)`. Use in signature_transaction_list and _deal_detail_context.
- **Template safety:** get_signers_display(t) and get_status_updated_display(t) return plain strings; no need for |safe. If a transaction is missing from the loop variable, ensure the template does not call the helper with None (current loops iterate over signature_transaction_list and signature_transactions, which are querysets, so t is always a transaction).
- **Zero signers:** Per Plan 3, signer_count may be 0; get_signers_display should return "0/0" in that case (no special case needed: f"{completed or 0}/{total}" with total=0).

---

## 10. Manual Testing (Details)

Use the following to verify the new columns without relying solely on unit tests.

**1. Dashboard list — new columns present**  
Log in as a user who can see the Signature transactions list. Open **Signature transactions** (sidebar or direct URL). Confirm the table has column headers: **Signers** and **Status updated** (after Status). If there are no transactions, confirm the empty state still looks correct (one row, centered message, no broken layout).

**2. Dashboard list — values**  
Create or pick a signature transaction that has signer_count set (e.g. 2) and signers_completed_count set (e.g. 0 or 1). Reload the list. Confirm the Signers cell shows "0/2" or "1/2". For **backfilled transactions** (Plan 1 migration), status_last_updated will equal submitted_at, so Status updated shows that date. If status_last_updated is null (edge case), confirm the cell shows "—".

**3. Dashboard list — legacy (null signer_count)**  
If you have (or create) a transaction with signer_count=None (e.g. created after schema but not backfilled, or edge case), open the list and confirm the Signers cell shows "—". After Plan 1’s data migration, all existing rows have status_last_updated = submitted_at, so Status updated should show a date for backfilled rows; only true edge cases show "—" there.

**4. Deal detail — same columns and values**  
Open a Deal that has at least one signature transaction. Scroll to the **Signature transactions** card. Confirm the table has **Signers** and **Status updated** columns and the values match what you see on the full list (same "0/2", "—", etc.).

**5. Format consistency**  
Confirm that Status updated uses the same date/time format as Submitted at (e.g. "Mar 15, 2025 2:30 PM") when both are present.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md (Plan 5).*

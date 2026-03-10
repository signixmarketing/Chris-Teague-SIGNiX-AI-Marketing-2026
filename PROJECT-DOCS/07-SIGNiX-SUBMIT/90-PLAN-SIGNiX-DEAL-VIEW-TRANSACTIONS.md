# Plan: Deal View — Related Signature Transactions (Plan 9)

This document outlines how to add **related signature transactions** on the Deal detail page: a subsection below the Documents section that lists signature transactions for this deal (Submitted at, SIGNiX DocumentSetID, Status, optional "Open signing" link), a link to the full dashboard, and **Delete Transaction History (for this deal)** with confirmation.

**Design reference:** [DESIGN-SIGNiX-SUBMIT.md](DESIGN-SIGNiX-SUBMIT.md) — Section 7.5 (Deal View — Related signature transactions), Section 3.4 (Dashboard and Deal View). Section 4.1 (SignatureTransaction model).

**Prerequisites:** Plan 2 (SignatureTransaction model, Deal relation with `related_name='signature_transactions'`) is implemented. Plan 8 (dashboard) is optional for the "View all signature transactions" link but not required for this plan to function. Transactions are created by Plans 6/7.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Placement** — Below the **Documents** section (and below the documents table/card), add a subsection **"Signature transactions"** (or "Related signature transactions") as a **separate card** (same style as Documents card) for clear structure (decided; see Section 8).
- **Table** — Columns: Submitted at, SIGNiX DocumentSetID, Status, optional "Open signing" link when the transaction has a first-signing URL and status is Submitted or In Progress. Same visibility rule as Plan 8: show "Open signing" to all authenticated users when the link is present and status allows. Order: newest first (`order_by('-submitted_at')`).
- **Link to dashboard** — A link "View all signature transactions" that goes to the dashboard list (`deals:signature_transaction_list`). Shown whenever the subsection is visible.
- **Delete Transaction History (for this deal)** — A button that deletes **all** signature transactions **for this deal only**. Use a **separate confirmation URL** (GET: confirmation page; POST: delete then redirect back to deal detail). For testing; may be removed or hidden later (Design 7.5).
- **When to show the subsection** — **Decided:** Always show the "Signature transactions" subsection on Deal detail so the user can see the list (or empty state) and the link to the full dashboard. When there are no transactions, show an empty state message and **hide** the Delete button (decided; see Section 8).
- **Access** — Same as deal detail (authenticated users; no extra permission).
- **Out of scope:** Transaction detail page, push-based status updates, changing the dashboard (Plan 8).

---

## 2. Data and Context

- **Source:** `deal.signature_transactions` (reverse relation from Plan 2). Order by `-submitted_at` for newest first.
- **Deal detail view:** Add to the deal detail context: `signature_transactions = deal.signature_transactions.order_by('-submitted_at')`. **Decided:** Add this inside **`_deal_detail_context`** (the helper that builds the context dict) so every code path that renders deal detail — including Plan 7 re-render on validation error, generate-documents error, regenerate-documents error — gets `signature_transactions` without changing each view. One extra query per deal detail load is acceptable.
- **Delete for this deal:** `SignatureTransaction.objects.filter(deal=deal).delete()` (or `deal_id=pk`). Run in a POST view after confirmation. **Stored artifacts:** Per design (DESIGN-SIGNiX-DASHBOARD-AND-SYNC Section 6.5a), when each SignatureTransaction is deleted, its **audit_trail_file** and **certificate_of_completion_file** are also removed from media storage via a **pre_delete** signal; no orphaned files remain.

---

## 3. URL for Delete (This Deal)

- **Delete all for this deal:** **Decided:** Deal-scoped URL `path("<int:pk>/signatures/delete-all/", ...)`, full path `/deals/<pk>/signatures/delete-all/`. GET: confirmation template; POST: `SignatureTransaction.objects.filter(deal_id=pk).delete()`, then redirect to `deals:deal_detail` with success message. Same pattern as Plan 8.

---

## 4. "Open signing" Link

- **When to show:** When the transaction has a non-empty `first_signing_url` and status is Submitted or In Progress. Same rule as Plan 8 dashboard.
- **Who can see it:** **Decided:** Show "Open signing" to all authenticated users when `first_signing_url` is non-empty and status is Submitted or In Progress (consistent with Plan 8).

---

## 5. Deal Detail Template Changes

- **Placement:** After the Documents card, add a **new card** with heading "Signature transactions" (or "Related signature transactions") (decided: separate card). Use the same vertical spacing as other section cards (e.g. Bootstrap `mb-3`). **Spacing:** So the gap between Documents and Signature transactions matches the gap between Signers and Documents, the **Documents card** should also have a bottom margin (`mb-3`); if it currently has none, add it when adding the new subsection.
- **Content:** When there are transactions: a **top row above the table** with the "View all signature transactions" link on the left and the "Delete Transaction History" button on the right (same pattern as the Documents card: `d-flex justify-content-between` so action buttons are top right). Then the table. A table with columns: Submitted at, SIGNiX DocumentSetID, Status, optional "Open signing" (link with `target="_blank"` and `rel="noopener noreferrer"` to `transaction.first_signing_url` when non-empty and status in [Submitted, In Progress]). When there are no transactions, show empty state message and the "View all signature transactions" link only; hide the Delete button.
- **Empty state:** When `signature_transactions` is empty, show a single line or message: e.g. "No signature transactions for this deal." and the "View all signature transactions" link. Do not show the Delete button when the list is empty.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Deal detail context and table (steps 1–4)

1. **Deal detail context**
   - Add `signature_transactions = deal.signature_transactions.order_by('-submitted_at')` to the **`_deal_detail_context`** helper (in `apps/deals/views.py`) so all callers — deal_detail, deal_generate_documents (error path), deal_regenerate_documents (error path), deal_send_for_signature (validation error path) — get it without changing each view.

2. **Template — subsection and table**
   - In `templates/deals/deal_detail.html`, after the Documents card, add a new card: heading "Signature transactions" (or "Related signature transactions"), table with columns Submitted at, SIGNiX DocumentSetID, Status, Open signing (when applicable). Use the same card margin as other sections (e.g. `mb-3`). If the Documents card has no bottom margin, add `mb-3` to it so spacing between Documents and Signature transactions is consistent with Signers–Documents. Iterate over `signature_transactions`. Use Bootstrap table classes to match the Documents table. Date format: e.g. `|date:"M j, Y g:i A"`.

3. **Link to dashboard**
   - In the same subsection, add a link "View all signature transactions" pointing to `{% url 'deals:signature_transaction_list' %}`.

4. **Verification (Batch 1)**
   - Load a deal that has signature transactions; subsection appears with rows. Load a deal with no transactions; subsection appears with empty state. Link to dashboard works.

### Batch 2 — Delete for this deal (steps 5–8)

5. **URL and view**
   - Add `path("<int:pk>/signatures/delete-all/", views.deal_signature_transaction_delete_all, name="deal_signature_transaction_delete_all")` in `apps/deals/urls.py`. View: GET renders confirmation template; POST performs `SignatureTransaction.objects.filter(deal_id=pk).delete()`, then redirects to `deals:deal_detail` with `pk` and success message. Require login; use `get_object_or_404(Deal, pk=pk)` so 404 if deal does not exist. **Stored files:** Each deleted transaction's audit trail and certificate of completion files are removed from media storage by the **pre_delete** signal on SignatureTransaction (Design Section 6.5a, 7.4).

6. **Confirmation template**
   - Create `templates/deals/deal_signature_transaction_delete_all_confirm.html`. Content: message "Are you sure? This will remove all transaction records for this deal.", form with POST to the delete URL, Cancel link back to deal detail.

7. **Delete button on deal detail**
   - In the Signature transactions subsection, add a "Delete Transaction History" button that links to the confirmation page (GET). Show only when `signature_transactions` is non-empty. Place it in a **top row above the table** (link "View all signature transactions" on the left, button on the right), matching the Documents card so action buttons are consistently in the top right.

8. **Verification (Batch 2)**
   - From deal detail, click "Delete Transaction History"; confirmation page appears. Confirm; only this deal's transactions are deleted; redirect to deal detail with success message.

### Batch 3 — Tests and polish (steps 9–10)

9. **Tests**
   - Deal detail: with no signature transactions, subsection shows empty state and no Delete button. With transactions, table shows rows and Delete button. Open signing link appears when first_signing_url and status allow; **when status is e.g. Complete, assert the signing URL is not in the response** (column header "Open signing" is always present). Delete flow: GET and **POST** require login; GET returns confirmation; POST deletes only that deal's transactions and redirects to deal detail. **Re-render context:** Test that when a deal-detail re-render path is used (e.g. Plan 7 validation error), the response still contains the Signature transactions subsection (e.g. mock `SignixValidationError` on send-for-signature, POST, then assert "Signature transactions" in response and `deal_detail.html` used).

10. **Polish**
    - Re-render paths (Plan 7 validation error, generate/regenerate error) already receive `signature_transactions` because it is added in `_deal_detail_context`; no extra code change. Verify by testing at least one re-render path (e.g. send-for-signature validation error) and asserting the subsection appears in the response.

---

## 6a. Implementation Batches and Verification

**Batch 1 — Context and table:** Add signature_transactions to deal detail context; new card in deal_detail.html with table and "View all signature transactions" link; empty state when no transactions.

**Implementation notes (Batch 1):** Add `signature_transactions` in **`_deal_detail_context`** so every deal detail render path gets it. Use `mb-3` on the new Signature transactions card; ensure the Documents card also has `mb-3` so the vertical gap between Documents and Signature transactions matches the gap between Signers and Documents. Tests: optional in Batch 1; see `apps/deals/tests/test_deal_view_signature_transactions.py` for examples (subsection presence, empty state, table content, Open signing link).

**Batch 2 — Delete for this deal:** URL `/deals/<pk>/signatures/delete-all/`, view with GET confirm and POST delete, confirmation template, Delete button on deal detail (shown only when there are transactions).

**Implementation notes (Batch 2):** Place the "View all signature transactions" link and "Delete Transaction History" button in a **top row above the table** (`d-flex justify-content-between`: link left, button right) so the Delete button is in the top right, consistent with the Documents card (Regenerate, Delete Document Set, Send for Signature). When the list is empty, do not show the top row with the button — only the empty state message and the View all link.

**Batch 3 — Tests and polish:** Tests for subsection and delete flow; context on re-renders.

**Implementation notes (Batch 3):** Test module can use three classes: list/subsection tests, delete-all tests, and Batch 3 tests (re-render, POST login, open signing when not allowed). **Delete flow:** Assert both GET and POST require login for the deal-scoped delete-all URL. **Open signing when not allowed:** To assert the link is hidden (e.g. status Complete), assert the **signing URL** is not in the response, not the text "Open signing" (column header is always present). **Re-render polish:** No code change needed if `signature_transactions` is in `_deal_detail_context`; verify by triggering a re-render (e.g. mock `SignixValidationError` on `submit_document_set_for_signature`, POST to `deal_send_for_signature`) and asserting the response contains "Signature transactions" and uses `deal_detail.html`.

---

## 7. File Summary

| Item | Value |
|------|--------|
| URL (delete for deal) | `deals:deal_signature_transaction_delete_all` → `/deals/<pk>/signatures/delete-all/` |
| View | `deal_signature_transaction_delete_all(request, pk)` in `apps/deals/views.py` |
| Template (confirm) | `deals/deal_signature_transaction_delete_all_confirm.html` |
| Template (deal detail) | `deals/deal_detail.html` — add Signature transactions card and table |
| Context (deal detail) | `signature_transactions` in `_deal_detail_context` (ordered by -submitted_at) |
| Tests | `apps/deals/tests/test_deal_view_signature_transactions.py` — subsection, empty state, table, Open signing, delete flow, re-render (Batches 1–3) |
| Model | `SignatureTransaction` (Plan 2); no new models |

---

## 8. Open Issues / Implementation Decisions

- **Subsection placement — same card vs separate card:** **Decided:** Use a **separate card** below the Documents card so the subsection is clearly distinct and the Documents card stays focused.

- **When to show the subsection:** **Decided:** Always show on every deal detail. Empty state when no transactions; hide Delete button when empty so "View all signature transactions" is always available.

- **Delete — URL pattern:** **Decided:** Use a **separate** deal-scoped URL `/deals/<pk>/signatures/delete-all/` with GET = confirmation and POST = delete then redirect to deal detail (same pattern as Plan 8).

- **"Open signing" visibility:** **Decided:** Same as Plan 8 — show for **all authenticated users** when first_signing_url is non-empty and status is Submitted or In Progress.

- **Context (signature_transactions):** **Decided:** Add `signature_transactions = deal.signature_transactions.order_by('-submitted_at')` **inside `_deal_detail_context`** so every code path that renders deal_detail (including Plan 7 re-render, generate/regenerate error paths) gets it without changing each view.

- **Empty state wording:** **Decided:** Use "No signature transactions for this deal." Optional: add "Send documents for signature from the Documents section above."

- **Ordering:** **Decided:** Newest first, `order_by('-submitted_at')`.

---

## 9. Summary: Decided Implementation Choices

| Item | Decided choice |
|------|----------------|
| **Subsection placement** | Separate card below the Documents card. |
| **When to show subsection** | Always show on deal detail; empty state when no transactions; hide Delete button when empty. |
| **Delete URL** | Separate URL `/deals/<pk>/signatures/delete-all/` with GET = confirm, POST = delete, redirect to deal detail. |
| **"Open signing" visibility** | Same as Plan 8 — show for all authenticated users when URL present and status allows. |
| **Context (signature_transactions)** | Add in `_deal_detail_context`; all deal detail render paths then include it. |
| **Card spacing** | New card uses `mb-3`; Documents card should have `mb-3` so spacing between sections is consistent. |
| **Delete button / View all** | When transactions exist: top row above table — link left, Delete button right (match Documents card). |
| **Empty state** | "No signature transactions for this deal."; optional hint about Send for Signature. |

---

*End of plan. Proceed to implementation only after review. This completes the SIGNiX submit flow plans (Plans 1–9) per PHASE-PLANS-SIGNiX-SUBMIT.*

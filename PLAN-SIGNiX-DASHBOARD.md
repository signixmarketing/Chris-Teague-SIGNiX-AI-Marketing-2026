# Plan: Signature Transactions Dashboard (Plan 8)

This document outlines how to add the **Signature transactions dashboard**: a main menu item, a list view of all signature transactions submitted to SIGNiX (with Deal link, description, SIGNiX DocumentSetID, status, submitted date, and optional "Open link" for signing), and a **Delete Transaction History** button that removes all records (for testing).

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — Section 7.3 (Signature transactions dashboard), Section 3.4 (Dashboard and Deal View). Section 4.1 (SignatureTransaction model).

**Prerequisites:** Plan 2 (SignatureTransaction model, Deal relation) is implemented. Plans 6 and 7 create transactions via the orchestrator. No dependency on Plan 9 (Deal View table); the dashboard lists all transactions system-wide.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Main menu** — Add a sidebar/menu item (e.g. "Signature transactions" or "Signatures") that links to the dashboard. URL **`/deals/signatures/`** under the deals app (decided; see Section 8).
- **List view** — A single page that shows a table of all `SignatureTransaction` records: Deal (link to deal detail), description/label (derived from deal id and document set template name), SIGNiX DocumentSetID, Status, Submitted at, optional "Open link" when `first_signing_url` is non-empty and status is Submitted or In Progress (shown to all authenticated users in initial version; see Section 4, 8).
- **Delete Transaction History** — A button (e.g. above or below the table) that deletes **all** signature transactions in the system. Require a confirmation step (GET: confirmation page or modal; POST: perform delete). Design states this is for **testing** and may be removed or hidden later.
- **Access** — Authenticated users only (`@login_required` or equivalent). No special role requirement unless the project adds one.
- **Out of scope:** Deal View related transactions table (Plan 9), transaction detail page (design does not require a dedicated detail view; link to Deal suffices), push-based status updates (status remains as stored; dashboard just displays it).

---

## 2. Data and Queries

- **Model:** `SignatureTransaction` (Plan 2) — `deal`, `document_set`, `signix_document_set_id`, `transaction_id`, `status`, `first_signing_url`, `submitted_at`, `completed_at`.
- **List query:** `SignatureTransaction.objects.all().order_by('-submitted_at').select_related('deal', 'document_set', 'document_set__document_set_template')` so each row has deal, document_set, and template for the description. If document_set_template is on DocumentSet as a ForeignKey, prefetch or select_related as needed.
- **Description/label:** Derive per row in the view or template from `deal_id` and `document_set.document_set_template.name` (or deal type name if template name blank). No stored label on SignatureTransaction (decided for Plan 8; see Section 8).
- **Delete all:** `SignatureTransaction.objects.all().delete()`. Run in a POST view after confirmation.

---

## 3. URL and View Names

- **Dashboard list:** **Decided:** URL `path("signatures/", ...)` in `apps/deals/urls.py`, full path `/deals/signatures/`. Views remain in `apps.deals`.
- **Delete all:** **Decided:** Separate URL `path("signatures/delete-all/", ...)` with GET = confirmation page, POST = delete then redirect to list.

---

## 4. "Open link" / "Sign" Column

- **When to show:** When the transaction has a non-empty `first_signing_url` and status is one of Submitted or In Progress.
- **Who can see it:** **Decided (Plan 8):** Show "Open link" for **all authenticated users** when the above conditions hold. Design intent to restrict to "current user is first signer" is documented as a possible enhancement (would require storing first-signer identity or using a convention such as lease officer = first signer). SIGNiX may enforce identity when the link is opened.

---

## 5. Main Menu (Sidebar)

- **Placement:** Add a new item in the sidebar in `templates/base.html`, after Deals and before or after the document templates section. Label: "Signature transactions" or "Signatures".
- **URL:** Use the dashboard list URL, e.g. `{% url 'deals:signature_transaction_list' %}`.
- **Active state:** Set `active` when `request.resolver_match.url_name == 'signature_transaction_list'` (or the chosen view name). Follow the same pattern as other nav items (e.g. `request.resolver_match.app_name == 'deals'` for Deals; for signatures we need a specific url_name check so the Signatures item is active only on the signatures page, not on every deals page).
- **Icon:** Use a Bootstrap icon consistent with the rest (e.g. `bi bi-pen` or `bi bi-file-earmark-signature`).

---

## 6. Implementation Order (Checklist)

### Batch 1 — List view and URL (steps 1–4)

1. **URL and view**
   - In `apps/deals/urls.py`, add `path("signatures/", views.signature_transaction_list, name="signature_transaction_list")`. In `apps/deals/views.py`, add `signature_transaction_list(request)`: require login; query `SignatureTransaction.objects.all().order_by('-submitted_at').select_related('deal', 'document_set')` (add `document_set__document_set_template` if DocumentSet has that FK). Pass queryset to template. Render template `deals/signature_transaction_list.html` (or equivalent).

2. **Template**
   - Create `templates/deals/signature_transaction_list.html` (or `signatures/signature_transaction_list.html` if using a separate app). Extend `base.html`. Content: page title "Signature transactions"; a table with columns: Deal (link to `deals:deal_detail` with `transaction.deal_id`), Description (derived label per Section 2), SIGNiX DocumentSetID, Status, Submitted at, optional "Open link" (link with `target="_blank"` and `rel="noopener noreferrer"` to `transaction.first_signing_url` when non-empty and status in [Submitted, In Progress]). Use Bootstrap table classes to match deal list and other list pages.

3. **Description/label**
   - In the template or in the view, compute a short label per transaction: e.g. `"Deal #{{ t.deal_id }} – {{ t.document_set.document_set_template.name|default:t.deal.deal_type.name|default:'Documents' }}"`. If `document_set` or template is missing, fallback to "Deal #&lt;id&gt;" or "—".

4. **Verification (Batch 1)**
   - Navigate to `/deals/signatures/`; list appears (empty or with data). Deal link goes to deal detail. If any transaction has first_signing_url and status Submitted/In Progress, "Open link" appears and opens in new tab.

### Batch 2 — Delete all and menu (steps 5–8)

5. **Delete all — confirmation and action**
   - Add URL, e.g. `path("signatures/delete-all/", views.signature_transaction_delete_all, name="signature_transaction_delete_all")`. View: GET renders a confirmation template ("Are you sure? This will remove all transaction records.") with a form that POSTs to the same view; POST performs `SignatureTransaction.objects.all().delete()`, then redirects to `deals:signature_transaction_list` with a success message. Require login.

6. **Delete all — link from list**
   - On the list template, add a "Delete Transaction History" button (e.g. above the table) that links to the delete-all confirmation page (GET). Style as a danger/outline-danger button so it is clear it is destructive.

7. **Sidebar menu**
   - In `templates/base.html`, add a nav item: "Signature transactions" (or "Signatures") linking to `deals:signature_transaction_list`. Use `request.resolver_match.url_name == 'signature_transaction_list'` for active class so only this page is highlighted. Add an icon (e.g. `bi bi-pen` or `bi bi-file-earmark-signature`).

8. **Verification (Batch 2)**
   - Click "Delete Transaction History" from list; confirmation page appears. Confirm; all transactions deleted and redirect to list. Sidebar shows "Signature transactions" and it is active on the list page.

### Batch 3 — Tests and polish (steps 9–10)

9. **Tests**
   - List view: GET with no transactions returns 200 and empty table. GET with fixtures returns table with expected columns and deal links. Open link present only when first_signing_url and status allow. Delete-all: GET returns confirmation; POST deletes all and redirects with message. Require login: unauthenticated request redirects to login.

10. **Polish**
    - Empty state: when there are no transactions, show a message (e.g. "No signature transactions yet. Send documents for signature from a Deal detail page."). Date formatting: use `|date:"M j, Y g:i A"` or similar for submitted_at.

---

## 6a. Implementation Batches and Verification

**Batch 1 — List view and URL**

**Includes:** URL `/deals/signatures/`, view `signature_transaction_list`, template with table (Deal, Description, SIGNiX DocumentSetID, Status, Submitted at, Open link), description derived from deal + document set template.

**How to test after Batch 1:**

1. Open `/deals/signatures/`; list renders. Deal links work. Open link appears when first_signing_url is set and status is Submitted/In Progress.

**Batch 2 — Delete all and menu**

**Includes:** URL for delete-all, GET confirmation and POST delete, "Delete Transaction History" button on list, sidebar nav item for Signature transactions.

**How to test after Batch 2:**

1. Delete all flow: confirm page → delete → redirect to list with success message. Sidebar shows Signature transactions and is active on list page.

**Batch 3 — Tests and polish**

**Includes:** View tests for list and delete-all, empty state message, date formatting.

**How to test after Batch 3:**

1. All tests pass. Manual: create a transaction (Plan 7), open dashboard, see row and Open link; delete all and confirm list is empty.

---

## 7. File Summary

| Item | Value |
|------|--------|
| URLs | `deals:signature_transaction_list` → `/deals/signatures/`, `deals:signature_transaction_delete_all` → `/deals/signatures/delete-all/` |
| Views | `signature_transaction_list(request)`, `signature_transaction_delete_all(request)` in `apps/deals/views.py` |
| Templates | `deals/signature_transaction_list.html`, `deals/signature_transaction_delete_all_confirm.html` (or single template with conditional) |
| Base template | `templates/base.html` — add nav item for Signature transactions |
| Model | `SignatureTransaction` (Plan 2); no new models |

---

## 8. Open Issues / Implementation Decisions

- **URL path:** **Decided:** Use `/deals/signatures/` and keep views in `apps.deals`. Design allows either; keeping under deals avoids a new app and matches Plan 2 (model in deals).

- **Delete all — same URL vs separate:** **Decided:** Use a **separate** URL `/deals/signatures/delete-all/` with GET = confirmation page and POST = delete then redirect to list.

- **Description/label storage:** **Decided:** Derive in the view or template from `deal_id` + `document_set.document_set_template.name` (or deal type name if template name blank). No new field on SignatureTransaction. If we later want a stable label that survives template renames, add a stored field in a follow-on change.

- **"Open link" visibility — who can see it:** **Decided:** Show "Open link" for **all authenticated users** when `first_signing_url` is non-empty and status is Submitted or In Progress. Restricting to "current user is first signer" (e.g. `request.user == transaction.deal.lease_officer`) remains a possible enhancement; implementing it would require a consistent convention or storing first-signer identity on the transaction.

- **Empty state message:** **Decided:** When the queryset is empty, show a short message: e.g. "No signature transactions yet. Send documents for signature from a Deal detail page."

- **Ordering:** **Decided:** `order_by('-submitted_at')` so newest first. Matches Plan 2 and Design.

- **Access control:** **Decided:** Authenticated users only (`@login_required`). No staff or special permission unless the project adds one.

- **Transaction detail page:** **Out of scope.** Design does not require a dedicated detail view; the list row and link to Deal are sufficient. Omit for Plan 8.

---

## 9. Summary: Decided Implementation Choices

| Item | Decided choice |
|------|----------------|
| **URL path** | `/deals/signatures/`; views in `apps.deals`. |
| **Delete all** | Separate URL `/deals/signatures/delete-all/` with GET = confirm, POST = delete. |
| **Description/label** | Derive in view/template from deal id + document set template name (no new field). |
| **"Open link" visibility** | Show for all authenticated users when URL present and status allows; "first signer only" is a possible future enhancement. |
| **Access control** | `@login_required` only unless project adds staff/permission. |

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md (Plan 9).*

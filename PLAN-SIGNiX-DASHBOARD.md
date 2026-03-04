# Plan: Signature Transactions Dashboard (Plan 8)

This document outlines how to add the **Signature transactions dashboard**: a main menu item, a list view of all signature transactions submitted to SIGNiX (with Deal link, description, SIGNiX DocumentSetID, status, submitted date, and optional "Open link" **so the first signer can re-open the signing flow if they did not complete it initially**), and a **Delete Transaction History** button that removes all records (for testing).

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — **Section 7.3** is the authoritative specification for the signature transactions dashboard (sidebar, list, delete-all). Section 3.4 summarizes the dashboard and Deal View; Section 4.1 defines the SignatureTransaction model. This plan implements Section 7.3 and flows from it (URLs, view names, templates, and batches).

**Prerequisites:** Plan 2 (SignatureTransaction model, Deal relation) is implemented. Plans 6 and 7 create transactions via the orchestrator. No dependency on Plan 9 (Deal View table); the dashboard lists all transactions system-wide.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Main menu** — Add a sidebar/menu item (e.g. "Signature transactions" or "Signatures") that links to the dashboard. URL **`/deals/signatures/`** under the deals app (decided; see Section 8).
- **List view** — A single page that shows a table of all `SignatureTransaction` records: Deal (link to deal detail), description/label (derived from deal id and document set template name), SIGNiX DocumentSetID, Status, Submitted at, optional "Open link" when `first_signing_url` is non-empty and status is Submitted or In Progress — **so the first signer can re-open the signing flow if they did not complete it when the transaction was created** (e.g. they closed the tab or returned later). Shown to all authenticated users in initial version; see Section 4, 8.
- **Delete Transaction History** — A button (e.g. above or below the table) that deletes **all** signature transactions in the system. Require a confirmation step (GET: confirmation page or modal; POST: perform delete). Design states this is for **testing** and may be removed or hidden later.
- **Access** — Authenticated users only (`@login_required` or equivalent). No special role requirement unless the project adds one.
- **Out of scope:** Deal View related transactions table (Plan 9), transaction detail page (design does not require a dedicated detail view; link to Deal suffices), push-based status updates (status remains as stored; dashboard just displays it).

---

## 2. Data and Queries

- **Model:** `SignatureTransaction` (Plan 2) — `deal`, `document_set`, `signix_document_set_id`, `transaction_id`, `status`, `first_signing_url`, `submitted_at`, `completed_at`.
- **List query:** `SignatureTransaction.objects.all().order_by('-submitted_at').select_related('deal', 'deal__deal_type', 'document_set', 'document_set__document_set_template')` so each row has deal, deal_type (for description fallback), document_set, and template. Include `deal__deal_type` so the template can fall back to deal type name when document_set_template is null.
- **Description/label:** Derive per row in the view or template from `deal_id` and `document_set.document_set_template.name` (or deal type name if template name blank). No stored label on SignatureTransaction (decided for Plan 8; see Section 8).
- **Delete all:** `SignatureTransaction.objects.all().delete()`. Run in a POST view after confirmation.

---

## 3. URL and View Names

- **Dashboard list:** **Decided:** URL `path("signatures/", ...)` in `apps/deals/urls.py`, full path `/deals/signatures/`. Views remain in `apps.deals`.
- **Delete all:** **Decided:** Separate URL `path("signatures/delete-all/", ...)` with GET = confirmation page, POST = delete then redirect to list.

---

## 4. "Open link" / "Sign" Column

- **Purpose:** The link opens the **first signer's SIGNiX signing URL**, allowing them to **re-enter the signing flow** if they did not complete signing when the transaction was first created (e.g. they closed the tab, returned later, or the session was interrupted). The dashboard (and, in Plan 9, the Deal View related transactions table) surfaces this link so the user can get back to the same transaction without relying on the initial pop-up or email.
- **When to show:** When the transaction has a non-empty `first_signing_url` and status is one of Submitted or In Progress.
- **Who can see it:** **Decided (Plan 8):** Show "Open link" for **all authenticated users** when the above conditions hold. Design intent to restrict to "current user is first signer" is documented as a possible enhancement (would require storing first-signer identity or using a convention such as lease officer = first signer). SIGNiX may enforce identity when the link is opened.

---

## 5. Main Menu (Sidebar)

- **Placement:** Add a new item in the sidebar in `templates/base.html`, after Deals and before or after the document templates section. Label: "Signature transactions" or "Signatures".
- **URL:** Use the dashboard list URL, e.g. `{% url 'deals:signature_transaction_list' %}`.
- **Active state:** Set `active` when `request.resolver_match.url_name == 'signature_transaction_list'` (or the chosen view name). Follow the same pattern as other nav items (e.g. `request.resolver_match.app_name == 'deals'` for Deals; for signatures we need a specific url_name check so the Signatures item is active only on the signatures page, not on every deals page).
- **Icon:** Use a Bootstrap icon consistent with the rest. **Use `bi bi-pen`** — it exists in Bootstrap Icons 1.11.x and fits "signature" (writing/pen). **Note:** `bi-file-earmark-signature` is not available in Bootstrap Icons 1.11.x; if the project upgrades to a version that adds it, it could be used instead.
- **"Deals" active state:** So that only "Signature transactions" is active on the signatures list and delete-all confirmation, the existing "Deals" nav item should **not** be active when `request.resolver_match.url_name` is `signature_transaction_list` or `signature_transaction_delete_all` (e.g. condition: `app_name == 'deals' and url_name not in ('signature_transaction_list', 'signature_transaction_delete_all')`).

---

## 6. Implementation Order (Checklist)

### Batch 1 — List view and URL (steps 1–4)

1. **URL and view**
   - In `apps/deals/urls.py`, add `path("signatures/", views.signature_transaction_list, name="signature_transaction_list")` — **place it before any `path("<int:pk>/", ...)` routes** so that `/deals/signatures/` is matched as the list view, not as a deal primary key. In `apps/deals/views.py`, add `signature_transaction_list(request)`: require login; query `SignatureTransaction.objects.all().order_by('-submitted_at').select_related('deal', 'deal__deal_type', 'document_set', 'document_set__document_set_template')`. Pass queryset to template as `signature_transaction_list`. Render template `deals/signature_transaction_list.html` (or equivalent).

2. **Template**
   - Create `templates/deals/signature_transaction_list.html` (or `signatures/signature_transaction_list.html` if using a separate app). Extend `base.html`. Content: page title "Signature transactions"; a table with columns: Deal (link to `deals:deal_detail` with `transaction.deal_id`), Description (derived label per Section 2), SIGNiX DocumentSetID, Status, Submitted at, optional "Open link" (link with `target="_blank"` and `rel="noopener noreferrer"` to `transaction.first_signing_url` when non-empty and **status is "Submitted" or "In Progress"** — use explicit `{% if t.status == "Submitted" or t.status == "In Progress" %}` in Django template, not `in` with a string, which does substring matching). Use Bootstrap table classes to match deal list and other list pages. **Empty state:** use `{% empty %}` with one row, colspan 6, message "No signature transactions yet. Send documents for signature from a Deal detail page." **Date:** use `{{ t.submitted_at|date:"M j, Y g:i A" }}` for Submitted at.

3. **Description/label**
   - In the template or in the view, compute a short label per transaction. **When `document_set` or `document_set_template` can be null**, use conditional blocks in the template rather than chained `|default:` (to avoid accessing `.name` on None): e.g. `{% if t.document_set.document_set_template %}{{ t.document_set.document_set_template.name }}{% elif t.deal.deal_type %}{{ t.deal.deal_type.name }}{% else %}Documents{% endif %}`. Prefix with "Deal #{{ t.deal_id }} – ".

4. **Verification (Batch 1)**
   - Navigate to `/deals/signatures/`; list appears (empty or with data). Deal link goes to deal detail. If any transaction has first_signing_url and status Submitted/In Progress, "Open link" appears and opens in new tab.

### Batch 2 — Delete all and menu (steps 5–8)

5. **Delete all — confirmation and action**
   - Add URL, e.g. `path("signatures/delete-all/", views.signature_transaction_delete_all, name="signature_transaction_delete_all")`. **Register this route before** `path("signatures/", ...)` in `urls.py` so that `/deals/signatures/delete-all/` is matched by the delete-all view, not the list view. View: GET renders a confirmation template ("Are you sure? This will remove all transaction records.") with a form that POSTs to the same view; POST performs `SignatureTransaction.objects.all().delete()`, then redirects to `deals:signature_transaction_list` with a success message (e.g. "All signature transaction records (N) have been removed." where N is the count before delete). Require login.

6. **Delete all — link from list**
   - On the list template, add a "Delete Transaction History" button (e.g. above the table) that links to the delete-all confirmation page (GET). Style as a danger/outline-danger button so it is clear it is destructive.

7. **Sidebar menu**
   - In `templates/base.html`, add a nav item: "Signature transactions" (or "Signatures") linking to `deals:signature_transaction_list`. Use `request.resolver_match.url_name == 'signature_transaction_list'` for active class so only this page is highlighted. Add an icon: **use `bi bi-pen`** (Bootstrap Icons 1.11.x; `bi-file-earmark-signature` is not available in that version). Ensure the existing "Deals" nav item is not active when on the signatures list or delete-all confirmation (see Section 5).

8. **Verification (Batch 2)**
   - Click "Delete Transaction History" from list; confirmation page appears. Confirm; all transactions deleted and redirect to list. Sidebar shows "Signature transactions" and it is active on the list page.

### Batch 3 — Tests and polish (steps 9–10)

9. **Tests**
   - List view: GET with no transactions returns 200 and empty table. GET with fixtures returns table with expected columns and deal links. Open link present only when first_signing_url and status allow; **assert that the signing URL is not in the response** when status is e.g. Complete (the column header "Open link" is always present, so do not assert absence of the text "Open link"). Delete-all: GET returns confirmation; POST deletes all and redirects with message. Require login: unauthenticated request redirects to login. Optional: empty-state message content; submitted_at date format.

10. **Polish**
    - Empty state: when there are no transactions, show a message (e.g. "No signature transactions yet. Send documents for signature from a Deal detail page."). Date formatting: use `|date:"M j, Y g:i A"` or similar for submitted_at.

---

## 6a. Implementation Batches and Verification

**Batch 1 — List view and URL**

**Includes:** URL `/deals/signatures/`, view `signature_transaction_list`, template with table (Deal, Description, SIGNiX DocumentSetID, Status, Submitted at, Open link), description derived from deal + document set template.

**How to test after Batch 1:**

1. Open `/deals/signatures/`; list renders. Deal links work. Open link appears when first_signing_url is set and status is Submitted/In Progress.

**Implementation notes (Batch 1):** Register the `signatures/` URL before any `<int:pk>/` routes in `urls.py` so the path is matched correctly. Use `select_related("deal", "deal__deal_type", "document_set", "document_set__document_set_template")` so the template can show description and fallback to deal type name when template is null. In the template, use `{% if t.status == "Submitted" or t.status == "In Progress" %}` for the Open link condition (Django template has no list-in for multiple values; string `in` is substring match). For description when `document_set_template` or `deal_type` can be missing, use `{% if %}...{% elif %}...{% else %}Documents{% endif %}` to avoid accessing `.name` on None. Empty state and date formatting (`|date:"M j, Y g:i A"`) can be implemented in Batch 1 to match other list pages. Optional: add basic list-view tests (login required, empty table, with fixture, open link when URL and status allow) in Batch 1 for earlier verification.

**Batch 2 — Delete all and menu**

**Includes:** URL for delete-all, GET confirmation and POST delete, "Delete Transaction History" button on list, sidebar nav item for Signature transactions.

**Implementation notes (Batch 2):** Register `signatures/delete-all/` **before** `signatures/` in `apps/deals/urls.py` so the path is matched correctly. Use **`bi-pen`** for the sidebar icon (Bootstrap Icons 1.11.x does not include `bi-file-earmark-signature`). Exclude `signature_transaction_list` and `signature_transaction_delete_all` from the "Deals" nav active condition so only "Signature transactions" is active on those pages. Success message after delete: e.g. "All signature transaction records (N) have been removed."

**How to test after Batch 2:**

1. Delete all flow: confirm page → delete → redirect to list with success message. Sidebar shows Signature transactions and is active on list page.

**Batch 3 — Tests and polish**

**Includes:** View tests for list and delete-all, empty state message, date formatting.

**Implementation notes (Batch 3):** Test module can use three classes: list view tests (`SignatureTransactionListViewTests`), delete-all tests (`SignatureTransactionDeleteAllTests`), and list UI tests (`SignatureTransactionListUITests` — Delete button and sidebar link). **Open link when not allowed:** The table always has a column header "Open link", so to assert the link is hidden (e.g. when status is Complete), assert that the **signing URL** is not in the response (or that the cell shows "—"), not `assertNotContains(resp, "Open link")`. **submitted_at in tests:** `SignatureTransaction.submitted_at` has `auto_now_add=True`; to test date formatting with a specific datetime, create the object then use `SignatureTransaction.objects.filter(pk=obj.pk).update(submitted_at=desired_datetime)` because `create(submitted_at=...)` is ignored.

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
| Tests | `apps/deals/tests/test_signature_transaction_dashboard.py` — list, delete-all, UI (Batch 3) |
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
| **Sidebar icon** | Use `bi-pen` (Bootstrap Icons 1.11.x; `bi-file-earmark-signature` not available). |
| **URL order** | Register `signatures/delete-all/` before `signatures/` in `urls.py`. |
| **Sidebar "Deals" active** | Exclude `signature_transaction_list` and `signature_transaction_delete_all` from Deals active state. |

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md (Plan 9).*

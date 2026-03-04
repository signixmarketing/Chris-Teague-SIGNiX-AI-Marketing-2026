# Plan: Signature Transaction Model (Plan 2)

This document outlines how to add the **SignatureTransaction** model and its relation to Deal (and DocumentSet). Each transaction represents one submission to SIGNiX: we store SIGNiX’s DocumentSetID, the client-chosen TransactionID, status, the first signer’s signing URL, and timestamps. This plan does **not** add list/detail UI—that is Plans 8 and 9. It only adds the model, migration, and Deal relation so that the orchestrator (Plan 6) can create and query signature transactions.

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — Section 4.1 (Signature transaction record), Section 4.2 (Document Instance Version status). PLAN-SIGNiX-SUBMIT-MASTER.md — Plan 2 deliverables.

**Prerequisites:** PLAN-MASTER plans 1–6 and PLAN-DOCS-MASTER plans 1–4 are implemented. The app has Deals and Document Sets (`apps.deals`, `apps.documents`).

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** A `SignatureTransaction` model in `apps.deals` that stores one row per SIGNiX submission: link to Deal and Document Set, SIGNiX DocumentSetID, client TransactionID, status, first-signing URL, submitted_at, completed_at.
- **Relations:** `Deal` gains a reverse relation (e.g. `related_name='signature_transactions'`) so that Deal detail and the dashboard can query `deal.signature_transactions` or `SignatureTransaction.objects.filter(deal=deal)`.
- **Out of scope this plan:** Any UI (list view, Deal View table), submit flow, or status updates. No views or URLs for signature transactions.

---

## 2. Model: SignatureTransaction

- **App:** `apps.deals` (per design Section 4.1: “Prefer `apps.deals` for the model and deal-scoped views”).
- **Persistence:** Existing database (SQLite). One table; multiple rows (one per submission).

**Fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `deal` | ForeignKey(Deal, on_delete=CASCADE, related_name='signature_transactions') | Deal from which this transaction was generated. |
| `document_set` | ForeignKey('documents.DocumentSet', on_delete=CASCADE) | Document set that was submitted (snapshot at submit time). |
| `signix_document_set_id` | CharField(max_length=255) | SIGNiX’s DocumentSetID returned from SubmitDocument. |
| `transaction_id` | CharField(max_length=36, blank=True) | Client-chosen TransactionID; **max length 36**, **UUID format** (e.g. from build_submit_document_body metadata). Optional for flexibility. |
| `status` | CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_SUBMITTED) | One of: Submitted, In Progress, Suspended, Complete, Cancelled. Until push is implemented, status stays "Submitted" unless updated manually. |
| `first_signing_url` | URLField(max_length=512, blank=True) | GetAccessLink URL for the first signer; opened in a separate window. |
| `submitted_at` | DateTimeField(auto_now_add=True) | When SubmitDocument was called. |
| `completed_at` | DateTimeField(null=True, blank=True) | When transaction was completed (from push or polling; used once push is implemented). |

**Status choices:**

Define constants and choices so Plan 6 and UI use the same values. **Define the five constants as class attributes on the model** (e.g. `STATUS_SUBMITTED = "Submitted"`) so that code can use `SignatureTransaction.STATUS_SUBMITTED`. Allowed values:

| Constant | Value (display) |
|----------|------------------|
| `STATUS_SUBMITTED` | `"Submitted"` |
| `STATUS_IN_PROGRESS` | `"In Progress"` |
| `STATUS_SUSPENDED` | `"Suspended"` |
| `STATUS_COMPLETE` | `"Complete"` |
| `STATUS_CANCELLED` | `"Cancelled"` |

In the model, define `STATUS_CHOICES = [(v, v) for v in (STATUS_SUBMITTED, STATUS_IN_PROGRESS, STATUS_SUSPENDED, STATUS_COMPLETE, STATUS_CANCELLED)]` (or explicit `[(STATUS_SUBMITTED, "Submitted"), ...]`) and use `choices=STATUS_CHOICES` on the `status` field. Initial create (Plan 6) will set `status=STATUS_SUBMITTED`.

**Conventions:**

- `__str__`: e.g. `"Signature transaction #<id> — Deal #<deal_id> — <status>"` or `"Deal #<deal_id> — <signix_document_set_id> — <status>"` so admin and shell are readable.
- **Meta:** `verbose_name = "Signature transaction"`, `verbose_name_plural = "Signature transactions"`. Ordering: e.g. `['-submitted_at']` so newest first.

**Relations:**

- **Deal:** `deal.signature_transactions` returns all SignatureTransactions for that deal. No change to Deal model file is required; the ForeignKey on SignatureTransaction defines the reverse relation.
- **DocumentSet:** `document_set` points to the set that was submitted. **on_delete=CASCADE** for strict referential integrity: if a DocumentSet is deleted, its signature transactions are deleted. We do not use SET_NULL so that every SignatureTransaction always has a valid document_set.

---

## 3. Migration and Checks

- **Migration:** Add `SignatureTransaction` to `apps/deals/models.py`, then run `python manage.py makemigrations deals` and `python manage.py migrate`.
- **Django check:** After migration, `python manage.py check` must pass. No new app or dependency; `documents.DocumentSet` is already in the project.

---

## 4. Usage (for Plan 6 and later)

- **Create (Plan 6 orchestrator):** `SignatureTransaction.objects.create(deal=deal, document_set=document_set, signix_document_set_id=..., transaction_id=..., status=SignatureTransaction.STATUS_SUBMITTED, first_signing_url=...)`. Using `auto_now_add=True` for `submitted_at` means you can omit `submitted_at` in `create()`.
- **Query by deal:** `SignatureTransaction.objects.filter(deal=deal).order_by('-submitted_at')` or `deal.signature_transactions.all()`.
- **Query all (dashboard, Plan 8):** `SignatureTransaction.objects.all().order_by('-submitted_at')` with `select_related('deal', 'document_set')` for list display.

---

## 5. Implementation Order (Checklist)

### Batch 1 — Model and migration (steps 1–3)

1. **Add SignatureTransaction to apps.deals**
   - In `apps/deals/models.py`, define status constants (`STATUS_SUBMITTED`, `STATUS_IN_PROGRESS`, `STATUS_SUSPENDED`, `STATUS_COMPLETE`, `STATUS_CANCELLED`) and `STATUS_CHOICES`. Define `SignatureTransaction` with all fields from Section 2 and use `choices=STATUS_CHOICES` on the status field. Use `related_name='signature_transactions'` on the Deal ForeignKey. Use `'documents.DocumentSet'` for the document_set ForeignKey (string to avoid circular import). Set `submitted_at` with `auto_now_add=True` so it is set on create.

2. **Migrations**
   - Run `python manage.py makemigrations deals --name add_signature_transaction` (or let Django generate the name).
   - Run `python manage.py migrate`.

3. **Verification (Batch 1)**
   - `python manage.py check` — no issues.
   - In shell: create a Deal and DocumentSet (or use existing), then `SignatureTransaction.objects.create(deal=deal, document_set=doc_set, signix_document_set_id='test-doc-set-1', status=SignatureTransaction.STATUS_SUBMITTED, first_signing_url='https://example.com/sign')`. Assert `t.deal_id`, `t.document_set_id`, `t.submitted_at` are set; `t.completed_at` is None. Query `deal.signature_transactions.all()` and confirm the instance is returned.

---

## 5a. Implementation Batches and Verification

**Batch 1 — Model and migration**

**Includes:** SignatureTransaction model in apps.deals with deal (CASCADE), document_set (CASCADE to documents.DocumentSet), signix_document_set_id, transaction_id, status, first_signing_url, submitted_at, completed_at. Migration created and applied.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — deals migration applied.
3. **Create and query:** In shell, get or create a Deal and a DocumentSet for that deal. Create a `SignatureTransaction` with required fields (deal, document_set, signix_document_set_id, status=SignatureTransaction.STATUS_SUBMITTED). Assert `submitted_at` is set, `completed_at` is None. Run `deal.signature_transactions.all()` and assert the new transaction is in the queryset.
4. **Reverse relation:** Prefetch or filter from Deal: `Deal.objects.prefetch_related('signature_transactions').get(pk=deal.pk)` and confirm `deal.signature_transactions.count() >= 1`.

Batch 1 is complete when the above pass.

---

## 6. File Summary

| Item | Value |
|------|--------|
| App | `apps.deals` |
| Model | `SignatureTransaction` (Section 2) |
| Migration | `apps/deals/migrations/0004_add_signature_transaction.py` (number may differ if Plan 1 added migrations; use `--name add_signature_transaction`) |
| Deal relation | `deal.signature_transactions` (reverse relation from SignatureTransaction.deal) |

---

## 7. Open Issues / Implementation Decisions

- **document_set on_delete:** **Decided:** Strict referential integrity — CASCADE. Every SignatureTransaction has a non-null document_set; deleting a DocumentSet deletes its signature transactions.
- **Status values:** **Decided:** The five allowed values are Submitted, In Progress, Suspended, Complete, Cancelled. Implement as model constants and `choices=STATUS_CHOICES` (Section 2).
- **transaction_id optional:** Design allows optional client-chosen TransactionID. Model uses **max_length=36** (UUID format per Design/Plan 5) and **blank=True** so Plan 6 can set it from build_submit_document_body metadata when present.
- **first_signing_url length:** 512 is used to accommodate long SIGNiX URLs; increase in a future migration if the API returns longer URLs.
- **Admin registration:** Optional. Register `SignatureTransaction` in `apps.deals.admin` for convenience during development if desired; not required by this plan.

---

## 8. Implementation Notes (from Plan 2 Batch 1)

- **Status constants on the model:** Define each of the five status values as a class attribute on `SignatureTransaction` (e.g. `STATUS_SUBMITTED = "Submitted"`) and build `STATUS_CHOICES` from them so that Plan 6 and templates can use `SignatureTransaction.STATUS_SUBMITTED` etc. without duplicating strings.
- **document_set ForeignKey:** Use the string `'documents.DocumentSet'` so Django resolves the app label and model without importing from `apps.documents` in `apps.deals.models` (avoids circular import). The `documents` app must be in `INSTALLED_APPS`.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-SIGNER-SERVICE.md (Plan 3).*

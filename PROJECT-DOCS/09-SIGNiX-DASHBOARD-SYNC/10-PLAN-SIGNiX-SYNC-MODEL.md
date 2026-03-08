# Plan: SIGNiX Sync Model (Dashboard/Sync Plan 1)

This plan adds the **model fields and status value** required for push-driven status and per-signer progress from DESIGN-SIGNiX-DASHBOARD-AND-SYNC. It does **not** add the push listener, any UI, or changes to the submit flow. Only schema and migrations so that Plan 2 (push listener) and Plan 3 (SubmitDocument with push URL) can use these fields.

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 7 (Data Model): SignatureTransaction (signer_count, signers_completed_refids, signers_completed_count, status_last_updated; **audit_trail_file**, **certificate_of_completion_file** per Section 7.4; Expired status); **Section 7.5 (SignatureTransactionEvent)** for event history; Section 7.3 (SignixConfig.push_base_url). PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md — Plan 1 deliverables.

**Prerequisites:** PHASE-PLANS-SIGNiX-SUBMIT plans 1–9 are implemented (SignixConfig, SignatureTransaction, dashboard, Deal View table). The app has `apps.deals` with `SignixConfig` and `SignatureTransaction` models.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **SignatureTransaction** — Add three fields for per-signer progress: **signer_count** (nullable), **signers_completed_refids** (list of strings), **signers_completed_count** (integer, default 0). Add **status_last_updated** (DateTimeField, nullable) so the dashboard can show when the current status was last updated (e.g. when the most recent signer completed, when the transaction was completed). Add **Expired** to the status choices so push handler and UI can set/display it. Add **audit_trail_file** and **certificate_of_completion_file** (FileField, blank=True, upload_to e.g. `"signature_transactions/%Y/%m/"`) so that when a transaction completes, Plan 5 can store the audit trail and certificate of completion PDFs on the transaction; Plan 6 (signature transaction detail page) then serves these already-stored files—no on-demand fetch when the user visits that page.
- **SignixConfig** — Add **push_base_url** (nullable) so the SubmitDocument body builder can include the push listener URL when set.
- **SignatureTransactionEvent** — New model (Section 7.5) for **event history** per transaction: so the signature transaction detail page can show a chronological timeline (Transaction submitted → push events → Transaction completed) and "when each signer signed" from party_complete events. Plan 2 creates an event for each push; Plan 3 creates the initial **submitted** event when the transaction is created.
- **Migrations** — One migration per model (or one combined migration for `deals`) so existing code and data remain valid; new fields are nullable or have defaults so existing rows and the current submit flow do not break. **Data migration assumption:** When we introduce push-driven status and per-signer progress, **all transactions that already exist are treated as complete with all signers having signed**. The backfill sets status=Complete, signer_count=2, signers_completed_count=2, signers_completed_refids=[], and completed_at/status_last_updated so the dashboard shows a consistent state; no legacy rows are left in Submitted or In Progress.
- **Out of scope this plan:** Push listener, SubmitDocument changes, dashboard Signers column, or download-on-complete. No views or URLs.

---

## 2. Model Changes

### 2.1 SignatureTransaction (apps.deals.models)

Add the following. Existing fields and relations are unchanged.

**New status constant and choices:**

- **STATUS_EXPIRED** — Add class attribute `STATUS_EXPIRED = "Expired"`.
- **STATUS_CHOICES** — Include the new value so that `STATUS_CHOICES` has six entries: Submitted, In Progress, Suspended, Complete, Cancelled, **Expired**. Update the list (or rebuild it) so that `status` field validation and admin/UI can use Expired.

**New fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `signer_count` | PositiveSmallIntegerField(null=True, blank=True) | Total number of signers at submit time. Set when the transaction is created (Plan 3). Null for transactions created before this field existed (legacy). |
| `signers_completed_refids` | JSONField(default=list) | List of strings (refid or pid) for each party that has completed. Used to avoid double-counting on partyComplete retries. Prefer refid when present; use pid when refid absent (handled in push listener). |
| `signers_completed_count` | PositiveSmallIntegerField(default=0) | Number of distinct parties that have completed (length of signers_completed_refids). Updated by push listener on partyComplete; optionally set to signer_count on action=complete. |
| `status_last_updated` | DateTimeField(null=True, blank=True) | When the status (or per-signer progress or completed_at) was last updated by the push listener. Set by apply_push_action whenever it mutates the transaction; enables dashboard "Status updated" column (when the most recent signer completed, when the transaction was completed). Null until first push update. |
| `audit_trail_file` | FileField(upload_to="signature_transactions/%Y/%m/", blank=True) | Populated by Plan 5 (download_signed_documents_on_complete) when the DownloadDocument response includes the audit trail PDF. Enables Plan 6 (signature transaction detail page) to offer "View audit trail" / "Download audit trail" from already-stored file; not fetched on demand when user visits the page. DESIGN Section 6.5a, 7.4. |
| `certificate_of_completion_file` | FileField(upload_to="signature_transactions/%Y/%m/", blank=True) | Populated by Plan 5 when the DownloadDocument response includes the certificate of completion PDF (optional in API request). Enables Plan 6 to offer "View certificate" / "Download certificate" when present. DESIGN Section 6.5a, 7.4. |

**Conventions:**

- **JSONField default:** Use `default=list` so new instances get an empty list. Do not use a mutable default on the class (e.g. avoid defining a module-level `[]` and passing it); Django’s JSONField with `default=list` is safe for new rows.
- **Existing rows:** After the schema migration, existing SignatureTransaction rows will have `signer_count=None`, `signers_completed_refids=[]` (or [] from default), `signers_completed_count=0`, `status_last_updated=None`. **A data migration** (RunPython) then backfills all such rows under the assumption that **all existing transactions are complete and all signers have signed**. For each row where `signer_count` is None: set **status** = STATUS_COMPLETE; set **signer_count** = 2, **signers_completed_count** = 2, **signers_completed_refids** = [] (no historical RefIDs; counts show "2/2"); set **completed_at** = existing completed_at if present, else submitted_at (so every backfilled row has a completed_at for display); set **status_last_updated** = **submitted_at**. Using **submitted_at** as the “last status update” for migrated rows is the intended design: we have no push history for those transactions, so the submit timestamp is the only meaningful “when status was last updated” value; the dashboard Status updated column then shows a consistent, logical date for every backfilled row. After the backfill, the dashboard shows all legacy transactions as Complete with 2/2 signers and a sensible Status updated value; no legacy rows remain in Submitted or In Progress.

### 2.2 SignixConfig (apps.deals.models)

Add one field:

| Field | Type | Purpose |
|-------|------|---------|
| `push_base_url` | CharField(max_length=512, blank=True, default="") or URLField(max_length=512, blank=True, default="") | Base URL for the push listener (e.g. `https://your-domain.ngrok-free.dev`). When set, SubmitDocument will include TransactionClientNotifyURL = push_base_url + "/signix/push/". When blank, client preferences are omitted (Plan 3 may add a fallback from settings/env). |

**Note:** Using `blank=True, default=""` (instead of `null=True`) keeps the field a non-null string and avoids NULL in the database; the packager treats empty string as “not set”. If you prefer nullable, use `null=True, blank=True` and check `if config.push_base_url:` in Plan 3.

---


### 2.3 SignatureTransactionEvent (apps.deals.models) — event history

New model for the **event timeline** on the signature transaction detail page (DESIGN Section 7.5).

| Field | Type | Purpose |
|-------|------|---------|
| `signature_transaction` | ForeignKey(SignatureTransaction, on_delete=CASCADE, related_name="events") | The transaction this event belongs to. |
| `event_type` | CharField(max_length=50) | One of: **submitted**, **send**, **party_complete**, **complete**, **suspend**, **cancel**, **expire**. **submitted** = app sent the transaction to SIGNiX (created in Plan 3); others = push notification received (created in Plan 2). |
| `occurred_at` | DateTimeField() | When the event occurred (from push `ts` or server time; for submitted = transaction.submitted_at). |
| `refid` | CharField(max_length=100, blank=True) | RefId from push when present (e.g. party_complete). Used to match "signed at" to signer position. |
| `pid` | CharField(max_length=100, blank=True) | Party ID from push when present (e.g. P01, P02). Used when refid is absent. |

**Meta:** ordering = ["occurred_at"] so the detail page can display events chronologically. No unique constraint required; duplicate events from push retries are acceptable (or Plan 2 can dedupe—see DESIGN 7.5).

**Creation:** Plan 2 (push listener) creates one event per push after saving the transaction. Plan 3 (submit) creates the **submitted** event when creating the SignatureTransaction.


## 3. Migration and Checks

- **Migrations:** After editing the models, run `python manage.py makemigrations deals` with a descriptive name (e.g. `add_signature_transaction_sync_fields` for the SignatureTransaction changes and `add_signix_config_push_base_url` for SignixConfig, or a single migration name if you prefer one migration). Then add a **data migration** that, for every `SignatureTransaction` where `signer_count` is None, applies the **existing-transactions-are-complete** assumption: set **status** = STATUS_COMPLETE, **signer_count** = 2, **signers_completed_count** = 2, **signers_completed_refids** = [], **completed_at** = existing completed_at if present else submitted_at, **status_last_updated** = **submitted_at**. Using submitted_at for status_last_updated is the intended design for migration: the last known “status update” for those rows is the submit time. Then run `python manage.py migrate`.
- **Django check:** After migration, `python manage.py check` must pass.
- **Existing code:** The submit flow (Plan 6 orchestrator) creates SignatureTransaction without the new fields; Django will set signer_count=None, signers_completed_refids=[], signers_completed_count=0 by default. No change to orchestrator in this plan. SignixConfig is loaded by get_signix_config(); existing callers do not need push_base_url until Plan 3.

---

## 4. Usage (for Plan 2, 3, 4, 5, 6)

- **Push listener (Plan 2):** Will update `status`, `signers_completed_refids`, `signers_completed_count`, `completed_at`, and **status_last_updated** on SignatureTransaction. Will use STATUS_EXPIRED for action=expire. Will **create a SignatureTransactionEvent** for each push (event_type from action, occurred_at from ts, refid/pid when present). **status_last_updated** is set whenever apply_push_action mutates the transaction (to the event time: push ts or now).
- **Orchestrator (Plan 3):** Will set `signer_count` when creating SignatureTransaction (e.g. `len(signer_order)`). Will read `SignixConfig.push_base_url` (or fallback) and pass it to build_submit_document_body. Will **create the initial SignatureTransactionEvent** (event_type=**submitted**, occurred_at=submitted_at). Will **mark document set versions as "Submitted to SIGNiX"** so the detail page can link to "document as sent."
- **Dashboard (Plan 4):** Will display `signers_completed_count` / `signer_count` (e.g. "1/2"); when `signer_count` is None, display "—" or "—/—". Will display **Status updated** from `status_last_updated` (formatted date/time; "—" when null).
- **Download on complete (Plan 5):** Will set `audit_trail_file` and `certificate_of_completion_file` when parsing the DownloadDocument response (DESIGN Section 6.5a). These fields remain blank until the transaction completes and the download flow runs.
- **Signature transaction detail (Plan 6):** Will display or serve `audit_trail_file` and `certificate_of_completion_file` when present; will display **events** (transaction.events.order_by("occurred_at")), **signers** (with signed at from party_complete events), and **documents** (as sent = version "Submitted to SIGNiX", signed = Final). No on-demand fetch—only already-stored files and existing data.

---

## 5. Implementation Order (Checklist)

### Batch 1 — SignatureTransaction fields and Expired (steps 1–4)

1. **Add STATUS_EXPIRED and update STATUS_CHOICES**
   - In `apps/deals/models.py`, add `STATUS_EXPIRED = "Expired"` after `STATUS_CANCELLED`. Update `STATUS_CHOICES` to include `(STATUS_EXPIRED, STATUS_EXPIRED)` so the status field accepts Expired.

2. **Add signer_count, signers_completed_refids, signers_completed_count, status_last_updated, audit_trail_file, certificate_of_completion_file**
   - On `SignatureTransaction`, add:
     - `signer_count = models.PositiveSmallIntegerField(null=True, blank=True)`
     - `signers_completed_refids = models.JSONField(default=list)`  # list of strings
     - `signers_completed_count = models.PositiveSmallIntegerField(default=0)`
     - `status_last_updated = models.DateTimeField(null=True, blank=True)`
     - `audit_trail_file = models.FileField(upload_to="signature_transactions/%Y/%m/", blank=True)`
     - `certificate_of_completion_file = models.FileField(upload_to="signature_transactions/%Y/%m/", blank=True)`
   - Place after `completed_at` so the model reads clearly. audit_trail_file and certificate_of_completion_file are populated by Plan 5 when the transaction completes (DESIGN Section 6.5a).

3. **Migration for SignatureTransaction**
   - Run `python manage.py makemigrations deals --name add_signature_transaction_sync_fields`.
   - Add a **data migration** (e.g. `backfill_signature_transaction_signer_counts`): in a RunPython forward function, for every `SignatureTransaction` where `signer_count` is None, apply the **existing-transactions-are-complete** assumption: set **status** = STATUS_COMPLETE; **signer_count** = 2; **signers_completed_count** = 2; **signers_completed_refids** = []; **completed_at** = row.completed_at if row.completed_at else row.submitted_at; **status_last_updated** = **row.submitted_at**. Using submitted_at for status_last_updated is the intended design: for migrated rows, the only meaningful “when status was last updated” is the submit time. Reverse can be a no-op or restore previous values.
   - Run `python manage.py migrate`.

4. **Verification (Batch 1)**
   - `python manage.py check` passes.
   - **Primary:** Run the unit tests for this plan (Section 5a / Section 6): `python manage.py test apps.deals.tests.test_sync_model.SignatureTransactionSyncFieldsTests` and `SignatureTransactionDataMigrationTests` (data migration backfill test). All must pass.
   - **Batch-scoped tests:** If `apps/deals/tests/test_sync_model.py` already contains Batch 2 or Batch 3 tests, keep Batch 1 verification clean by either (a) splitting the tests by batch/class and running only the Batch 1 classes, or (b) temporarily skipping future-batch test classes until their fields/models exist. Do not let a not-yet-implemented Batch 2/3 test block Batch 1 completion.
   - **Optional (shell):** Create a SignatureTransaction with the same args as today (deal, document_set, signix_document_set_id, status=STATUS_SUBMITTED). Assert `signer_count` is None, `signers_completed_refids == []`, `signers_completed_count == 0`, `status_last_updated` is None. Create another with `signer_count=2`, etc.; save and reload; assert values persist.
   - **Data migration:** For any existing SignatureTransaction rows that were present before the schema migration, after running migrations they should have **status** = Complete, **signer_count** = 2, **signers_completed_count** = 2, **signers_completed_refids** = [], **completed_at** set (to original completed_at or submitted_at), and **status_last_updated** set. Verify in shell or via the data-migration unit test (Section 6).

### Batch 2 — SignixConfig push_base_url (steps 5–7)

5. **Add push_base_url to SignixConfig**
   - In `apps/deals/models.py`, on `SignixConfig`, add:
     - `push_base_url = models.CharField(max_length=512, blank=True, default="")`
   - (Alternatively URLField if you prefer; CharField is sufficient for a URL string.) Place after submitter_phone or with other “settings” fields.

6. **Migration for SignixConfig**
   - Run `python manage.py makemigrations deals --name add_signix_config_push_base_url`.
   - Run `python manage.py migrate`.

7. **Verification (Batch 2)**
   - `python manage.py check` passes.
   - Run the unit tests for SignixConfig: `python manage.py test apps.deals.tests.test_sync_model.SignixConfigPushBaseUrlTests` (includes **test_signix_config_page_loads** when the config URL is available).
   - In shell: `from apps.deals.signix import get_signix_config; c = get_signix_config(); assert c.push_base_url == ""`. Set `c.push_base_url = "https://example.ngrok-free.dev"; c.save(); c.refresh_from_db(); assert c.push_base_url == "https://example.ngrok-free.dev"`.
   - **Optional:** Open SIGNiX Configuration in the browser (staff user). Page loads without error. In this codebase the existing route name is `signix_config`; the unit test can assert `GET reverse("signix_config")` returns 200 for an authenticated staff user.

### Batch 3 — SignatureTransactionEvent (steps 8–11)

8. **Add SignatureTransactionEvent model**
   - In `apps/deals/models.py`, add model per Section 2.3: signature_transaction (FK, related_name="events"), event_type (CharField), occurred_at (DateTimeField), refid (CharField, blank=True), pid (CharField, blank=True). Meta: ordering = ["occurred_at"].

9. **Migration for SignatureTransactionEvent**
   - Run `python manage.py makemigrations deals --name add_signature_transaction_event`.
   - Run `python manage.py migrate`.

10. **Verification (Batch 3)**
   - `python manage.py check` passes.
   - Run unit tests: `python manage.py test apps.deals.tests.test_sync_model.SignatureTransactionEventTests` — all pass (Section 6).
   - **Broader regression check (recommended):** Because Batch 3 is additive in this codebase and no existing view/service depends on `transaction.events` yet, it is reasonable to run the broader existing suite (e.g. `python manage.py test apps.deals.tests` or the full project suite) after the migration to confirm the new model does not regress existing dashboard/send flows.
   - **Optional (shell):** Create a SignatureTransaction, then create a SignatureTransactionEvent(transaction, event_type="submitted", occurred_at=timezone.now()); save; assert transaction.events.count() == 1 and transaction.events.first().event_type == "submitted".

11. **No event backfill in Plan 1** — Existing transactions are not backfilled with events; the detail page (Plan 6) will show events only for transactions that receive the submitted event (Plan 3) and push events (Plan 2). Legacy rows will have an empty events list.

---

## 5a. Implementation Batches and Verification

Implement in **three batches**. After each batch, run the verification steps and the tests listed.

### Batch 1 — SignatureTransaction: Expired status and per-signer fields

**Includes:** STATUS_EXPIRED constant; STATUS_CHOICES updated to include Expired; signer_count (null=True, blank=True); signers_completed_refids (JSONField, default=list); signers_completed_count (default=0); **status_last_updated** (DateTimeField, null=True, blank=True); **audit_trail_file** and **certificate_of_completion_file** (FileField, blank=True, upload_to="signature_transactions/%Y/%m/"). Migration `add_signature_transaction_sync_fields` (or equivalent name). **Data migration** `backfill_signature_transaction_signer_counts` (or equivalent): for every row where signer_count is None, apply the **existing-transactions-are-complete** assumption — set **status** = STATUS_COMPLETE, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at=(existing completed_at or submitted_at), **status_last_updated=submitted_at** (so the dashboard Status updated column shows a consistent value for migrated rows).

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — new deals migration applied.
3. **Unit tests (primary):** `python manage.py test apps.deals.tests.test_sync_model.SignatureTransactionSyncFieldsTests apps.deals.tests.test_sync_model.SignatureTransactionDataMigrationTests` — all tests pass.
4. **Batch-scoped test hygiene:** If the same module already includes Batch 2 (`SignixConfigPushBaseUrlTests`) or Batch 3 (`SignatureTransactionEventTests`) tests, run only the Batch 1 classes above or skip the future-batch classes until their implementation lands.
5. **Optional — Shell, defaults:** Create a `SignatureTransaction` with only the required fields (deal, document_set, signix_document_set_id, status=SignatureTransaction.STATUS_SUBMITTED). Assert `tx.signer_count is None`, `tx.signers_completed_refids == []`, `tx.signers_completed_count == 0`, `tx.status_last_updated is None`.
6. **Optional — Shell, Expired:** Set `tx.status = SignatureTransaction.STATUS_EXPIRED` and `tx.save()`. Reload; assert `tx.status == SignatureTransaction.STATUS_EXPIRED`. Confirm STATUS_EXPIRED is in `SignatureTransaction.STATUS_CHOICES`.
7. **Optional — Shell, optional fields set:** Create a transaction with `signer_count=2`, `signers_completed_refids=["P01"]`, `signers_completed_count=1`, `status_last_updated=timezone.now()`. Save, reload from DB; assert values persist.
8. **Data migration verification:** Run the unit test **test_backfill_sets_complete_and_signer_counts** (Section 6). If the database had existing SignatureTransaction rows before the schema migration, after running migrations those rows should have **status** = Complete, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at set, status_last_updated set. The test verifies the backfill logic; production verification can be done in shell or DB.

### Batch 1 is complete when the above pass.

### Batch 2 — SignixConfig.push_base_url

**Includes:** push_base_url field on SignixConfig (CharField max_length=512, blank=True, default=""). Migration `add_signix_config_push_base_url` (or equivalent).

**How to test after Batch 2:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — migration applied.
3. **Unit tests:** `python manage.py test apps.deals.tests.test_sync_model.SignixConfigPushBaseUrlTests` — all tests pass (includes **test_signix_config_page_loads** if the config view is registered).
4. **Shell — get_signix_config:** `c = get_signix_config()`; assert `c.push_base_url == ""`. Set `c.push_base_url = "https://test.ngrok-free.dev"`, save, refresh; assert value persists.
5. **Optional — Config page:** Open SIGNiX Configuration in the browser (staff user). Page loads without error. The unit test can assert GET to the config URL returns 200 for an authenticated staff user.

Batch 2 is complete when the above pass.

### Batch 3 — SignatureTransactionEvent

**Includes:** SignatureTransactionEvent model (Section 2.3); migration `add_signature_transaction_event`. No data backfill for existing transactions.

**How to test after Batch 3:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — migration applied.
3. **Unit tests:** `python manage.py test apps.deals.tests.test_sync_model.SignatureTransactionEventTests` — all pass (Section 6).
4. **Broader regression check (recommended):** Run `python manage.py test apps.deals.tests` (or the full suite) to confirm the additive model change does not affect existing dashboard/send flows.
5. **Optional (shell):** Create a SignatureTransaction (or use existing). Create SignatureTransactionEvent(signature_transaction=tx, event_type="submitted", occurred_at=timezone.now()). Save. Assert tx.events.count() == 1, tx.events.first().event_type == "submitted".

Batch 3 is complete when the above pass.

---

## 6. Unit Tests (add to apps.deals.tests)

Create **apps/deals/tests/test_sync_model.py** with the following test classes. These tests assert that the new fields and status exist and behave as expected.

**SignatureTransactionSyncFieldsTests:**

- **test_expired_status_constant_exists** — Assert `SignatureTransaction.STATUS_EXPIRED == "Expired"`.
- **test_status_choices_include_expired** — Assert "Expired" appears in the choice values (e.g. `[c[0] for c in SignatureTransaction.STATUS_CHOICES]` contains `STATUS_EXPIRED`).
- **test_create_without_sync_fields_uses_defaults** — Create a SignatureTransaction with only required fields (deal, document_set, signix_document_set_id, status=STATUS_SUBMITTED). Assert signer_count is None, signers_completed_refids == [], signers_completed_count == 0, status_last_updated is None.
- **test_create_with_sync_fields_persists** — Create with signer_count=2, signers_completed_refids=["P01", "P02"], signers_completed_count=2, status_last_updated=timezone.now(). Save, reload from DB; assert all four fields match.
- **test_status_expired_can_be_saved** — Create a transaction, set status=SignatureTransaction.STATUS_EXPIRED, save; reload and assert status == STATUS_EXPIRED.

**SignixConfigPushBaseUrlTests:**

- **test_push_base_url_default_blank** — get_signix_config(); assert config.push_base_url == "" (or None if you used null=True).
- **test_push_base_url_persists** — get_signix_config(); set push_base_url to a test URL; save(); refresh_from_db(); assert push_base_url equals the test URL.
- **test_signix_config_page_loads** — (Optional, requires config URL.) As an authenticated staff user, GET the SIGNiX Configuration page URL (in this codebase: `reverse("signix_config")`). Assert response.status_code == 200 and that the response contains the config form or "SIGNiX Configuration" so the page renders after Batch 2.

**SignatureTransactionDataMigrationTests:**

- **test_backfill_sets_complete_and_signer_counts** — Extract the data-migration backfill logic into a small helper (e.g. `backfill_signature_transaction_signer_counts_for_row(transaction)` or run it for a queryset). Create a SignatureTransaction with signer_count=None, status=STATUS_SUBMITTED, submitted_at=timezone.now(). Call the backfill helper for that row (or the same logic the migration uses). Assert: status == STATUS_COMPLETE, signer_count == 2, signers_completed_count == 2, signers_completed_refids == [], completed_at is set (to submitted_at when completed_at was None), status_last_updated == transaction.submitted_at. This verifies the backfill behavior that the data migration applies to existing rows; the migration’s RunPython can call the same helper.

**SignatureTransactionEventTests:**

- **test_create_event_and_related_name** — Create a SignatureTransaction, then create a SignatureTransactionEvent(signature_transaction=tx, event_type="submitted", occurred_at=timezone.now()). Save. Assert tx.events.count() == 1, tx.events.first().event_type == "submitted".
- **test_events_ordered_by_occurred_at** — Create a transaction and two events with different occurred_at (e.g. t1, t2 with t1 < t2). Save. Assert list(tx.events.values_list('event_type', flat=True)) is in chronological order (e.g. ["send", "party_complete"]).
- **test_event_type_submitted** — Create event with event_type="submitted". Assert event.event_type == "submitted" and event.signature_transaction_id == tx.pk.

Use the same test setup as other deals tests (e.g. create Deal, DocumentSet, User as needed). For SignixConfig tests, use get_signix_config() from apps.deals.signix so the singleton exists.

**Batch-scoped test organization:** Because this plan is implemented in three batches, it is acceptable to keep all test classes in one module **only if** future-batch classes are skipped until their implementation exists. Alternatively, split them into separate modules (`test_sync_model_batch1.py`, `test_sync_model_batch2.py`, etc.). The important rule is that **Batch 1 can be verified cleanly on its own** without being blocked by Batch 2/3 expectations.

---

## 7. File Summary

| Item | Value |
|------|--------|
| App | `apps.deals` |
| Models modified | `SignatureTransaction` (Section 2.1), `SignixConfig` (Section 2.2), **`SignatureTransactionEvent`** (Section 2.3, new model) |
| Migrations | `add_signature_transaction_sync_fields`, **`backfill_signature_transaction_signer_counts`** (data migration), `add_signix_config_push_base_url`, **`add_signature_transaction_event`** (names may vary; use `makemigrations --name ...`; data migration can be created with `makemigrations --empty deals --name backfill_signature_transaction_signer_counts` then add RunPython) |
| Tests | `apps/deals/tests/test_sync_model.py` — SignatureTransactionSyncFieldsTests, SignixConfigPushBaseUrlTests, **SignatureTransactionDataMigrationTests**, **SignatureTransactionEventTests** |

---

## 8. Open Issues / Implementation Decisions

- **push_base_url: null vs blank:** Design says “nullable”; this plan allows either `null=True, blank=True` or `blank=True, default=""`. Using a non-null default (`default=""`) avoids NULL in the database and keeps the type a string. Plan 3 will check `if config.push_base_url:` (or `if getattr(config, 'push_base_url', None):`) before adding ClientPreference elements. **Decided:** Use `blank=True, default=""` so the column is NOT NULL; no migration data backfill needed.
- **JSONField default=list:** Django’s JSONField with `default=list` is safe: each new instance gets a new list. Do not use a module-level list as default.
- **Admin:** Optional. If SignatureTransaction or SignixConfig is registered in admin, the new fields will appear automatically. **push_base_url** need not be in the SignixConfig admin form for typical use: the app will use get_push_base_url(request) (Plan 3; DESIGN Section 5.4) for both submit and the config form display. Add push_base_url to the admin only as an optional override. When the config form is shown, pass get_push_base_url(request) to the template and display it next to the field (e.g. “When blank, app will use: &lt;derived&gt;/signix/push/”) so the user sees the effective default.
- **Existing config page behavior:** In this codebase, the SIGNiX config page already exists and uses `SignixConfigForm` with an explicit `Meta.fields` list. That means adding `push_base_url` to the model in **Batch 2** does **not** expose it on the page automatically, which is desirable for this batch: the page continues to render unchanged, and **Plan 3** must intentionally add `push_base_url` to the form and template when the UI is ready.
- **Order of migrations:** Batch 1, Batch 2, and **Batch 3 are kept separate** so you can verify SignatureTransaction first, then SignixConfig, then SignatureTransactionEvent. Optionally combine into fewer migrations if you prefer; the plan describes three batches for clear verification steps. **Decided:** Implement as three batches; do not combine Batch 3 with Batch 1 for the initial implementation.
- **Existing transactions = complete, all signers signed:** When we introduce push-driven status and per-signer progress (Plan 1), any transaction that already exists in the database is treated as **complete** with **all signers having signed**. The data migration sets status=STATUS_COMPLETE, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at (to existing completed_at or submitted_at), and **status_last_updated = submitted_at**. Using **submitted_at** as the “last status update” for migrated rows is the intended design (we have no push history for those transactions), so the dashboard Status updated column shows a consistent, logical value. **Decided:** Implement as specified in Section 2.1 (Conventions) and the data migration steps above.
- **Batch 3 impact on existing code:** In this codebase, `SignatureTransactionEvent` is a clean additive model change: existing dashboard, deal-detail, and SIGNiX submit flows do not reference `transaction.events` yet. That makes Batch 3 a good point to run the broader existing test suite after the migration, even before Plans 2/3 start creating event rows.

---

## 9. Implementation Notes

- **STATUS_CHOICES:** Rebuild the list so it includes Expired, e.g. `STATUS_CHOICES = [(c, c) for c in (STATUS_SUBMITTED, STATUS_IN_PROGRESS, STATUS_SUSPENDED, STATUS_COMPLETE, STATUS_CANCELLED, STATUS_EXPIRED)]` or append `(STATUS_EXPIRED, STATUS_EXPIRED)` to the existing list. Ensure the status field’s `choices=STATUS_CHOICES` still applies.
- **Existing SignatureTransaction rows:** After the schema migration, existing rows will have signer_count=None (or NULL), signers_completed_refids=[] (if default=list is applied—check Django’s behavior for JSONField default), signers_completed_count=0, status_last_updated=None. The **data migration** (RunPython) then applies the **existing-transactions-are-complete** assumption: for every row where signer_count is None, set status=STATUS_COMPLETE, signer_count=2, signers_completed_count=2, signers_completed_refids=[], completed_at=(existing completed_at or submitted_at), status_last_updated=submitted_at. Using submitted_at for status_last_updated is the intended design: for those rows, the only meaningful "last status update" timestamp is the submit time, so the dashboard Status updated column shows a consistent value. That way all legacy transactions appear as Complete with 2/2 signers and a sensible Status updated; no legacy rows remain in Submitted or In Progress. If the migration does not set signers_completed_refids for existing rows (e.g. JSONField default), ensure the app treats None as [] where needed (e.g. in Plan 4 display: `refids = getattr(tx, 'signers_completed_refids', None) or []`).
- **SignixConfig form:** Plan 3 adds **get_push_base_url(request=None)** in `apps.deals.signix` and uses it for both submit and the config form. Add push_base_url to the SIGNiX Configuration form as an optional override. When the form is rendered, pass **get_push_base_url(request)** to the template and display it next to the field (e.g. “When blank, app will use: &lt;result&gt;/signix/push/”). This plan only adds the model field; the config page may show the field (with derived default via helper) in Plan 3—optional.

---

*End of plan. Proceed to implementation only after review. Next: 20-PLAN-SIGNiX-PUSH-LISTENER.md (Plan 2).*

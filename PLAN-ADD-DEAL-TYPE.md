# Plan: Add Deal Type

This document outlines how to add **Deal Type** to the Django lease application. Deal Type classifies deals (e.g., lease, cash purchase) and determines which Document Set Template is used when generating documents. The initial release has exactly one Deal Type: "Lease - Single Signer". All deals default to this type. No UI for the user to select deal type.

**Design reference:** DESIGN-DOCS.md — Document Set Templates, Deal Type Association, and Deal Type (initial release) in Decisions Log.

**Prerequisites:** PLAN-MASTER plans 1–5 implemented (Baseline, Vehicles, Contacts, Deals, Images). This plan modifies the existing Deal model in `apps.deals`.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** `DealType` with `name` (e.g., "Lease - Single Signer").
- **Deal model:** Add `deal_type` FK to `DealType`. All deals have a deal type; new and existing deals default to "Lease - Single Signer".
- **Data:** One initial Deal Type "Lease - Single Signer" created by migration 1 (optional management command for manual setup).
- **UI:** No Deal Type list/add/edit pages. No deal_type field on Deal add/edit forms. Deal type is set automatically; user does not select it.
- **Access:** N/A (no new user-facing pages).

---

## 2. Model and Storage

- **App:** Add `DealType` to existing `apps.deals`.
- **Persistence:** SQLite (existing database).
- **Model:** `DealType`
  - `name` — `CharField`, max_length=100, unique. Human-readable (e.g., "Lease - Single Signer").
  - Conventions: Docstrings, `__str__` (return `name`), `verbose_name` / `verbose_name_plural` in `Meta`.

- **Deal model change:** Add `deal_type` — `ForeignKey(DealType, on_delete=models.PROTECT, null=True, blank=True)`. Use `null=True` for migration flexibility; the app ensures it is always set (see Section 5). `PROTECT` prevents deleting a DealType that is in use.

---

## 3. Seed Data

One Deal Type for initial release:

| Field | Value |
|-------|--------|
| name  | Lease - Single Signer |

**Implementation:** The default DealType is created by **migration 1** (RunPython) so that `migrate` is self-contained—no seed command need run between migrations. A management command `setup_initial_deal_type` is also provided for manual setup or idempotent "ensure exists"; it is optional.

---

## 4. Pages and Behavior

No new pages. Deal add/edit forms are unchanged from the user's perspective. The `deal_type` field is not shown in forms.

- **Deal add:** View sets `instance.deal_type` to the default DealType before saving.
- **Deal edit:** `deal_type` is not displayed or changed.
- **Existing deals:** Migration assigns the default DealType to any Deal with `deal_type` null.

---

## 5. Default Deal Type Logic

- **Helper:** Add `DealType.get_default()` (class method) that returns the "Lease - Single Signer" instance, creating it if necessary (`get_or_create`).
- **Deal add view:** Before saving a new Deal, set `instance.deal_type = DealType.get_default()`.
- **Deal model `save()`:** If `deal_type_id` is None, set `deal_type = DealType.get_default()`. Ensures any Deal created outside the add view (e.g., admin, shell) also gets the default.

---

## 6. Migration Strategy

1. **Migration 1:** Create `DealType` model and add `RunPython` to create "Lease - Single Signer" if it does not exist. Single `migrate` run is self-contained—no seed between migrations.
2. **Migration 2:** Add `deal_type` to `Deal` with `null=True`, `blank=True`.
3. **Migration 3 (data migration):** RunPython to set `Deal.objects.filter(deal_type__isnull=True).update(deal_type=<default>)`. Use `apps.get_model` for historical models.

---

## 7. Implementation Order (Checklist)

### Batch 1 — Data layer (steps 1–5)

1. **DealType model**
   - In `apps/deals/models.py`, add `DealType` with `name` (CharField, max_length=100, unique). Add `__str__` and `Meta` verbose names.
   - Add class method `DealType.get_default()` that returns `DealType.objects.get_or_create(name="Lease - Single Signer")[0]`.

2. **Migration 1**
   - Run `python manage.py makemigrations deals --name add_dealtype`.
   - Edit the migration: add `RunPython` operation after `CreateModel(DealType)` that creates "Lease - Single Signer" if it does not exist. Use `apps.get_model('deals', 'DealType')` and `get_or_create(name="Lease - Single Signer")`.
   - Run `python manage.py migrate`. The default DealType is created automatically—no seed between migrations.

3. **Seed command (optional)**
   - Create `apps/deals/management/commands/setup_initial_deal_type.py`. Use `get_or_create(name="Lease - Single Signer")`; idempotent. For manual setup or ensuring the default exists; not required for migrations.

4. **Deal.deal_type field**
   - Add `deal_type = models.ForeignKey(DealType, on_delete=models.PROTECT, null=True, blank=True, related_name="deals")` to `Deal`.
   - Run `python manage.py makemigrations deals --name add_deal_deal_type`.

5. **Data migration**
   - Run migrations. Create a data migration: `python manage.py makemigrations deals --empty --name backfill_deal_type`.
   - Edit the migration: add `RunPython` that gets `Deal` and `DealType`, gets default DealType, updates `Deal.objects.filter(deal_type__isnull=True)`.
   - Run `python manage.py migrate`.

Batch 1 complete when DealType exists (created by migration), and all Deals have a `deal_type` set.

### Batch 2 — Integration (steps 6–8)

6. **Deal model save**
   - Override `Deal.save()`: if `self.deal_type_id is None`, set `self.deal_type = DealType.get_default()`. Call `super().save()`.

7. **Deal add view**
   - In the deal add view (POST handler), before `form.save()`: if creating (not editing), set `instance.deal_type = DealType.get_default()`. Ensure the form's `instance` gets this before save (e.g., `instance = form.save(commit=False)` then `instance.deal_type = DealType.get_default()` then `instance.save()`).

8. **Admin (optional)**
   - Register `DealType` in `apps/deals/admin.py` for visibility. No sidebar link.

9. **Verification**
   - Shell: create a Deal without setting deal_type; confirm it gets the default. UI: add a deal via the form; confirm deal_type is set. List/edit deals; no regression.

---

## 7a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps.

### Batch 1 — Data layer (steps 1–5)

**Includes:** DealType model, migrations (with default creation in migration 1), optional seed command, Deal.deal_type field, data migration.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.

2. **Migrations:** `python manage.py migrate` — DealType table exists, Deal has deal_type column.

3. **Default DealType exists (from migration 1):**
   ```python
   from apps.deals.models import DealType
   dt = DealType.objects.get(name="Lease - Single Signer")
   assert dt is not None
   ```

4. **Idempotent seed (optional):** Run `python manage.py setup_initial_deal_type`; no duplicate. `DealType.objects.count() == 1`.

5. **Data migration — existing deals have deal_type:**
   ```python
   from apps.deals.models import Deal, DealType
   assert Deal.objects.filter(deal_type__isnull=True).count() == 0
   # If there were Deals before migration, they should now have deal_type set
   for d in Deal.objects.all():
       assert d.deal_type.name == "Lease - Single Signer"
   ```

6. **get_default:**
   ```python
   from apps.deals.models import DealType
   dt = DealType.get_default()
   assert dt.name == "Lease - Single Signer"
   ```

Batch 1 complete when the above pass.

### Batch 2 — Integration (steps 6–9)

**Includes:** Deal.save() default, deal add view sets deal_type, optional admin.

**How to test after Batch 2:**

1. **Shell — new Deal gets default via save():**
   ```python
   from django.contrib.auth import get_user_model
   from apps.deals.models import Deal, DealType
   from decimal import Decimal
   from datetime import date

   User = get_user_model()
   user = User.objects.first()
   d = Deal(
       lease_officer=user,
       date_entered=date.today(),
       lease_start_date=date.today(),
       lease_end_date=date(2026, 12, 31),
       payment_amount=Decimal("100.00"),
   )
   d.save()  # deal_type not set; save() should set it
   assert d.deal_type_id is not None
   assert d.deal_type.name == "Lease - Single Signer"
   d.delete()  # clean up
   ```

2. **UI — add deal via form:** Log in, go to Deals, Add deal. Fill required fields, submit. In shell: `Deal.objects.latest('id').deal_type.name == "Lease - Single Signer"`.

3. **UI — edit deal:** Edit an existing deal; save. Deal type should remain unchanged. No deal_type field visible on form.

4. **Deal form:** Confirm `DealForm.Meta.fields` does not include `deal_type`.

5. **Admin (if registered):** Visit `/admin/deals/dealtype/`; see "Lease - Single Signer".

Batch 2 complete when all of the above pass.

---

## 8. File and URL Summary

| Item   | Value |
|--------|-------|
| App    | `apps.deals` |
| Model  | `DealType(name)` |
| Change | `Deal.deal_type` FK to DealType |
| Seed   | Optional: `python manage.py setup_initial_deal_type` (default created by migration 1) |
| Nav    | No new sidebar link |
| UI     | No deal_type field on Deal forms |

---

## 9. Out of Scope (This Phase)

- Deal Type list/add/edit UI (future: when multiple types exist).
- Deal type selector on Deal add/edit form (future).
- Document Set Templates (separate plan; will reference DealType).
- Pagination or search on DealType (only one record in initial release).

---

*End of plan. Proceed to implementation only after review.*

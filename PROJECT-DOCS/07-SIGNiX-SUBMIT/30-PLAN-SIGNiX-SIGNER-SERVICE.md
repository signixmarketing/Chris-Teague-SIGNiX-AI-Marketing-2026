# Plan: Signer Service (Plan 3)

This document outlines how to add the **signer identification** and **slot→person resolution** service layer used by the Signers table (Plan 4) and the transaction packager (Plans 5–6). There is no UI in this plan—only the two service functions and unit tests.

**Design reference:** [DESIGN-SIGNiX-SUBMIT.md](DESIGN-SIGNiX-SUBMIT.md) — Section 5.3 (Signers derived from document set template), Section 5.1 (Signers MemberInfo example mapping), Section 6.1.1 (MemberInfo data sourcing). [PHASE-PLANS-SIGNiX-SUBMIT.md](PHASE-PLANS-SIGNiX-SUBMIT.md) — Plan 3 deliverables.

**Prerequisites:** [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) plans 1–4 and PHASE-PLANS-DOCS plans 1–4 are implemented. The app has Deals, Contacts, Document Set Templates, DocumentSetTemplateItem (GenericForeignKey to Static/Dynamic templates), and both template types with `tagging_data` containing `member_info_number`. LeaseOfficerProfile (User profile) exists per [01-BASELINE/10-PLAN-BASELINE.md](../01-BASELINE/10-PLAN-BASELINE.md). No dependency on SignixConfig or SignatureTransaction.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **`get_signers_for_document_set_template(document_set_template)`** — Given a DocumentSetTemplate, return an ordered list of signer slot numbers (e.g. `[1, 2]`) by scanning each template in the set and collecting distinct `member_info_number` values from their `tagging_data`. Used by Deal View (Signers table) and the packager to know how many signers exist and which slots to resolve.
- **Slot→person resolution** — Given a deal and a slot number (1, 2, …), return the person’s data (first_name, middle_name, last_name, email, phone) for that slot, or `None` if the slot cannot be resolved (e.g. slot 2 but deal has no contacts). Convention: slot 1 = lease officer (User + LeaseOfficerProfile); slot 2 = first contact (`deal.contacts` ordered by id). Same convention used by the Signers table and the packager.
- **Module location:** `apps.deals.signix`. Create `apps/deals/signix.py` if it does not already exist (e.g. if Plan 3 is implemented before Plan 1). Plan 1 adds `get_signix_config()` in the same module.
- **Out of scope:** No UI, no signer order or authentication storage (Plan 4), no SubmitDocument building or sending.

---

## 2. get_signers_for_document_set_template

- **Signature:** `get_signers_for_document_set_template(document_set_template) -> list[int]`
- **Input:** A `DocumentSetTemplate` instance (e.g. the one for the deal’s deal type or `document_set.document_set_template`).
- **Behavior:**
  1. For each item in `document_set_template.items.all()` (in order), resolve the template via the item’s GenericForeignKey (`item.template` → StaticDocumentTemplate or DynamicDocumentTemplate).
  2. Read `tagging_data` from each template (a list of dicts). From each dict that has a `member_info_number` key with an integer value, collect that value.
  3. Return an **ordered list of unique** signer slot numbers, e.g. `[1, 2]`. Order: **numeric ascending** (1, 2, 3, …) so the list is stable and matches SIGNiX MemberInfo ordering.
- **Edge cases:** If the template has no items or no `member_info_number` in any tagging_data, return `[]`. **If `document_set_template` is None,** the function accepts it and returns `[]` so callers need not check. If an item’s template is missing or the GenericForeignKey resolves to a wrong type, **skip that item** (collect no member_info_number from it); do not raise.
- **Dependencies:** `doctemplates` app (DocumentSetTemplate, DocumentSetTemplateItem, StaticDocumentTemplate, DynamicDocumentTemplate). No SIGNiX or deals signix config.

---

## 3. Slot→person resolution

- **Convention (current):**
  - **Slot 1** — Lease officer: `deal.lease_officer` (User). Name and email from **LeaseOfficerProfile** if present (`first_name`, `last_name`, `email`, `phone_number`); `middle_name` is not on profile, use `""`. **If no profile,** fall back to User: split `user.get_full_name()` — first word = `first_name`, remainder (trimmed) = `last_name`; if `get_full_name()` is empty or blank, use `first_name=user.get_username()`, `last_name=""`. Email from `user.email`; phone from profile if present, else `""`.
  - **Slot 2** — First contact: first contact in `deal.contacts.order_by("id")`. Use Contact fields: `first_name`, `middle_name`, `last_name`, `email`, `phone_number`.
  - **Slot 3 and beyond** — Not in current convention; return `None`. Extend in a later release (e.g. second contact for slot 3) if needed.

- **Return shape:** A simple structure so Plan 4 and Plan 5 can consume it. Use a **dataclass** or **typed dict** with: `first_name`, `middle_name`, `last_name`, `email`, `phone`. All strings; use `""` for missing optional values. When the slot cannot be resolved, return **`None`** (caller validates that all required slots resolve before submit).

- **Signature:** `resolve_signer_slot(deal, slot_number) -> SignerPerson | None`

  Define a small type, e.g.:

  ```python
  class SignerPerson:
      first_name: str
      middle_name: str
      last_name: str
      email: str
      phone: str
  ```

  (Use a dataclass, named tuple, or dict with consistent keys; tests and packager will use the same shape.)

- **Dependencies:** `apps.deals` (Deal), `apps.contacts` (Contact), `apps.users` (LeaseOfficerProfile). Deal must have `lease_officer` and `contacts` (M2M) loaded; use `select_related("lease_officer")` and `prefetch_related("contacts")` when calling from views if needed.

---

## 4. Module layout: apps.deals.signix

- **File:** `apps/deals/signix.py`.
- **Contents:**
  - `SignerPerson` (dataclass or similar) with fields above.
  - `get_signers_for_document_set_template(document_set_template)`.
  - `resolve_signer_slot(deal, slot_number)`.
- **Imports:** `signix.py` does not import doctemplates, Contact, LeaseOfficerProfile, or User; it uses `getattr` on the document_set_template, deal, and related instances passed in. Plan 1’s `get_signix_config` only needs `SignixConfig` from `apps.deals.models`. This avoids circular imports; callers pass in instances with relations loaded as needed.

- **Optional:** If Plan 1 already added `get_signix_config()` in this file, append the signer functions to the same module. Do not duplicate `get_signix_config` in this plan.

---

## 5. Implementation Order (Checklist)

### Batch 1 — get_signers_for_document_set_template (steps 1–3)

1. **Implement get_signers_for_document_set_template**
   - In `apps/deals/signix.py` (create file if missing), implement the function per Section 2. Iterate `document_set_template.items.all()`, resolve each item’s template (Static or Dynamic), collect `member_info_number` from each entry in `tagging_data` that has that key with an int value. Return sorted unique list of integers.
   - Handle missing or malformed `tagging_data` (e.g. not a list, or entries without member_info_number) without raising; only collect valid integers.

2. **Unit tests (Batch 1)**
   - Test: DocumentSetTemplate with no items → `[]`.
   - Test: One Static template with tagging_data `[{"member_info_number": 1}, {"member_info_number": 2}]` → `[1, 2]`.
   - Test: Two templates (Static + Dynamic), each with member_info_number 1 and 2 → `[1, 2]` (unique, sorted).
   - Test: tagging_data with non-int or missing member_info_number → those entries ignored, others collected.
   - Test: Empty tagging_data → `[]`.
   - Test: `document_set_template` is None → `[]`.

3. **Verification (Batch 1)**
   - Run tests. `get_signers_for_document_set_template` returns correct slots for a fixture template.

### Batch 2 — Slot→person resolution (steps 4–6)

4. **Define SignerPerson and resolve_signer_slot**
   - In `apps/deals/signix.py`, define `SignerPerson` (dataclass with first_name, middle_name, last_name, email, phone).
   - Implement `resolve_signer_slot(deal, slot_number)`. Slot 1: lease officer from deal.lease_officer + LeaseOfficerProfile (or User fallback). Slot 2: first contact from deal.contacts.order_by("id").first(). Slot > 2: return None. Return None if slot 1 but no lease_officer, or slot 2 but no contacts.

5. **Unit tests (Batch 2)**
   - Test: Deal with lease_officer and LeaseOfficerProfile → slot 1 returns SignerPerson with profile first_name, last_name, email, phone; middle_name "".
   - Test: Deal with lease_officer but no LeaseOfficerProfile → slot 1 returns SignerPerson using User (get_full_name or username, email).
   - Test: Deal with one contact → slot 2 returns SignerPerson with contact’s first_name, middle_name, last_name, email, phone_number.
   - Test: Deal with no contacts → slot 2 returns None.
   - Test: Deal with no lease_officer → slot 1 returns None (if deal allows null lease_officer; otherwise skip).
   - Test: slot 3 returns None (or extend convention later).

6. **Verification (Batch 2)**
   - Run tests. For a deal with lease officer and one contact, `get_signers_for_document_set_template(template)` returns `[1, 2]` and `resolve_signer_slot(deal, 1)` and `resolve_signer_slot(deal, 2)` return the expected SignerPerson instances.

---

## 5a. Implementation Batches and Verification

**Batch 1 — get_signers_for_document_set_template and tests**

**Includes:** Function in `apps.deals.signix`; unit tests that assert slot list from DocumentSetTemplate items and tagging_data (empty, single template, multiple templates, unique/sorted, malformed data).

**How to test after Batch 1:**

1. Create a DocumentSetTemplate with one or two items (Static and/or Dynamic) and tagging_data containing member_info_number 1 and 2. Call `get_signers_for_document_set_template(template)`; assert result is `[1, 2]`.
2. Run pytest (or Django test) for the new tests. All pass.

**Batch 2 — resolve_signer_slot and SignerPerson, tests**

**Includes:** SignerPerson type, `resolve_signer_slot(deal, slot_number)` in `apps.deals.signix`; unit tests for slot 1 (with/without profile), slot 2 (with/without contact), slot 3 → None.

**How to test after Batch 2:**

1. Create a Deal with lease_officer (User with LeaseOfficerProfile) and one Contact. Call `resolve_signer_slot(deal, 1)` and `resolve_signer_slot(deal, 2)`; assert names and email match. Call `resolve_signer_slot(deal, 3)`; assert None.
2. Run full test suite for signix. All pass.

---

### Implementation notes (from Batch 1)

- **get_signers_for_document_set_template** does not import doctemplates in `signix.py`; it receives a `DocumentSetTemplate` instance from the caller and uses `document_set_template.items.all()`. Item order follows `DocumentSetTemplateItem.Meta.ordering = ["order"]`. Each item’s template is accessed via `getattr(item, "template", None)` and `tagging_data` via `getattr(template, "tagging_data", None)` so missing or wrong-type templates are skipped without raising. Only `isinstance(tagging_data, list)` and `isinstance(entry, dict)` with `isinstance(val, int)` for `member_info_number` are collected; malformed or non-list `tagging_data` is skipped.
- **Unit tests** that build document set templates must provide `file` for Static/Dynamic templates (e.g. `SimpleUploadedFile`). Use `ContentType.objects.get_for_model(StaticDocumentTemplate)` (and `DynamicDocumentTemplate`) when creating `DocumentSetTemplateItem` so the GenericForeignKey resolves correctly.

### Implementation notes (from Batch 2)

- **resolve_signer_slot** does not import `Contact` or `LeaseOfficerProfile` in `signix.py`; it uses `getattr(deal, "lease_officer", None)`, `getattr(user, "lease_officer_profile", None)`, and `getattr(contact, "first_name", None)` etc. so the module stays free of model imports from `apps.contacts` and `apps.users`, avoiding circular imports. The deal instance is assumed to have `lease_officer` and `contacts` loaded (callers can use `select_related("lease_officer")` and `prefetch_related("contacts")`).
- **SignerPerson** was implemented as a **frozen** dataclass (`@dataclass(frozen=True)`).
- **Unit tests** include an extra case for slot 1 when the user has blank `get_full_name()` → first_name becomes `user.get_username()`, last_name `""`. Deal with no lease officer is tested by setting `deal.lease_officer = None` in memory (no need for a nullable FK in the DB).

---

## 6. File Summary

| Item | Value |
|------|--------|
| Module | `apps.deals.signix` (`apps/deals/signix.py`) |
| Types | `SignerPerson` (first_name, middle_name, last_name, email, phone) |
| Functions | `get_signers_for_document_set_template(document_set_template) -> list[int]`, `resolve_signer_slot(deal, slot_number) -> SignerPerson \| None` |
| Tests | Unit tests in `apps/deals/tests/test_signix.py` or `apps/deals/tests/test_signer_service.py` |

---

## 7. Open Issues / Implementation Decisions

- **Slot 3+:** **Decided:** Return `None` for slot > 2 in the current convention. Extend in a later release (e.g. second contact for slot 3) if needed.
- **Lease officer fallback when no profile:** **Decided:** Split `user.get_full_name()` — first word = first_name, remainder (trimmed) = last_name. If `get_full_name()` is empty or blank, use `first_name=user.get_username()`, `last_name=""`. Email from `user.email`; phone `""`.
- **document_set_template is None:** **Decided:** Function accepts `None` and returns `[]` so callers need not check before calling.
- **DocumentSetTemplateItem.template missing or wrong type:** **Decided:** Skip that item; collect no member_info_number from it. Do not raise.
- **Location:** Design open issue 1 leaves app location flexible; this plan places the signer service in `apps.deals.signix`. If the codebase later introduces `apps.signix`, these functions can move there and be re-exported or imported by deals.

---

*End of plan. Proceed to implementation only after review. Next: [40-PLAN-SIGNiX-SIGNERS-TABLE.md](40-PLAN-SIGNiX-SIGNERS-TABLE.md) (Plan 4).*

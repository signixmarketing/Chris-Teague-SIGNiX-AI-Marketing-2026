# Plan: Signers Table and Storage (Plan 4)

This document outlines how to add **storage for signer order and authentication** and the **Signers table** on the Deal detail page. Users see who will sign, in what order, and can reorder signers and set authentication per signer (SelectOneClick or SMSOneClick). The packager (Plans 5–6) reads this stored order and auth when building SubmitDocument.

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — Section 4.3 (Signer order and authentication), Section 5.3 (Signers table on Deal View), Section 7.4 (Deal View — Signers table). PLAN-SIGNiX-SIGNER-SERVICE.md (Plan 3) for `get_signers_for_document_set_template` and `resolve_signer_slot`.

**Prerequisites:** Plan 3 (signer service) is implemented. Deal detail page and Document Sets exist (PLAN-ADD-DOCUMENT-SETS). Deal has `deal_type` and optional `document_sets`; DocumentSetTemplate exists per deal type.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Storage:** Persist **signer order** (list of slot numbers in signing order, e.g. `[1, 2]` or `[2, 1]`) and **signer authentication** (per-slot SIGNiX auth type: SelectOneClick or SMSOneClick) so the packager and the Signers table both use the same data.
- **Signers table on Deal View:** A table showing one row per signer slot, in order: Order, Role, Name, Email, (optional) Phone, **Authentication** (dropdown). User can **reorder** signers (e.g. up/down buttons) and **change authentication** per signer; both persist.
- **When to show:** Show the Signers section when the deal has a deal type for which a Document Set Template exists (same condition as “Generate Documents”). If the deal has a document set, use `document_set.document_set_template`; otherwise use the template for `deal.deal_type`. If no template exists, hide the section or show an empty state.
- **Out of scope:** Submit flow (Plan 7), build body (Plan 5). This plan only adds storage, UI, and endpoints to load/save order and auth.

---

## 2. Storage: Deal (resolved)

**Decision:** Store on **Deal** so one order and one auth mapping apply to the deal regardless of document set. Simpler for this release; no sync when a document set is created or regenerated. The packager reads `deal.signer_order` and `deal.signer_authentication` (or helpers that return defaults when empty). Design Section 9.6 resolved: signer order and authentication on Deal.

- **Deal:** Add two optional JSONFields: `signer_order`, `signer_authentication`. If later we need per–document-set order/auth, we can add fields to DocumentSet and migrate (out of scope here).

---

## 3. Model Fields (Deal)

- **`signer_order`** — JSONField (e.g. list of integers), **null=True, blank=True**. Example: `[1, 2]` or `[2, 1]`. When null/empty, **effective order** = return value of `get_signers_for_document_set_template(template)` (numeric order).
- **`signer_authentication`** — JSONField (e.g. dict mapping slot → auth type), **null=True, blank=True**. Example: `{"1": "SelectOneClick", "2": "SMSOneClick"}`. Keys are **strings** (slot number as string) for JSON compatibility. When a slot is missing from the dict, **default** by convention: slot 1 (lease officer) → SelectOneClick; slot 2 (first contact) → SMSOneClick; slot 3+ → SelectOneClick (or document in plan). Plan 5 will use these defaults when building MemberInfo.

**Validation:** Store only valid auth values: `"SelectOneClick"` and `"SMSOneClick"`. Order list must contain only slot numbers that appear in the template’s signer list (no new slots); can be a subset or reorder of that list.

---

## 4. Helpers (read/write)

Implement in `apps.deals.signix` or in a small module used by the view and packager:

- **`get_signer_order_for_deal(deal, document_set_template)`** — Return the effective signer order: `deal.signer_order` if set and non-empty, else `get_signers_for_document_set_template(document_set_template)`.
- **`get_signer_authentication_for_slot(deal, slot_number)`** — Return the auth type for the slot: from `deal.signer_authentication` if present for that slot (key = str(slot_number)), else default: slot 1 → `"SelectOneClick"`, slot 2 → `"SMSOneClick"`, slot 3+ → `"SelectOneClick"`.

These allow the packager (Plan 5) and the Signers table to share the same logic. Optionally expose constants for auth values (e.g. `AUTH_SELECT_ONE_CLICK = "SelectOneClick"`, `AUTH_SMS_ONE_CLICK = "SMSOneClick"`).

---

## 5. Signers Table UI

- **Placement:** On the Deal detail page, add a **Signers** card **above** the Documents card (between Summary and Documents). Same template: `templates/deals/deal_detail.html` (or partial included there).
- **When visible:** Only when the deal has a **document set template** available: if the deal has a document set, use `document_set.document_set_template`; else use `DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).first()`. If no template is found, do not render the Signers section (or show “No signers — configure a document set template for this deal type”).
- **Content:** One row per signer in **effective order** (from `get_signer_order_for_deal`). Columns:
  - **Order** — Position (1, 2, …).
  - **Role** — Label for the slot: e.g. slot 1 → “Lease officer”, slot 2 → “Lessee” (or “First contact”). Use a simple mapping for the current convention; extend later if slots grow.
  - **Name** — From `resolve_signer_slot(deal, slot)` (first + middle + last).
  - **Email** — From `resolve_signer_slot(deal, slot).email`.
  - **Phone** (optional) — From `resolve_signer_slot(deal, slot).phone`; can be hidden on small screens.
  - **Authentication** — Dropdown per row: **SelectOneClick** | **SMSOneClick**. Current value from `get_signer_authentication_for_slot(deal, slot)`. On change, POST to save.
- **Reorder:** Provide **up/down** (or similar) controls so the user can move a signer up or down. On submit, compute the new order (e.g. swap adjacent slots) and save to `deal.signer_order`.
- **Saving:** **Decided:** (1) **Authentication** — One form for the whole table: all auth dropdowns plus one “Save signer settings” button; POST saves `signer_authentication` for all slots. (2) **Reorder** — “Move up” / “Move down” buttons per row that POST immediately (no separate Save); view updates `signer_order` and redirects back to deal detail.
- **Empty / unresolved:** If a slot does not resolve to a person (`resolve_signer_slot` returns None), show a placeholder (e.g. “— No contact —” for slot 2) and still show the row so the user sees that a signer is missing. Authentication dropdown can remain; saving order/auth still allowed.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Storage and helpers (steps 1–4)

1. **Add fields to Deal**
   - In `apps/deals/models.py`, add `signer_order` (JSONField, **null=True, blank=True**, no default) and `signer_authentication` (JSONField, **null=True, blank=True**, no default). Helpers treat null/empty as “use template order and slot-based defaults.”
   - Run `makemigrations` and `migrate`.

2. **Helpers**
   - In `apps/deals/signix.py` (or a new `apps/deals/signer_helpers.py`), implement `get_signer_order_for_deal(deal, document_set_template)` and `get_signer_authentication_for_slot(deal, slot_number)` with defaults as in Section 4. Use `get_signers_for_document_set_template` from Plan 3.

3. **Role label helper (optional)**
   - Add a small mapping or function for role label by slot: e.g. `get_role_label_for_slot(slot_number)` → `"Lease officer"` for 1, `"Lessee"` for 2, `f"Signer {slot_number}"` for 3+. Used by the template.

4. **Verification (Batch 1)**
   - Django check and migrate. In shell: set `deal.signer_order = [2, 1]`, save; call `get_signer_order_for_deal(deal, template)` and assert `[2, 1]`. Clear signer_order; assert result is template order. Same for auth: set `deal.signer_authentication = {"2": "SelectOneClick"}`, assert `get_signer_authentication_for_slot(deal, 2)` → `"SelectOneClick"`, and slot 1 uses default.

### Batch 2 — Signers table and save (steps 5–9)

5. **Deal detail context**
   - In `deal_detail` view (and any view that renders deal detail), compute: document set template for the deal (from document_set or deal_type). If template exists, compute signer slots (from `get_signers_for_document_set_template`), effective order (`get_signer_order_for_deal`), and for each slot in order: resolve person (`resolve_signer_slot`), auth (`get_signer_authentication_for_slot`), role label. Pass to template as e.g. `signers` list of dicts: `[{slot, order_index, role_label, person, auth}, ...]`. If template is None, pass `signers=[]` or `show_signers=False`.

6. **Template: Signers card**
   - In `templates/deals/deal_detail.html`, add a **Signers** card above the Documents card. Only show if `signers` is non-empty (or `show_signers`). Table: Order, Role, Name, Email, Phone (optional), Authentication (dropdown). Use Bootstrap table styling to match the rest of the app.

7. **Save authentication**
   - Add a view that accepts POST with `deal_pk` and auth per slot (e.g. `auth_1`, `auth_2`, …). Validate values are SelectOneClick or SMSOneClick. Update `deal.signer_authentication` (merge with existing so other slots are preserved), save, redirect back to deal detail. **URL:** `POST /deals/<pk>/signers/update-auth/` (name e.g. `deal_signers_update_auth`).

8. **Reorder**
   - Add a view that accepts POST with `deal_pk`, `action` (move_up | move_down), and `slot` (integer). Load deal and current effective order; swap slot with previous/next; write new list to `deal.signer_order`, save, redirect back to deal detail. **URL:** `POST /deals/<pk>/signers/reorder/` (name e.g. `deal_signers_reorder`).

9. **Verification (Batch 2)**
   - Load deal detail for a deal with a document set template and two signer slots; Signers table shows two rows with correct names and auth. Change auth for slot 2 to SelectOneClick; submit; reload and confirm. Move signer 2 up (so order becomes [2, 1]); reload and confirm order changed. Run packager later (Plan 5) and confirm it uses the stored order and auth.

---

## 6a. Implementation Batches and Verification

**Batch 1 — Storage and helpers**

**Includes:** `signer_order` and `signer_authentication` on Deal; migration; `get_signer_order_for_deal`, `get_signer_authentication_for_slot`; optional `get_role_label_for_slot`.

**How to test after Batch 1:**

1. Migrate; in shell create or load a deal with a document set template. Assert `get_signer_order_for_deal(deal, template)` returns `[1, 2]` when signer_order is empty. Set `deal.signer_order = [2, 1]`, save; assert helper returns `[2, 1]`. Assert `get_signer_authentication_for_slot(deal, 1)` is SelectOneClick and for slot 2 is SMSOneClick when signer_authentication is empty; set auth for 2 to SelectOneClick, assert helper returns it.

**Batch 2 — UI and save**

**Includes:** Signers card on deal detail; context with signers list; POST endpoints (or one) to save auth and reorder; redirect back to deal detail.

**How to test after Batch 2:**

1. Open deal detail for a deal that has a document set template (and ideally a document set with signer slots 1 and 2). Signers table appears with two rows. Change authentication for one signer; save; reload and confirm. Use move up/down; reload and confirm order. Confirm unresolved slot (e.g. no contact) shows a placeholder and table still renders.

---

## 7. File and URL Summary

| Item | Value |
|------|--------|
| Model | `Deal`: add `signer_order`, `signer_authentication` (JSONField, null=True, blank=True) |
| Helpers | `get_signer_order_for_deal(deal, document_set_template)`, `get_signer_authentication_for_slot(deal, slot_number)`, optional `get_role_label_for_slot(slot_number)` in `apps.deals.signix` or `signer_helpers` |
| Template | `templates/deals/deal_detail.html` — Signers card above Documents |
| URLs | `POST /deals/<pk>/signers/update-auth/` (deal_signers_update_auth), `POST /deals/<pk>/signers/reorder/` (deal_signers_reorder) |
| View | Deal detail view extended to pass `signers` (and template); new view(s) for update-auth and move up/down |

---

## 8. Open Issues / Implementation Decisions

- **Storage location (Deal vs DocumentSet):** **Decided for this plan:** Store on **Deal**. One order and one auth set per deal; packager reads from deal. If per–document-set order is needed later, add fields to DocumentSet in a follow-up.
- **Auth value format:** Use strings `"SelectOneClick"` and `"SMSOneClick"` in JSON and in the packager. Constants can be defined in `apps.deals.signix` for consistency.
- **Role labels:** Use a simple mapping for slots 1 and 2 (“Lease officer”, “Lessee” or “First contact”); slot 3+ use “Signer 3”, etc. Refinable later (e.g. from template or config).
- **Form approach:** **Decided:** One form for the whole table: all auth dropdowns + one “Save signer settings” button that POSTs auth for all slots. Reorder via separate “Move up” / “Move down” buttons that POST immediately (no separate Save for order).
- **Unresolved signer:** When `resolve_signer_slot` returns None, show a placeholder in Name/Email/Phone but keep the row and allow saving order/auth so the user can still reorder and fix (e.g. add a contact) later.
- **Default for signer_order/signer_authentication:** **Decided:** Use **null=True, blank=True** (no default). Helpers treat null/empty as “use template order / slot defaults”; avoids storing `[]`/`{}` when the user has never changed anything.
- **URL shape for save:** **Decided:** Two endpoints: `POST /deals/<pk>/signers/update-auth/` (body: auth_1, auth_2, …) and `POST /deals/<pk>/signers/reorder/` (body: action=move_up|move_down, slot=<int>).

---

## 9. Open Issues and Recommendations (Summary)

| Issue | Status | Recommendation |
|-------|--------|----------------|
| **Storage: Deal vs DocumentSet** | Decided | Store on **Deal** (`signer_order`, `signer_authentication`). Simpler; one place for packager. Move to DocumentSet later if per-set order is required. |
| **Auth value format** | Decided | Use strings `"SelectOneClick"` and `"SMSOneClick"`. Define constants in `apps.deals.signix` for use in Plan 5 and UI. |
| **Role labels** | Decided | Simple mapping: slot 1 → “Lease officer”, slot 2 → “Lessee” (or “First contact”), slot 3+ → “Signer &lt;n&gt;”. |
| **Form approach** | Decided | One form for the whole table: all auth dropdowns + one “Save signer settings” button. Reorder via “Move up” / “Move down” buttons that POST immediately. |
| **Unresolved signer (slot has no person)** | Decided | Show placeholder text (e.g. “— No contact —”); keep row and allow saving order/auth. |
| **Default for JSONFields** | Decided | Use **null=True, blank=True** (no default). Helpers treat null/empty as “use template order / slot defaults”. |
| **URL shape for save** | Decided | Two endpoints: `POST /deals/&lt;pk&gt;/signers/update-auth/` and `POST /deals/&lt;pk&gt;/signers/reorder/` (body: action=move_up|move_down, slot=&lt;int&gt;). |

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-BUILD-BODY.md (Plan 5).*

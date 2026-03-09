# Plan: Add Data Interface (Schema and Deal Data Retrieval)

This document outlines how to add the **Internal Data Schema** and **Deal Data Retrieval** interface to the Django lease application. The schema provides `get_schema()` and `get_paths()` for discovering and presenting mappable data paths. The deal data interface provides `get_deal_data(deal)` to retrieve the full deal-centric structure for a specific deal. UI includes a Schema viewer page and a Debug Data page (deal list with View JSON modal).

**Design reference:** [DESIGN-DATA-INTERFACE.md](DESIGN-DATA-INTERFACE.md). **Knowledge:** [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) (§4 — schema and deal data as single source for documents).

**Prerequisites:** [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) plans 1–3 are implemented (Baseline, Biz Domain Master, Images). The schema depends on Deal, Vehicle, Contact, User, and LeaseOfficerProfile models.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **Schema interface:** `get_schema()` returns the full Deal-centric schema as a tree (root, nodes, children); `get_paths()` returns a flat list of mappable path strings. JSON-serializable. Built via `Model._meta.get_fields()` and related APIs.
- **Deal data interface:** `get_deal_data(deal)` returns a nested dict conforming to the schema (deal scalars, lease_officer, deal_type, vehicles, contacts). JSON-serializable. Vehicles and contacts ordered by `id`.
- **UI:** Schema viewer page (displays structure); Debug Data page (deal list with "View JSON" button per deal; modal shows formatted JSON with Copy button).
- **Access:** Authenticated users only (`@login_required`).
- **App:** New app `apps.schema` (no models; service module + views).

---

## 2. Schema Interface (get_schema, get_paths)

- **Implementation:** Create `apps.schema.services` with functions `get_schema()` and `get_paths()`.
- **Discovery:** Use `Model._meta.get_fields()` to introspect Deal, Vehicle, Contact, User, LeaseOfficerProfile. Follow FKs and M2Ms; limit depth (one level of relation from Deal). Deal is root; paths start with `deal.`.
- **Output:** Schema is a tree: `{ "root": "deal", "description": "...", "version": "1", "nodes": [...] }`. Each node: `path`, `type` (string, date, decimal, integer, object, list), optional `model`, optional `description` (from field `verbose_name`), optional `children`, optional `item_path` for lists.
- **get_paths():** Derive from schema—return flat list of mappable path strings including leaf paths, list paths (`deal.vehicles`, `deal.contacts`), and root `deal`. Include `deal.payment_amount`, `deal.vehicles.item.sku`, `deal.vehicles_count`, `deal.contacts.item.full_name`, `deal.contacts_count`, etc. Derived paths (`full_name`, `vehicles_count`, `contacts_count`) are explicit schema entries, not from model introspection.
- **get_paths_grouped_for_mapping():** Return paths grouped for the mapping UI Source dropdown: Data Source (`deal`), List sources (with descriptive labels), Scalar / item paths. Enables future expansion (e.g. additional root data sources).
- **Node types:** Map Django field types to schema types (DateField→date, DecimalField→decimal, CharField/TextField→string, ForeignKey/M2M→object/list).

---

## 3. Deal Data Interface (get_deal_data)

- **Implementation:** Add `get_deal_data(deal)` to `apps.schema.services`.
- **Input:** `Deal` instance only. The view fetches the deal before calling; the function does not accept `deal_id`.
- **Output:** Nested dict with `deal` at root. Structure: scalars (dates as `"YYYY-MM-DD"`, decimals as numbers), `lease_officer` (username + `lease_officer_profile`: first_name, last_name, phone_number, email, full_name), `deal_type` (name), `vehicles` (list of {sku, year, jpin}), `vehicles_count`, `contacts` (list of {first_name, middle_name, last_name, full_name, email, phone_number}), `contacts_count`. Contact `full_name` is computed from first + middle + last (space-separated). `vehicles_count` and `contacts_count` are integer counts derived from list lengths; use transforms (`number_to_word`, `plural_suffix`) in mapping for display variants.
- **Ordering:** `deal.vehicles.order_by('id')`, `deal.contacts.order_by('id')`.
- **Null handling:** If `lease_officer` or `lease_officer_profile` missing, use `null` (explicit null). Empty vehicles/contacts → `[]`.

---

## 4. Pages and Behavior

### 4.1 Schema viewer page

- **URL:** `/schema/` (name `schema_view`).
- **Content:** Call `get_schema()`, render the tree as a nested, collapsible structure (path, type, model, description).
- **Header:** "Data schema".
- **Layout:** Extends `base.html`. Sidebar link "Data schema" → `/schema/`.

### 4.2 Debug Data page

- **URL:** `/schema/debug/` (name `debug_data_list`).
- **Content:** Table of all deals (columns: Date entered, Lease officer, Deal type, Lease start, Lease end, Payment, Actions). Each row has "View JSON" button.
- **View JSON:** Click opens a modal. Set each button's `data-json-url` via `{% url 'schema:deal_data_json' deal.pk %}` so the correct URL is passed to JavaScript. Modal fetches that URL, displays formatted JSON in `<pre>`; has "Copy" button that copies to clipboard and shows "Copied!" feedback (hide after ~2 s); modal can be closed (X or outside click).
- **Empty state:** "No deals yet." if no deals.
- **Layout:** Extends `base.html`. Sidebar link "Debug Data" → `/schema/debug/`.

### 4.3 JSON endpoint (for modal)

- **URL:** `/schema/deal/<pk>/data/` (name `deal_data_json`).
- **Method:** GET. Returns `JsonResponse(get_deal_data(deal))`. `@login_required`. 404 if deal not found.

---

## 5. Navigation and Integration

- **Sidebar:** Add "Data schema" and "Debug Data" links (e.g. after Images, before Admin). Use URL-level active state: `request.resolver_match.url_name == 'schema_view'` for Data schema, `url_name == 'debug_data_list'` for Debug Data (only the current page shows active).
- **Config:** Add `"apps.schema"` to `INSTALLED_APPS` (insert immediately after `apps.deals`). In `config/urls.py`, add `path("schema/", include("apps.schema.urls"))` after the deals path and before the images path.
- **Jazzmin:** Out of scope for this phase; skip custom links.

---

## 6. Implementation Notes

- **Field names:** Use `deal.lease_start_date`, `deal.lease_end_date` (not `lease_start`). Match the actual Deal model.
- **Views and services:** Keep views thin: call schema services from views; do not duplicate schema or deal-data logic in views (per [20-APPROACH.md](../20-APPROACH.md)).
- **LeaseOfficerProfile:** Access via `user.lease_officer_profile`; may not exist (handle `DoesNotExist` or use `getattr(user, 'lease_officer_profile', None)`). Include `full_name` from the profile property.
- **Decimal serialization:** Use `float()` or ensure JSON encoder handles Decimal (Django's `JsonResponse` handles it).
- **Copy button:** Use `navigator.clipboard.writeText()` with the JSON string. Show "Copied!" feedback after successful copy; hide it after ~2 seconds to return to neutral state.

---

## 7. Implementation Order (Checklist)

### Batch 1 — App and core logic (steps 1–4)

1. **Create `apps.schema` app**
   - Create `apps/schema/` with `__init__.py`, `apps.py` (`name = "apps.schema"`), `views.py`, `urls.py`.
   - Add `"apps.schema"` to `INSTALLED_APPS` (after `apps.deals`).

2. **Schema discovery**
   - Create `apps/schema/services.py`.
   - Implement `get_schema()`: introspect Deal, Vehicle, Contact, User, LeaseOfficerProfile; build tree structure (`root`, `description`, `version`, `nodes`) with `path`, `type`, `model`, `description` (from `field.verbose_name`), `children`, `item_path` for lists. JSON-serializable.
   - Implement `get_paths()`: derive from schema; return `["deal.payment_amount", "deal.vehicles.item.sku", ...]`.

3. **Deal data retrieval**
   - Implement `get_deal_data(deal)` in `apps/schema/services.py`.
   - Build nested dict per DESIGN-DATA-INTERFACE. Handle lease_officer, lease_officer_profile (use `null` when missing), deal_type, vehicles (order_by id), contacts (order_by id).
   - Ensure output is JSON-serializable (dates as strings, decimals as numbers).

4. **URL routing**
   - In `config/urls.py`: add `path("schema/", include("apps.schema.urls"))` after deals, before images.
   - In `apps/schema/urls.py`: `app_name = "schema"`; create minimal placeholder views that return a simple `HttpResponse` for schema viewer and debug page so `/schema/` and `/schema/debug/` do not 404. These will be replaced in Batches 2 and 3.

Batch 1 complete when `get_schema()`, `get_paths()`, and `get_deal_data(deal)` work and can be tested in shell; `/schema/` loads.

### Batch 2 — Schema viewer page (steps 5–7)

5. **Schema viewer view**
   - View `schema_view`: call `get_schema()`, pass to template. `@login_required`.

6. **Schema viewer template**
   - `templates/schema/schema_view.html` — extends `base.html`; render schema as nested, collapsible structure (path, type, model, description). Use a recursive template include (e.g. `_schema_node.html`) so nested nodes render correctly. Ensure unique HTML IDs for each collapsible section (e.g. slugify the node path) for Bootstrap collapse.

7. **URL and sidebar**
   - URL: `""` → schema_view (at `/schema/`).
   - Sidebar: add "Data schema" link → `schema:schema_view`, icon e.g. `bi bi-diagram-3`. Active when `url_name == 'schema_view'`.

Batch 2 complete when Schema viewer page displays the schema.

### Batch 3 — Debug Data page and JSON endpoint (steps 8–12)

8. **Deal data JSON endpoint**
   - View `deal_data_json`: GET, `get_object_or_404(Deal, pk=pk)`, return `JsonResponse(get_deal_data(deal))`. `@login_required`.
   - URL: `deal/<int:pk>/data/` → deal_data_json.

9. **Debug Data list view**
   - View `debug_data_list`: list all deals `order_by('-date_entered')`; pass to template. `@login_required`.

10. **Debug Data template**
    - `templates/schema/debug_data_list.html` — table (Date entered, Lease officer, Deal type, Lease start, Lease end, Payment, Actions). Actions: "View JSON" button per row with `data-json-url="{% url 'schema:deal_data_json' deal.pk %}"`. Include Bootstrap modal; modal body shows `<pre>` with JSON; "Copy" button that copies and shows "Copied!" feedback (hide after ~2 s). JavaScript: on "View JSON" click, fetch `data-json-url`, display formatted JSON in modal.

11. **URLs**
    - `debug/` → debug_data_list
    - `deal/<int:pk>/data/` → deal_data_json

12. **Sidebar**
    - Add "Debug Data" link → `schema:debug_data_list`, icon e.g. `bi bi-bug`. Active when `url_name == 'debug_data_list'`.

---

## 7a. Implementation Batches and Verification

Implement in **three batches**. After each batch, run the verification steps.

### Batch 1 — App and core logic (steps 1–4)

**Includes:** Create `apps.schema`, add to `INSTALLED_APPS`, implement `get_schema()`, `get_paths()`, `get_deal_data(deal)`, minimal URL routing.

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Shell — get_schema:**
   ```python
   from apps.schema.services import get_schema
   schema = get_schema()
   assert isinstance(schema, (list, dict))
   # Check for expected paths
   paths = [n["path"] if isinstance(n, dict) else getattr(n, "path", None) for n in (schema if isinstance(schema, list) else schema.get("nodes", []))]
   assert any("deal.payment_amount" in str(p) for p in paths) or any(p == "deal.payment_amount" for p in paths)
   ```
3. **Shell — get_paths:**
   ```python
   from apps.schema.services import get_paths
   paths = get_paths()
   assert isinstance(paths, list)
   assert "deal.payment_amount" in paths or "deal.date_entered" in paths
   assert "deal.vehicles.item.sku" in paths or any("deal.vehicles" in p for p in paths)
   ```
4. **Shell — get_deal_data:**
   ```python
   from apps.deals.models import Deal
   from apps.schema.services import get_deal_data
   import json
   deal = Deal.objects.first()
   if deal:
       data = get_deal_data(deal)
       assert "deal" in data
       assert "payment_amount" in data["deal"] or "date_entered" in data["deal"]
       json.dumps(data)  # Must not raise
   ```
5. **URLs:** Visit `/schema/` — no 404 (placeholder or schema view acceptable).

Batch 1 complete when the above pass.

### Batch 2 — Schema viewer page (steps 5–7)

**Includes:** Schema viewer view, template, sidebar link.

**How to test after Batch 2:**

1. **Login:** Log in as karl (or any user).
2. **Sidebar:** "Data schema" link appears (e.g. after Images, before Admin).
3. **Schema page:** Click "Data schema"; `/schema/` loads. Page shows schema structure as nested, collapsible tree (paths, types). No errors.
4. **Auth:** Logout; visit `/schema/` — redirect to login.

Batch 2 complete when the above pass.

### Batch 3 — Debug Data page (steps 8–12)

**Includes:** Deal data JSON endpoint, Debug Data list view and template, modal with View JSON and Copy, sidebar link.

**How to test after Batch 3:**

1. **Login:** Log in as karl.
2. **Sidebar:** "Debug Data" link appears.
3. **Debug Data page:** Click "Debug Data"; `/schema/debug/` loads. Table shows deals (or "No deals yet" if empty).
4. **View JSON:** If deals exist, click "View JSON" on a deal. Modal opens; JSON is displayed (formatted).
5. **Copy:** Click "Copy" button; "Copied!" feedback appears; paste somewhere — JSON content matches.
6. **Close modal:** Click X or outside; modal closes.
7. **JSON endpoint:** Visit `/schema/deal/1/data/` (or valid deal pk) in browser; returns JSON. Visit with invalid pk; 404.
8. **Auth:** Logout; visit `/schema/debug/` — redirect to login.

Batch 3 complete when all of the above pass.

---

## 8. File and URL Summary

| Item | Value |
|------|-------|
| App | `apps.schema` |
| Module | `apps/schema/services.py` — `get_schema()`, `get_paths()`, `get_deal_data(deal)` |
| Schema viewer | `/schema/` — displays schema structure |
| Debug Data | `/schema/debug/` — deal list, View JSON per row |
| Deal JSON | `/schema/deal/<pk>/data/` — returns `get_deal_data(deal)` as JSON |
| Nav | Sidebar: "Data schema" → `/schema/`, "Debug Data" → `/schema/debug/` |
| Models | None (no migrations) |

---

## 9. Out of Scope (This Phase)

- Jazzmin custom links for schema/debug pages.
- HTTP API exposure (future; interface is API-ready).
- Context builder or mapping UI (PLAN-ADD-DYNAMIC-DOC-TEMPLATES).
- Document generation (PLAN-ADD-DOCUMENT-SETS).
- Pagination on Debug Data deal list.

---

*End of plan. Proceed to implementation only after review.*

# Design: Internal Data Schema and Deal Data Interface

This document captures the design for the **Internal Data Schema** and **Deal Data Retrieval** interface. These are foundational capabilities that support dynamic document templates (mapping, context building) and debugging. They are distinct from document workflows; see **../06-DOCS/DESIGN-DOCS.md** for document templates, document sets, and signing.

---

## Scope

- **Internal Data Schema** — A programmatic representation of the data structure for Deals and related objects (Vehicles, Contacts, User). Used for mapping configuration, document population, and a schema viewer page.
- **Deal Data Retrieval** — A clean interface to retrieve the full data for a specific deal, including child Vehicles, Contacts, and the lease officer (User).
- **UI** — Schema viewer page (structure); Debug Data page (deal list with View JSON per deal).

This interface is the **single source of truth** for schema and deal data. ../06-DOCS/DESIGN-DOCS.md mandates that document features (mapping UI, context builder) use it exclusively and must not traverse Django models or QuerySets directly. See ../06-DOCS/DESIGN-DOCS.md for the no-circumvention requirement.

Implementation will follow in separate PLAN files.

---

## Current Platform (Assumed)

This design assumes the platform has:

- **Deals** — Deal model with lease officer, deal type (FK), vehicles and contacts (M2M), and deal properties (dates, payment, deposit, insurance, governing law). Deal Type "Lease - Single Signer" exists and is the default.
- **Vehicles** — Vehicle model with SKU, year, JPIN.
- **Contacts** — Contact model with first_name, middle_name, last_name, email, phone_number.
- **Users** — Django User with optional LeaseOfficerProfile (first_name, last_name, phone_number, email, full_name).

Plans 1–3 from 70-PLAN-MASTER.md (Baseline, Biz Domain Master, Images) are implemented. This design is implemented by 10-PLAN-DATA-INTERFACE.md (70-PLAN-MASTER.md plan 4). The core domain (Deals, Vehicles, Contacts) is designed in **../02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md**.

---

## 1. Internal Data Schema

The internal data schema is a **clean, programmatic representation** of the data structure used when populating dynamic document templates. It describes what data paths exist and how they relate. Deal is the **root object**; Vehicles, Contacts, and the lease officer (User) are **child objects** reachable from the deal. This structure reflects the domain: documents are generated *for* a deal, and all data in the template context is in the scope of that deal.

### Purpose and Uses

The schema interface supports three consumers:

1. **Mapping configuration** — The Dynamic Template mapping UI uses the schema to present available data paths (e.g., dropdowns) and validate user selections. See ../06-DOCS/DESIGN-DOCS.md for the mapping feature.
2. **Document population** — The context builder uses the schema for paths and the Deal Data Retrieval interface (Section 2) for data; it applies the mapping and transforms to build the template context at render time.
3. **Schema viewer page** — A dedicated page in the app displays the internal data structure for testing, troubleshooting, and reference.

The interface is **internal** to the application today. It is designed to be **API-ready**: the schema is JSON-serializable, stateless for discovery, and has a clear contract. Exposing it via HTTP (e.g., `GET /api/schema`) later requires no change to the structure.

### Deal-Centric Hierarchy

Using Deal as the root is the correct choice because:

- Documents are always generated in the context of a deal.
- Template mappings reference paths like `deal.payment_amount`, `deal.vehicles`, `deal.contacts[0].first_name`, `deal.lease_officer`.
- Vehicles and Contacts are accessed via `deal.vehicles` and `deal.contacts`; the lease officer via `deal.lease_officer`. They have no standalone root role in document context.

The hierarchy:

- **deal** (root)
  - **Scalar fields:** `date_entered`, `lease_start_date`, `lease_end_date`, `payment_amount`, `payment_period`, `security_deposit`, `insurance_amount`, `governing_law`
  - **lease_officer** (FK → User, with `lease_officer_profile` for display name, phone, email)
  - **deal_type** (FK → DealType; `name`)
  - **vehicles** (M2M → list of Vehicle: `sku`, `year`, `jpin`)
  - **vehicles_count** (derived: integer count of vehicles; use transform `number_to_word` or `plural_suffix` for "one"/"two" or ""/"s")
  - **contacts** (M2M → list of Contact: `first_name`, `middle_name`, `last_name`, `full_name` (computed: first + middle + last, space-separated), `email`, `phone_number`)
  - **contacts_count** (derived: integer count of contacts; use transform `number_to_word` or `plural_suffix` for display variants)

### Schema Structure (JSON-Serializable)

The schema is a tree of nodes. Each node describes a path, its type, and (for complex types) its children. The structure is suitable for internal use and future HTTP API responses.

**Node types:** `string`, `date`, `decimal`, `integer`, `object`, `list`

**Scalar node** (leaf):

```json
{
  "path": "deal.payment_amount",
  "type": "decimal",
  "model": "Deal",
  "description": "Payment amount"
}
```

**Object node** (with children):

```json
{
  "path": "deal.lease_officer",
  "type": "object",
  "model": "User",
  "children": [
    { "path": "deal.lease_officer.username", "type": "string" },
    { "path": "deal.lease_officer.lease_officer_profile.first_name", "type": "string" },
    { "path": "deal.lease_officer.lease_officer_profile.last_name", "type": "string" }
  ]
}
```

**List node** (with item schema):

```json
{
  "path": "deal.vehicles",
  "type": "list",
  "model": "Vehicle",
  "item_path": "item",
  "children": [
    { "path": "deal.vehicles.item.sku", "type": "string" },
    { "path": "deal.vehicles.item.year", "type": "string" },
    { "path": "deal.vehicles.item.jpin", "type": "string" }
  ]
}
```

For list variables in templates (`{% for item in data.jet_pack_list %}`), the mapping specifies `deal.vehicles` as the source. When template item field names (e.g. `item.sku`) match schema field names (`sku`), the list is used as-is; `item_map` is optional and only needed when renaming or selecting fields.

**Root schema response** (example shape):

```json
{
  "root": "deal",
  "description": "Deal-centric document context schema",
  "version": "1",
  "nodes": [
    { "path": "deal", "type": "object", "children": [ ... ] }
  ]
}
```

Or a flatter structure: `nodes` is a list of all nodes (scalars and containers), and the tree is implied by path prefixes. Implementation can choose the most convenient representation; the contract is that paths are unique and follow the Deal-centric hierarchy.

### Schema Interface (Internal)

The schema is provided by a dedicated module or service in a new app **`apps.schema`**. This keeps schema and deal-data concerns separate from Deals, Document Templates, and other features. The interface is internal (Python functions or methods) but designed so that each operation can become an API endpoint later.

| Operation | Input | Output | Future API |
|-----------|-------|--------|------------|
| `get_schema()` | — | Full schema (tree or flat nodes); JSON-serializable | `GET /api/schema` |
| `get_paths()` | — | Flat list of mappable path strings (leaf paths, list paths, and root `deal`) | Derivable from `get_schema()` or `GET /api/schema/paths` |
| `get_paths_grouped_for_mapping()` | — | Deal paths grouped for mapping UI: Data Source (e.g. `deal`), List sources (e.g. `deal.vehicles`, `deal.contacts`), Scalar / item paths. Returns `[(group_label, [(path, display_label), ...]), ...]`. The mapping UI (per DESIGN-DOCS) appends an Images optgroup from the Image model for image variables. | — |

**Data retrieval** for a specific deal is handled by the **Deal Data Retrieval** interface (Section 2). The context builder calls `get_deal_data(deal)` to obtain the full deal-centric structure, then applies the mapping and transforms. The schema defines valid paths; the retrieval interface returns values for those paths.

### Schema Viewer Page

A dedicated page in the app displays the internal data structure. It calls `get_schema()` and renders the tree (or flat list) in a readable format. Uses: testing, troubleshooting, and reference when configuring mappings. Placement: sidebar link "Data schema" or "Schema reference", under a suitable section (e.g. near Document Templates or Admin). `@login_required`.

### Implementation Notes

- **Discovery:** Use `Model._meta.get_fields()` and related APIs to build the schema from Deal, Vehicle, Contact, User, LeaseOfficerProfile. Follow FKs and M2Ms; limit depth to avoid infinite recursion (e.g. stop at one level of relation from Deal).
- **Deal as root:** All paths start with `deal.`. The root node `deal` represents the Deal instance.
- **List items:** For `deal.vehicles` and `deal.contacts`, the schema exposes per-item paths (e.g. `deal.vehicles.item.sku`, `deal.contacts.item.full_name`). When template loop variable names match schema field names (e.g. `item.sku` → `sku`), the list can be used as-is; `item_map` is optional and only needed for renaming or field selection. For contacts, `full_name` is a derived field computed in `get_deal_data()`; it is not introspected from the Contact model.
- **Derived scalars (vehicles_count, contacts_count):** Integer counts computed in `get_deal_data()` from the respective list lengths. Formatting (number-to-word, plural suffix) is the mapping layer's responsibility via transforms.
- **User / LeaseOfficerProfile:** `deal.lease_officer` points to User; `lease_officer_profile` (reverse OneToOne) provides `first_name`, `last_name`, `phone_number`, `email`, `full_name`. Expose these as `deal.lease_officer.lease_officer_profile.*`. The profile may not exist; handle `DoesNotExist` or use `getattr(user, 'lease_officer_profile', None)`.

---

## 2. Deal Data Retrieval

The **Deal Data Retrieval** interface returns the full data for a specific deal in a structure that conforms to the Internal Data Schema (Section 1). It is distinct from the schema: the schema describes *what paths exist*; this interface returns *actual values* for a given deal instance, including child Vehicles, Contacts, and the lease officer (User).

### Purpose and Uses

1. **Document population** — The context builder calls this interface to obtain deal data, then applies the template mapping and transforms to produce the final template context. See ../06-DOCS/DESIGN-DOCS.md.
2. **Debug Data page** — A separate "Debug Data" menu item leads to a page that lists deals in a table, with a "View JSON" button per deal. Clicking it opens a modal displaying `get_deal_data(deal)` as formatted JSON, with a **Copy** button (clipboard) and easy close. Keeps debug functionality out of the main user workflow. Uses: debugging, verifying what data is available for document generation, and troubleshooting mapping issues.
3. **Future API** — A document-generation service (or external consumer) could request deal data via HTTP without direct database access.

The interface is **internal** today. It is designed to be **API-ready**: input and output are simple and JSON-serializable; exposing `GET /api/deals/<id>/data` later requires no change to the contract.

### Interface

| Operation | Input | Output | Future API |
|-----------|-------|--------|------------|
| `get_deal_data(deal)` | `Deal` instance only; the view fetches the deal before calling | Nested dict conforming to schema; JSON-serializable | `GET /api/deals/<id>/data` |

### Output Structure

The output is a nested dict with `deal` at the root. The structure mirrors the schema paths; each path in the schema has a corresponding value. Dates are ISO 8601 strings; decimals are numbers; relations are expanded (no raw IDs unless useful).

**Example shape:**

```json
{
  "deal": {
    "date_entered": "2024-01-15",
    "lease_start_date": "2024-02-01",
    "lease_end_date": "2025-01-31",
    "payment_amount": 150.00,
    "payment_period": "month",
    "security_deposit": 500.00,
    "insurance_amount": 100.00,
    "governing_law": "Delaware",
    "lease_officer": {
      "username": "karl",
      "lease_officer_profile": {
        "first_name": "Karl",
        "last_name": "Smith",
        "phone_number": "...",
        "email": "karl@example.com",
        "full_name": "Karl Smith"
      }
    },
    "deal_type": {
      "name": "Lease - Single Signer"
    },
    "vehicles": [
      { "sku": "Skyward Personal Jetpack P-2024", "year": "2024", "jpin": "4CH8P4K7E3X6Z9R2V" }
    ],
    "vehicles_count": 1,
    "contacts_count": 1,
    "contacts": [
      { "first_name": "Max", "middle_name": "", "last_name": "Danger", "full_name": "Max Danger", "email": "...", "phone_number": "..." }
    ]
  }
}
```

- **Scalars:** Direct values; dates as `"YYYY-MM-DD"`; decimals as numbers.
- **lease_officer:** Expanded object with `username` and `lease_officer_profile` (first_name, last_name, phone_number, email, full_name).
- **deal_type:** Expanded object with `name`.
- **vehicles, contacts:** Lists of objects; each object has the fields from the schema (`deal.vehicles.item.*`, `deal.contacts.item.*`). For contacts, `full_name` is computed from `first_name`, `middle_name`, and `last_name` (space-separated, empty parts omitted). Order: `deal.vehicles.order_by('id')` and `deal.contacts.order_by('id')` (Django M2M has no intrinsic order; id order is stable and sufficient for v1).
- **vehicles_count, contacts_count:** Derived scalars (integer count of the respective list). Formatting (e.g. "one", ""/"s") is handled by transforms (`number_to_word`, `plural_suffix`) in the mapping layer, not in the data interface.

### Relationship to Context Builder

The **context builder** (used when populating dynamic templates; see ../06-DOCS/DESIGN-DOCS.md):

1. Calls `get_deal_data(deal)` to obtain the full deal-centric structure.
2. Applies the mapping config: for each template variable (e.g. `data.payment_amount`), looks up the source path (e.g. `deal.payment_amount`) in the returned structure, applies any transform (e.g. `date_day`, `date_month_day`), and builds the template context.

The context builder **must not** traverse Django models or QuerySets directly; it works exclusively from the structure returned by `get_deal_data()`. Path resolution (e.g. `deal.contacts[0]` for "first contact") is performed on that structure—e.g. the first element of the `contacts` list—not via database queries. ../06-DOCS/DESIGN-DOCS.md enforces this no-circumvention requirement for all document features.

### Implementation Notes

- **Single source:** `get_deal_data()` is the canonical way to retrieve deal data for document population. All consumers use it; no ad-hoc ORM traversal elsewhere.
- **Schema conformance:** The output structure must match the schema. When the schema is updated (e.g. new fields), `get_deal_data()` must be updated to include them. Both schema and retrieval derive from the same models, so changes flow through both.
- **Null handling:** If `lease_officer` or `lease_officer_profile` is missing, return `null` (explicit null). Same for empty `vehicles` or `contacts` (empty list `[]`).
- **API readiness:** The function accepts a `Deal` instance; the view fetches the deal before calling. A future API view would fetch the deal (e.g. `get_object_or_404(Deal, pk=pk)`) and pass it to `get_deal_data(deal)`.
- **Debug Data page:** A separate "Debug Data" menu item (sidebar) leads to a page that lists all deals in a table. Each row shows key deal info (e.g. date entered, lease officer) and has a "View JSON" button that opens a modal displaying `get_deal_data(deal)` as formatted JSON. The modal includes a **Copy** button (clipboard) and can be easily closed. Keeps debug functionality separate from the main deal workflow. Placement: e.g. after Document Templates or near Admin, or in a "Developer" section if one exists. `@login_required`.

---

## Decisions Log

### Internal Data Schema

The internal data schema is a first-class, Deal-centric representation of mappable data paths. It is provided by a dedicated schema service/module with `get_schema()` and `get_paths()`. Deal is the root; Vehicles, Contacts, and the lease officer (User) are children. The schema is JSON-serializable and designed for future API exposure. Uses: mapping UI, context builder (document population), and a schema viewer page for testing and troubleshooting.

### Deal Data Retrieval

The Deal Data Retrieval interface (`get_deal_data(deal)`) returns the full data for a specific deal as a nested, JSON-serializable structure that conforms to the schema. The context builder uses it to populate dynamic templates; a future API (`GET /api/deals/<id>/data`) can expose it without change to the contract.

### Schema and deal data: implementation location

Schema discovery, `get_schema()`, `get_paths()`, and `get_deal_data()` live in a new app **`apps.schema`**. Keeps concerns separate from Deals, Document Templates, etc.

### Schema structure: tree representation

The chosen representation for `get_schema()` is the **tree structure**: `{ "root": "deal", "description": "...", "version": "1", "nodes": [ ... ] }` with nested `children`. The schema viewer renders this as a collapsible tree.

### get_deal_data input: Deal instance only

`get_deal_data(deal)` accepts a `Deal` instance only. The view fetches the deal before calling; the function does not accept `deal_id`. This keeps fetching at the view layer and the function focused on transformation.

### Debug Data page

A separate **"Debug Data"** menu item (sidebar) leads to a page that lists all deals in a table. Each row shows key deal info (e.g. date entered, lease officer) and has a **"View JSON"** button. Clicking it opens a **modal** that fetches and displays `get_deal_data(deal)` as formatted JSON. The modal includes a **Copy** button (clipboard) and can be easily closed. This keeps debug functionality out of the main user workflow (deal list, deal detail, edit, documents). Same data the context builder uses; useful for debugging and verifying what data is available for document generation. `@login_required`. Placement: e.g. after Document Templates or near Admin, or in a "Developer" section if one exists.

### Vehicles and contacts ordering

For `get_deal_data()` output, vehicles and contacts are ordered by `id` (`order_by('id')`). Django M2M has no intrinsic order; id order is stable and sufficient for v1. The context builder uses this order when resolving "first contact" or "first vehicle" (e.g. `deal.contacts[0]` = first element of the list).

### Single source of truth; no circumvention

This interface is the canonical source for schema and deal data. Document features must use `get_paths_grouped_for_mapping()` for deal paths in the Source dropdown and `get_deal_data()` for deal data. They must not traverse Django models or QuerySets for deal paths. Image variables are mapped via a separate Images optgroup (from the Image model) per ../06-DOCS/DESIGN-DOCS.md.

---

*End of design. Implementation follows PLAN files. See ../06-DOCS/DESIGN-DOCS.md for document templates, document sets, and signing.*

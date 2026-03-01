# Design: Documents for Deals

This document captures design decisions and concepts for handling documents related to a Deal. Implementation will follow in separate PLAN files.

---

## Scope

- Documents are associated with a Deal.
- Design covers concepts, data model, user flows, and integration points.
- No implementation here—PLAN files will describe implementation steps.
- The Internal Data Schema and Deal Data Retrieval interface are in **DESIGN-DATA-INTERFACE.md**; this document references them where relevant.

## Current Platform (Assumed)

This design assumes the platform already has:

- **Deals** — Deal model with lease officer, deal type (FK), vehicles and contacts (M2M), and deal properties (dates, payment, deposit, insurance, governing law). Deal Type "Lease - Single Signer" exists and is the default. The **deal detail page** (read-only summary) exists with Back, Edit, and Delete buttons; list links to detail via View (no Edit on list).
- **Vehicles** — Vehicle model with SKU, year, JPIN; full CRUD.
- **Contacts** — Contact model; full CRUD.
- **Images** — Image model with name, file, stable URL; full CRUD.

Plans 1–6 (PLAN-BASELINE through PLAN-ADD-DATA-INTERFACE) are implemented. This design extends the deal detail page with the Documents section and related features.

**Related design:** The Internal Data Schema and Deal Data Retrieval interface are documented in **DESIGN-DATA-INTERFACE.md**. Dynamic document templates use the schema for mapping and `get_deal_data(deal)` for population. The Debug Data page (deal list with View JSON) is also defined there.

---

## Deal Document Workflow

The workflow for a Deal is:

1. **Data entry** — Deal data is entered into the system.

2. **Finalization** — When the deal details are finalized and all necessary data is present, a **document set** is created.

3. **Document set contents** — The document set contains:
   - **Populated documents** — Documents generated from and populated with deal data.
   - **Required documents** — Static documents that must be acknowledged (e.g., disclosures, terms).

4. **Iterations** — Deal data may change. New versions of documents may be generated as the data evolves.

5. **Signing** — When the data is finalized and the deal is ready to be signed, the documents are sent to **SIGNiX** for electronic signing.

6. **Completion** — When the SIGNiX transaction is complete and all documents have been signed:
   - The app is notified.
   - Signed documents are downloaded from SIGNiX.
   - Those signed documents are stored as the **final versions** in the document set.

---

## Static Document Templates (First Implementation Step)

Static document templates are likely the first feature to implement. They are the reusable PDFs that become "required documents" in a document set (e.g., disclosures, advisories, terms).

### Concept

- A **static document template** is a PDF file that contains PDF form fields (AcroForm fields).
- Example fields: a signature field, and a date-of-signature field.
- Like the Images feature: upload the PDF file to the app.
- In addition to the file: store metadata that describes the form fields, so the app (and later SIGNiX integration) knows how to populate and handle them.

### Prototype Data Structure

From a previous prototype, the structure used was:

```json
{
    "ref_id": "ZoomJetPackSafetyAdvisory",
    "desc": "Zoom Jet Pack Safety Advisory",
    "file_name": "ZoomJetPackSafetyAdvisory.pdf",
    "mime_type": "application/pdf",
    "doc_source_type": "static",
    "doc_source_location": "zoom-safety-advisory.pdf",
    "tagging_type": "pdf_fields",
    "tagging_data": [
        {
            "tag_name": "SignatureField",
            "field_type": "signature",
            "member_info_number": 2,
            "date_signed_field_name": "DateField",
            "date_signed_format": "MM/dd/yy"
        }
    ]
}
```

### Field Definitions

| Field | Purpose |
|-------|---------|
| `ref_id` | Unique identifier for the template (e.g., for reference in document sets). |
| `desc` | Human-readable description. |
| `file_name` | Original filename. |
| `mime_type` | MIME type (e.g., `application/pdf`). |
| `doc_source_type` | `"static"` (vs. generated from deal data). |
| `doc_source_location` | Path/reference to the stored file. |
| `tagging_type` | How the document is tagged; `"pdf_fields"` means it uses PDF form fields. |
| `tagging_data` | Array of form-field definitions. |

Each item in `tagging_data`:

| Field | Purpose |
|-------|---------|
| `tag_name` | PDF form field name (must match the field in the PDF). |
| `field_type` | Type of field (e.g., `signature`, `date`, `text`). |
| `member_info_number` | Which signer (SIGNiX concept). See [Decisions Log](#decisions-log) for mapping. |
| `date_signed_field_name` | (For signature fields) PDF field name where the date is written. |
| `date_signed_format` | (For signature fields) Date format (e.g., `MM/dd/yy`). |

### Modeling in the App

- **Template-level:** A model (e.g., `StaticDocumentTemplate`) holds: `ref_id`, `description`, `file` (FileField), `mime_type` (or derived), `doc_source_type`, `tagging_type`, and possibly `doc_source_location` (or derive from file path).
- **Field-level:** `tagging_data` can be stored as:
  - **Option A:** `JSONField` — flexible, matches prototype; querying individual fields is harder.
  - **Option B:** Related model (e.g., `TemplateFormField`) — one row per field; easier to validate and query, more tables/joins.
- **Recommendation:** Start with `JSONField` for `tagging_data` to stay close to the prototype and iterate; normalize to a related model later if needed.

### UI for Entering Field Metadata

User-friendly flow:

1. **Upload** — User uploads the PDF (like Images).
2. **Template metadata** — User enters `ref_id`, description.
3. **Form field configuration** — User adds one or more field definitions. Options:
   - **Inline formset** — Add/remove rows; each row: tag_name, field_type, member_info_number, and (when field_type=signature) date_signed_field_name, date_signed_format.
   - **Step-by-step wizard** — Upload → metadata → add fields one by one.
   - **Single form with dynamic "Add field"** — Similar to formset but simpler; append new field blocks via JavaScript.

Considerations:
- `tag_name` must match the actual PDF field name; users enter it manually (see Decisions Log — auto-detection is a future enhancement).
- `field_type` as a dropdown: `signature`, `date`, `text`, etc.
- Conditional UI: show `date_signed_field_name` and `date_signed_format` only when `field_type` is `signature`.
- `member_info_number`: see Decisions Log — Signer 1 = deal user, Signer 2 = first contact; show as "User (lease officer)" / "Contact" in UI.

---

## Dynamic Document Templates (Likely Second Implementation Step)

Dynamic templates are HTML files containing Django Template Language (DTL). They are introduced after static templates and produce the **populated documents** in a document set.

### Concept

- A **dynamic document template** is an HTML file with DTL variables and tags (e.g., `{{ deal.payment_amount }}`, `{% for vehicle in vehicles %}`).
- At render time: combine the template with deal data (including vehicles, signers/contacts, lease officer) to produce a fully-populated HTML string.
- That HTML is then sent to an HTML-to-PDF feature to create a PDF.
- Templates may reference one or more **Images** from the Images app (logos, diagrams, etc.) — this is why the Images feature exists.

### Workflow

1. User uploads an HTML template file.
2. User (or system) configures the **mapping** of template variables to deal data.
3. At document-generation time: render template with deal context → HTML string → HTML-to-PDF → PDF.

### Required Features

- **Upload** — Users upload dynamic templates (HTML files), similar to static template uploads.
- **Mapping** — Parse DTL to extract template variables, use the Internal Data Schema (see DESIGN-DATA-INTERFACE.md) for available paths, provide a UI to map variables to data sources and transforms, and apply the mapping at render time. See [Template-to-Data Mapping](#template-to-data-mapping).
- **Signature and date fields** — Dynamic PDFs also need signature/date fields for SIGNiX. Because the PDF is generated from HTML (no pre-existing AcroForm fields), SIGNiX uses **text tagging**: anchor text in the document defines placement for field bounding boxes. See below.

### Signature and Date Fields via Text Tagging

Unlike static templates (which use existing PDF form fields), dynamic templates produce PDFs from rendered HTML. There are no native form fields in the output. **SIGNiX text tagging** solves this:

- The app specifies **anchor text** — a string that appears in the rendered document (e.g., `"LESSOR:"`, `"Date:"`).
- The app specifies a **bounding box** relative to that anchor: `x_offset`, `y_offset`, `width`, `height`.
- SIGNiX locates the anchor text in the PDF and places the field (signature or date) at the specified offset.
- This allows signature and date-signed fields to be placed in HTML-generated PDFs without modifying the PDF structure itself.

#### Prototype Data Structure (text tagging)

From a previous prototype:

```json
{
    "ref_id": "ZoomJetPackLease",
    "desc": "Zoom Jet Pack Lease",
    "file_name": "ZoomJetPackLease.pdf",
    "mime_type": "application/pdf",
    "doc_source_type": "dynamic",
    "doc_source_location": "zoom-lease-agreement.html",
    "tagging_type": "text_tagging",
    "tagging_data": [
        {
            "tag_name": "LesseeDate",
            "field_type": "date_signed",
            "is_required": "yes",
            "anchor_text": "Date:",
            "bounding_box": {
                "x_offset": 30,
                "y_offset": 0,
                "width": 90,
                "height": 12
            }
        },
        {
            "tag_name": "LessorDate",
            "field_type": "date_signed",
            "is_required": "yes",
            "anchor_text": "As",
            "bounding_box": {
                "x_offset": 30,
                "y_offset": 0,
                "width": 90,
                "height": 12
            }
        },
        {
            "tag_name": "Lessor",
            "field_type": "signature",
            "is_required": "yes",
            "anchor_text": "LESSOR:",
            "bounding_box": {
                "x_offset": 150,
                "y_offset": 6,
                "width": 120,
                "height": 24
            },
            "member_info_number": 1,
            "date_signed_field_name": "LessorDate",
            "date_signed_format": "MM/dd/yy"
        },
        {
            "tag_name": "Lessee",
            "field_type": "signature",
            "is_required": "yes",
            "anchor_text": "LESSEE:",
            "bounding_box": {
                "x_offset": 45,
                "y_offset": 6,
                "width": 120,
                "height": 24
            },
            "member_info_number": 2,
            "date_signed_field_name": "LesseeDate",
            "date_signed_format": "MM/dd/yy"
        }
    ]
}
```

#### Field Definitions (text tagging)

Each item in `tagging_data` for `tagging_type: "text_tagging"`:

| Field | Purpose |
|-------|---------|
| `tag_name` | Unique field name for SIGNiX (e.g., `Lessor`, `LesseeDate`). |
| `field_type` | `signature` or `date_signed`. |
| `is_required` | Whether the field is required (e.g., `"yes"`). |
| `anchor_text` | Text string in the document used to locate the field placement. Must appear in the rendered HTML/PDF. |
| `bounding_box` | `x_offset`, `y_offset`, `width`, `height` — position and size relative to the anchor. |
| `member_info_number` | (Signature fields only) Which signer — 1 = user, 2 = contact. See [Decisions Log](#decisions-log). |
| `date_signed_field_name` | (Signature fields only) `tag_name` of the `date_signed` field where the signature date is written. |
| `date_signed_format` | (Signature fields only) Date format (e.g., `MM/dd/yy`). |

**Note:** Template authors must ensure the anchor text appears in the rendered HTML. For example, the HTML might include `<span>LESSOR:</span>` or a label "Date:" so SIGNiX can find it.

### Template-to-Data Mapping

Dynamic templates expect a context dict (e.g., `data`) whose structure may differ from the Deal/Vehicle/Contact models. A **mapping feature** specifies how template variables are populated from deal data. The mapping UI is integrated into the template upload/edit flow.

The mapping feature **consumes the Internal Data Schema** (see DESIGN-DATA-INTERFACE.md). Available data paths come from the schema interface (`get_schema()` / `get_paths()`), not from ad-hoc model introspection. This keeps schema discovery in one place and ensures consistency across the mapping UI, context builder, and schema viewer page.

#### Flow

1. User uploads an HTML template.
2. System parses DTL and extracts variable references (e.g., `data.payment_amount`, `data.jet_pack_list`, `item.sku`).
3. System obtains available data paths from the schema interface (`get_paths()`).
4. User maps each template variable to a data source (schema path or transform).
5. Mapping is stored with the template (e.g., JSONField).
6. At render time: the context builder calls `get_deal_data(deal)` (see DESIGN-DATA-INTERFACE.md) to obtain deal data, applies the mapping and transforms to build the template context, then renders the template with that context.

#### DTL Parsing

- Walk Django's parsed `Template` node tree to collect:
  - Variable nodes: `{{ data.payment_amount }}`, `{{ item.sku }}`
  - Loop iterables and loop variables: `{% for item in data.jet_pack_list %}` → `data.jet_pack_list`, `item`
- Filters do not change the base variable: `{{ data.payment_amount|floatformat:2 }}` → `data.payment_amount`.
- **Scope:** Single-level loops and flat variables. `{% include %}` and custom template tags are best-effort or out of scope for v1.

#### Schema as Source of Paths

- The mapping UI and context builder use the **Internal Data Schema** (see DESIGN-DATA-INTERFACE.md), not ad-hoc model introspection.
- **No circumvention:** The mapping UI obtains paths from `get_paths()` only. The context builder obtains deal data from `get_deal_data(deal)` only. Neither may traverse Django models or QuerySets directly.
- The schema defines valid paths such as `deal.payment_amount`, `deal.date_entered`, `deal.lease_start_date`, `deal.lease_officer`, `deal.vehicles`, `deal.contacts`, `deal.vehicles.item.sku`, `deal.contacts.item.first_name`, etc.
- The schema service (in `apps.schema`) builds this tree via introspection; document features consume it through `get_paths()` and `get_deal_data()`.

#### Mapping Types

| Type | Example | Implementation |
|------|---------|----------------|
| **Direct** | `data.payment_amount` → `deal.payment_amount` | Pass-through from path in `get_deal_data()` output. |
| **Date part** | `data.entered_day` → day of `deal.date_entered` | Transform: extract day, month, or year from date value in `get_deal_data()` output. |
| **Concatenate** | `data.lessee_name` → first contact's `first_name + " " + last_name` | Transform: join fields from an object in the `get_deal_data()` output (e.g. first element of `deal.contacts` list). |
| **List** | `data.jet_pack_list` → `deal.vehicles`; `item.sku` → `Vehicle.sku` | Map list source and per-item fields from `get_deal_data()` output. |
| **List-derived** | `data.number_of_items_number` → count of `deal.vehicles` | Transform: count items in the list from `get_deal_data()` output (e.g. `len(deal_data["deal"]["vehicles"])`). |
| **Number-as-word** | `data.number_of_items_text` → "one", "two", etc. | Transform: integer to English word. |
| **Plural suffix** | `data.number_of_items_inflection` → "" or "s" | Transform: "" if count is 1, "s" otherwise. |

#### Transforms (Built-in)

The mapping UI offers a fixed set of transforms. Each mapping entry specifies: template variable, data source (schema path), and optional transform. Transforms operate on values from the `get_deal_data(deal)` output; the context builder applies them when building the template context.

| Transform | Input | Output | Use case |
|-----------|-------|--------|----------|
| (none) | Value from `get_deal_data()` output | As-is | Direct fields |
| `date_day` | DateField | Day as int (1–31) | `data.entered_day` |
| `date_month` | DateField | Month as int (1–12) or name | `data.entered_month` |
| `date_year` | DateField | Year as int | `data.entered_year` |
| `concat` | Multiple text fields | Joined string (e.g., first + last name) | `data.lessee_name` |
| `count` | List (from `get_deal_data` output) | Integer count | `data.number_of_items_number` |
| `number_to_word` | Integer | "one", "two", etc. | `data.number_of_items_text` |
| `plural_suffix` | Integer | "" or "s" | `data.number_of_items_inflection` |

Additional date-part transforms (e.g., `date_month_name`, `date_day_month` for "January 15") can be added as needed.

#### Reference Template Structure (Demo)

The design targets templates like the Zoom Jet Pack Lease Agreement: a single top-level object (e.g., `data`) with flat properties and one list.

- **Flat:** `data.entered_day`, `data.entered_month`, `data.entered_year`, `data.lessee_name`, `data.payment_amount`, `data.lease_start_day_month`, etc.
- **List:** `data.jet_pack_list` with `{% for item in data.jet_pack_list %}`; each `item` has `sku`, `year`, `jpin` (mapping to Vehicle).
- **Computed from list:** `data.number_of_items_number`, `data.number_of_items_text`, `data.number_of_items_inflection`.

Static assets (e.g., `{% static '...' %}`) are handled separately; the mapping feature focuses on deal data.

#### Mapping Storage

- Store as a JSON config, e.g.:
  ```json
  {
    "data.payment_amount": { "source": "deal.payment_amount" },
    "data.entered_day": { "source": "deal.date_entered", "transform": "date_day" },
    "data.lessee_name": { "source": "deal.contacts[0]", "transform": "concat", "fields": ["first_name", "last_name"] },
    "data.jet_pack_list": { "source": "deal.vehicles", "item_map": { "sku": "sku", "year": "year", "jpin": "jpin" } },
    "data.number_of_items_number": { "source": "deal.vehicles", "transform": "count" }
  }
  ```
- Exact schema can be refined during implementation.

#### Implementation Scope (v1)

- **Supported:** Flat variables, single-level `{% for item in list %}` loops, direct mappings, and the transforms listed above.
- **Out of scope for v1:** Nested loops, `{% include %}`, custom template tags, computed expressions beyond the transform set.

---

## Document Set Templates (and Document Sets)

A **Document Set** is attached to a Deal and contains the documents produced for that deal (lease agreement, safety advisory, etc.). A **Document Set Template** specifies *which* Document Templates (Static or Dynamic) are used to create those documents, and in what order.

### Concept

- A **Document Set Template** defines an ordered list of Document Templates (Static and/or Dynamic).
- When a user creates a Document Set for a Deal, the system uses the appropriate Document Set Template to determine which templates to instantiate.
- Document Set Templates are associated with **Deal Types**. The Deal Type on the Deal determines which Document Set Template is used.

### Deal Type Association

- **Deal Type** — A classification of the deal (e.g., lease, cash purchase, early lease termination, trade-in). The Deal model has an explicit `deal_type` field. Deal Type is already implemented as part of PLAN-ADD-DEALS and is in place.
- **Initial release:** There is exactly one Deal Type: **"Lease - Single Signer"**. All deals default to this type. No UI for the user to select deal type.
- **Future:** When multiple Deal Types exist, the user will select the deal type (e.g., when creating or editing a Deal). Each Deal Type may use a different Document Set Template. Document Set Templates may also vary by number of co-signers or signer roles (e.g., guarantor vs. primary signer).

### Template Reusability

- The same Document Template (Static or Dynamic) can appear in multiple Document Set Templates. For example, the safety advisory may be used in both lease and cash-purchase document sets.

### Initial Release Configuration

- One Deal Type: **"Lease - Single Signer"** (explicit, default for all deals).
- One Document Set Template for "Lease - Single Signer", containing (in order):
  1. **Dynamic Template** — The lease agreement (populated from deal data)
  2. **Static Template** — The safety advisory (required acknowledgment)

### Required Features

- **UI to configure Document Set Templates** — Select Document Templates (Static and Dynamic) and put them in order. Associate the Document Set Template with a Deal Type. All templates in a Document Set Template are required.

### Admin Configuration Flow

**UI pattern:** Use the same pattern as Deals, Vehicles, and Contacts—list, add, edit, delete views with sidebar links.

**Setup order:** Per PLAN-MASTER, plans 1–6 (Baseline, Vehicles, Contacts, Deals, Images, Data Interface) are implemented before document features. The **data interface** (apps.schema: `get_schema()`, `get_paths()`, `get_deal_data(deal)`) per DESIGN-DATA-INTERFACE.md and PLAN-DATA-INTERFACE is in place. For document features:

1. Create **Static Document Templates** — Upload PDF, add field metadata (ref_id, description, tagging_data).
2. Create **Dynamic Document Templates** — Upload HTML, configure mapping (uses `get_paths()` from apps.schema) and text tagging; context builder uses `get_deal_data(deal)` from apps.schema.
3. Create **Document Set Templates** — Associate with Deal Type, add templates in order.

All templates listed in a Document Set Template are required. The admin configures templates; users work with deals and system-generated documents.
- **Workflow:** When the user is ready to create the Document Set for a Deal, the system:
  1. Determines the Deal Type (e.g., "Lease - Single Signer")
  2. Looks up the Document Set Template associated with that Deal Type
  3. Uses the template's ordered list of Document Templates to create the documents in the Document Set

### Future Extensibility

- Additional Deal Types (cash purchase, early termination, trade-in) — each with its own Document Set Template.
- Document Set Templates may vary by number of co-signers (different templates for 1 vs. 2+ signers).
- Signer roles (guarantor, primary, etc.) may influence which Document Templates are included.
- Additional signer roles, co-signer variants, etc.

---

## Document Sets, Document Instances, and Document Instance Versions

### Structure

- **Document Set** — Attached to a Deal. Contains an ordered list of **Document Instances**.
- **Document Instance** — One document in the set (e.g., lease agreement or safety advisory). Has an ordered list of **Document Instance Versions**.
- **Document Instance Version** — A version of the document (e.g., draft v1, draft v2, signed). Numbered sequentially, has a creation timestamp, and a **Status** field.

### Document Set Fields

- `deal` — FK to the Deal
- `document_set_template` — FK to the Document Set Template last used to initially create it (for traceability)

### Document Instance Fields

- `document_set` — FK to the parent Document Set
- `source_document_template` — FK to the Document Template (Static or Dynamic) this instance was created from
- `template_type` — Display field indicating whether the source is "static" or "dynamic"
- Order within the Document Set (e.g., `order` or `position` field)

### Document Instance Version Fields

- `document_instance` — FK to the parent Document Instance
- `version_number` — Sequential (1, 2, 3, …)
- `created_at` — Timestamp
- `status` — See [Status flow](#status-flow) below
- `file` — The PDF file (FileField)

### Creation Flow (Generate Documents)

Documents are created when the Deal has **sufficient data**: all Deal fields have values, and there is at least one vehicle, one user (lease officer), and one signer (contact). The system:

1. Determines the Deal's Deal Type and looks up the associated Document Set Template
2. Creates a Document Set for the Deal, linking it to that Document Set Template
3. Iterates through the Document Set Template's ordered list of Document Templates:
   - **Dynamic template:** Obtain deal data via `get_deal_data(deal)` (DESIGN-DATA-INTERFACE.md); build template context from mapping and transforms; render HTML/DTL with deal context; images via static references (see [Image references](#image-references-in-dynamic-templates)) → render to HTML → convert to PDF (pdfkit/wkhtmltopdf) → store the PDF in a new Document Instance Version
   - **Static template:** Copy the static PDF from the template to a new Document Instance Version
4. For each template, creates a Document Instance (with link to source template, template_type) and adds the first Document Instance Version with status "Draft"

**Atomicity:** If Document Set creation fails at any step (e.g., template render error, PDF generation failure), roll back all Document Instance creation and Document Instance Versions. The Document Set (if created) should also be rolled back so the Deal is left in a consistent state.

**Error handling and logging:** Include sufficient logging and error handling so that if an error occurs, the cause can be diagnosed and the fix determined. Log failures at each step (template lookup, context build, render, PDF conversion, file storage) with enough context to understand what went wrong.

### Re-generation Flow (Regenerate Documents)

When deal data changes, documents can be re-drawn. The same generation process runs, but the results are stored as *subsequent* Document Instance Versions (version 2, 3, …) on the existing Document Instances—not replacements. Previous versions remain for history.

### Status Flow

| Status | When |
|--------|------|
| **Draft** | Generated documents (initial or re-generated) |
| **Submitted to SIGNiX** | Document Set is packaged and sent to SIGNiX for signing |
| **Final** | When SIGNiX completes: a *new* Document Instance Version is created to hold the signed PDF. |

The SIGNiX notification mechanism (how the app learns a transaction is complete) will be discussed in the SIGNiX integration design.

### User Experience

The goal is to automate as much as possible. Use language users will understand: **Documents** and **Versions** (rather than "Document Instance" and "Document Instance Version") in the UI.

**Deal page layout:**
- The deal detail page (read-only summary with Back, Edit, Delete) already exists. The Documents section will be added at the **bottom of this page**. (Layout may be refined during implementation—e.g., tabs or other restructuring.) Debug data viewing is on a separate "Debug Data" page (see DESIGN-DATA-INTERFACE.md), not on the deal detail page.

**Deal page — before Document Set exists:**
- **"Generate Documents"** button — Enabled when Deal has sufficient data (all Deal fields populated; at least one vehicle, one user/lease officer, one signer/contact). Creates Document Set, Document Instances, and first Document Instance Versions automatically.
- **"Send for Signature"** — **Inactive** when there are no documents yet.

**Deal page — after Document Set exists:**
- **"Regenerate Documents"** — Re-runs generation; adds new Document Instance Versions to existing Document Instances. Available even after sending to SIGNiX—if deal data must change after documents were sent, the existing SIGNiX transaction is cancelled, and the new documents (in the later Document Instance Versions) are eligible for packaging and re-sending to SIGNiX.
- **"Delete Document Set"** — Removes the Document Set and its contents.
- **"Send for Signature"** — **Active** when documents exist. Packages documents and data for SIGNiX, sends the transaction. Updates Document Instance Version status to "Submitted to SIGNiX".
- **Documents table** — Each row shows:
  - Document name (from source template—e.g., "Lease Agreement", "Safety Advisory")
  - Latest version info (version number, status, creation date)
  - **View latest** — Opens the latest version's PDF (easy one-click access)
  - **View all versions** — Opens the Document Instance page to see and view prior versions
- The latest Document Instance Version should be easy to view, and when it was created should be easy to see.

**Document Instance page (View all versions):**
- Versions listed in **descending order** (latest first).
- **Latest** indicator in the table for the current latest version.
- Each version: version number, status, creation date; **View** and **Download** options.
- **View** — Opens the PDF in an in-browser viewer (e.g., new window or tab).
- **Download** — Downloads the PDF file.

**SIGNiX completion (automated):**
- When the app is notified by SIGNiX that a transaction is completed, it automatically downloads the signed documents and creates new Document Instance Versions (status: **Final**) to hold them. (SIGNiX notification details in SIGNiX integration design.)

---

## Open Questions / Design Decisions

*(None at present.)*

---

## Decisions Log

### member_info_number (signer mapping)

`member_info_number` is a SIGNiX concept; full SIGNiX details will be addressed during SIGNiX integration. For now:

| Value | Maps to |
|-------|---------|
| 1 | The **user** (lease officer) on the deal |
| 2 | The **(first) contact** on the deal |

A future version may support multiple contacts/signers, but the current design assumes exactly two signers: user and first contact.

### PDF field detection

PDF field auto-detection (reading form field names from the uploaded PDF) is a desired future enhancement. For the initial implementation, assume users are tech-savvy and will provide the necessary field details (e.g., `tag_name`, `field_type`) manually through the app's UI.

### Image references in dynamic templates

Images are referenced in dynamic templates using **static references**—e.g., the URL/path from the Images app (see PLAN-ADD-IMAGES.md). Each image has a stable, HTTP-accessible URL (e.g., `/media/images/…`) that can be used in the template. Images should be available to pdfkit/wkhtmltopdf via this public link; if not, the solution will be addressed during implementation.

### HTML-to-PDF generation

For the first release, use **pdfkit** with **wkhtmltopdf** installed. This was used in an earlier prototype and worked well. A different technology may be chosen in a future release.

### Deal Type (initial release)

Deal Type is explicit on the Deal model and is implemented. The platform has one Deal Type: **"Lease - Single Signer"**. All deals default to this type; there is no UI for the user to select deal type. When multiple Deal Types are introduced in a later release, the user will select the deal type (e.g., when creating or editing a Deal).

### Document template reusability

The same Document Template (Static or Dynamic) can appear in multiple Document Set Templates. For example, the safety advisory may be included in both lease and cash-purchase document sets.

### Sufficient data (for Generate Documents)

A Deal has sufficient data when: all Deal fields have values, and there is at least one vehicle, one user (lease officer), and one signer (contact).

### Regenerate Documents after SIGNiX

The Regenerate Documents button remains available after documents have been sent to SIGNiX. If deal data must change post-send, the existing SIGNiX transaction is cancelled; the newly generated documents (in later Document Instance Versions) can then be packaged and re-sent to SIGNiX.

### Document Instance Version status: Final

Document Instance Versions created when signed documents are downloaded from SIGNiX have status **Final**.

### Admin UI pattern

Document Templates (Static and Dynamic) and Document Set Templates use the same UI pattern as Deals, Vehicles, and Contacts: list, add, edit, delete views with sidebar links.

### Configuration setup order

Per PLAN-MASTER: plans 1–6 (including Data Interface) are implemented first; then document plans in PLAN-DOCS-MASTER order. The data interface (apps.schema: `get_schema()`, `get_paths()`, `get_deal_data(deal)`) per DESIGN-DATA-INTERFACE.md is implemented in PLAN-DATA-INTERFACE before Dynamic Document Templates. Admin creates Static and Dynamic Document Templates, then Document Set Templates that reference them. Deal Type is already implemented as part of Deals (PLAN-ADD-DEALS); no separate setup step.

### Document Set Template: all templates required

All templates listed in a Document Set Template are required. (Future releases may support optional templates.)

### Document Instances and Versions: view-only

Document Instances and Document Instance Versions are created by system automation (Generate Documents, Regenerate Documents, SIGNiX completion). Users view them; there is no Edit UI for Document Instances or Document Instance Versions.

### Deal View / Edit split

Deals use a **View / Edit split**: the primary entry point from the list is **View** (deal detail page), not Edit. From the deal detail page, the user can Edit or Delete. Flow: List → View (detail) → Edit or Delete from there. This is implemented in **PLAN-ADD-DEALS** (deal_detail view, list links to detail, Edit and Delete buttons on detail). PLAN-ADD-DOCUMENT-SETS extends the deal detail page with the Documents section.

### Document viewing UX

- Use user-friendly language in the UI: **Documents** and **Versions** (not "Document Instance", "Document Instance Version").
- Documents table on Deal page: document name, latest version info (version, status, date), "View latest" (one-click), "View all versions" (opens version history).
- Versions listed in descending order (latest first); show "Latest" indicator.
- View: in-browser PDF viewer (e.g., new window). Download: file download.
- "Send for Signature" active when documents exist, inactive when no documents.
- Documents section at bottom of Deal page (layout may be refined during implementation).

### First contact / first vehicle (ordering)

For mappings that use "first contact" or "first vehicle" (e.g., `data.lessee_name` from the first contact), use the order defined by `get_deal_data()` (vehicles and contacts ordered by id per DESIGN-DATA-INTERFACE.md). The context builder resolves `deal.contacts[0]` as the first element of the `contacts` list in that output. A future release may provide a UI to change this order. For the initial release, this is not material—vehicle order is not critical, and the demo will have only one signer.

### Document Set creation: atomicity and error handling

If Document Set creation fails at any step, roll back all Document Instance creation and Document Instance Versions. Include sufficient logging and error handling so that if an error occurs, the cause can be diagnosed and the fix determined.

### Data interface: no circumvention

Dynamic document mapping and population must use the data interface (DESIGN-DATA-INTERFACE.md) exclusively. The mapping UI obtains paths from `get_paths()` only. The context builder obtains deal data from `get_deal_data(deal)` only. Neither may traverse Django models or QuerySets directly. This ensures a single source of truth and keeps document features decoupled from model structure.

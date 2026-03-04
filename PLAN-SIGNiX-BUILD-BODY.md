# Plan: Build SubmitDocument Body (Plan 5)

This document outlines how to implement **building the SubmitDocument request body (XML)** from a deal, document set, and configuration—without sending to SIGNiX. This enables unit testing of the payload and debugging (e.g. dump XML). The send step and persistence are in Plan 6.

**Design reference:** DESIGN-SIGNiX-SUBMIT.md — Section 6 (Transaction Packager), Section 6.1.1 (SubmitDocument data sourcing), Section 6.4 (Separation of body construction and send). KNOWLEDGE-SIGNiX.md — SubmitDocument structure, template approach, Form/Base64, escaping and `| safe`.

**Prerequisites:** Plans 1 (SignixConfig, get_signix_config), 3 (signer service, resolve_signer_slot, get_signers_for_document_set_template), and 4 (signer order/auth storage, get_signer_order_for_deal, get_signer_authentication_for_slot) are implemented. Document Sets with instances and latest versions (PLAN-ADD-DOCUMENT-SETS). Plan 2 (SignatureTransaction) is not required for building the body but is required for Plan 6.

**Review this plan before implementation.** Implementation order is in **Section 7**; **Section 7a** defines batches and verification.

---

## 1. Goals and Scope

- **`build_submit_document_body(deal, document_set, ...)`** — Build the full SubmitDocument request XML string from deal, document_set, and stored configuration. No HTTP is performed. Uses SignixConfig (CustInfo, submitter, Data-level defaults), signer order and authentication (Plan 4), slot→person resolution (Plan 3), document_set instances and latest-version PDFs, and template `tagging_data` for Form structure. All data sourcing per DESIGN-SIGNiX-SUBMIT Section 6.1.1.
- **Validation** — A validation helper used by this function (and by the Plan 6 orchestrator) ensures: document set belongs to deal; at least one instance present; each instance has a latest version with a file; every signer slot from the document set template is resolved to a person; SignixConfig is present with submitter email. On validation failure, do not build body; surface errors to caller.
- **Django template (DTL)** — Request XML is produced by rendering a Django template with a data dict. Only intentionally embedded XML (e.g. Form content) is marked `| safe`; all other values are escaped.
- **Return value** — Function returns the XML string and optionally metadata (e.g. client-chosen TransactionID) so Plan 6 can persist it on SignatureTransaction.
- **Unit tests** — Assert on structure and key values in the built XML (no HTTP). Optional: management command or debug view to dump body without sending.
- **Out of scope:** POST to SIGNiX, response parsing, GetAccessLink, creating SignatureTransaction, updating DocumentInstanceVersion status (Plan 6).

---

## 2. Validation

A single validation step must pass before building the body. The same validation is used by the Plan 6 orchestrator so submit is not attempted when preconditions fail.

**Validation rules:**

1. **document_set** is not None.
2. **document_set.deal_id == deal.pk** (document set belongs to deal).
3. **document_set.document_set_template** is not None (template required for signer list and Form building).
4. **At least one instance:** `document_set.instances.exists()`.
5. **Per instance:** Has a latest version (e.g. `instance.versions.order_by("-version_number").first()`); that version has a non-empty `file` (file has been generated and saved).
6. **Signer slots resolved:** For the template's signer slots (from `get_signers_for_document_set_template(document_set.document_set_template)`), each slot must resolve to a person: `resolve_signer_slot(deal, slot)` is not None for every slot in the effective signer order.
7. **SignixConfig:** `get_signix_config()` returns a config with **submitter_email** non-empty (and optionally all five credentials non-empty for a "valid for submit" check; design requires submitter email for submit).

**Error handling:**

- Implement a **validation function** that either:
  - **Option A:** Returns `(True, None)` on success and `(False, list_of_error_messages)` on failure; caller decides whether to raise or return.
  - **Option B:** Raises a custom exception (e.g. `SignixValidationError`) with a list of error messages on failure; no return value on success (caller proceeds to build).

- **Recommendation:** Use **Option B** — raise `SignixValidationError` (subclass of `ValueError` or a custom base) with attribute `errors: list[str]`. The orchestrator (Plan 6) can catch it and return a user-facing message without making an HTTP call. Simplifies the "validate then build" flow.

**Signature:** `validate_submit_preconditions(deal, document_set) -> None` (raises `SignixValidationError` with `errors` list on failure).

**Location:** Same module as build body, e.g. `apps.deals.signix`.

---

## 3. Data Dict Structure

The Django template is rendered with a single data dict. Structure below matches DESIGN 6.1.1 and KNOWLEDGE-SIGNiX example.

### 3.1 CustInfo (from SignixConfig)

| Key | Source |
|-----|--------|
| `cust_info.sponsor` | config.sponsor |
| `cust_info.client` | config.client |
| `cust_info.userId` | config.user_id |
| `cust_info.password` | config.password |
| `cust_info.workgroup` | config.workgroup |
| `cust_info.demo` | config.demo_only — render as `"true"` or `"false"` per Flex API |
| `cust_info.del_docs_after` | config.delete_documents_after_days |
| `cust_info.email_content` | config.default_email_content |

### 3.2 Data (transaction and submitter)

| Key | Source / rule |
|-----|----------------|
| `transaction_data.transactionId` | Client-chosen; **max length 36 characters** in **standard UUID format** (e.g. `uuid.uuid4()` → `"550e8400-e29b-41d4-a716-446655440000"`). Unique per transaction; Plan 6 persists it on SignatureTransaction. |
| `transaction_data.doc_set_description` | `"Deal #<deal_id> - <template_name>"`; use **ASCII hyphen** between parts to avoid encoding issues in signer email subject. Template name from same as above. Escape for XML if needed (Django escapes by default). |
| `transaction_data.filename` | If Flex API requires a single FileName at Data level: use first document's template `ref_id` + `.pdf` (e.g. `ZoomJetPackLease.pdf`), or omit per API. Per-Form filename: use that Form's source template `ref_id` + `.pdf`. See Section 9. |
| `transaction_data.contact_info` | Omit or config submitter email/phone per design. |
| `transaction_data.delivery_type` | Use **`"SDDDC"`** when Flex requires DeliveryType (valid enum). |
| `transaction_data.suspend_on_start` | `"false"` (constant). |
| `submitter.email` | config.submitter_email |
| `submitter.name` | config.submitter_first_name + middle + last, trimmed, space-separated (blank if all empty). |
| `submitter.phone` | config.submitter_phone or default `"800-555-1234"` when blank and required. |

### 3.3 Signers (MemberInfo)

- **Order:** Use **effective signer order**: `get_signer_order_for_deal(deal, document_set.document_set_template)`. First in list = first MemberInfo = first signer in SIGNiX workflow.
- **Per signer (in that order):** Resolve person with `resolve_signer_slot(deal, slot)` and auth with `get_signer_authentication_for_slot(deal, slot)`. Validation already ensured no None.

**List `data.signers`** — each item a dict:

| Key | Source |
|-----|--------|
| `first_name` | person.first_name |
| `middle_name` | person.middle_name or `""` |
| `last_name` | person.last_name |
| `email` | person.email |
| `phone` | person.phone (required for SMSOneClick; send in MemberInfo as MobileNumber). |
| `service` | Auth type: `"SelectOneClick"` or `"SMSOneClick"` from get_signer_authentication_for_slot |
| `sms_count` | `1` for SMSOneClick, `0` for SelectOneClick (schema requires SMSCount; order per Flex: Service then MobileNumber then SMSCount). |
| `ssn` | Default `"910000000"` (design 6.1.1). |
| `dob` | Default `"01/01/1990"` — **MM/DD/YYYY** format (Flex DateType); placeholder for SelectOneClick/SMSOneClick. |
| `ref_id` | Role or position, e.g. `"Signer 1"`, `"Signer 2"` or from get_role_label_for_slot; implementation choice. |

### 3.4 Form (documents)

- **One Form per document instance** — order by `document_set.instances.order_by("order")`.
- **Branch on template type:** **StaticDocumentTemplate** → AcroForm path (SignatureLine, SignField, optional DateSignedField/DateSignedFormat). **DynamicDocumentTemplate** → text-tagging path (TextTagField, TextTagSignature).
- **Per Form:** Document identifier and filename from the instance's **source template `ref_id`** + `.pdf` (e.g. `ZoomJetPackLease.pdf`). **Tag definitions** from that template's `tagging_data`; **document content** = base64-encoded bytes of latest version's `file`. The Form XML structure (element names, order, attributes) follows the **Flex API SubmitDocument request XML** specification.

- **Static (AcroForm):** Form elements per schema: **RefID**, **Desc**, **FileName**, **MimeType**, **SignatureLine(s)** (each with MemberInfoNumber, **SignField** = PDF AcroForm field name, and optional **DateSignedField** / **DateSignedFormat** when tagging_data has date_signed_field_name), **Length**, **Data**. When tag_name is missing in tagging_data, use **signature_field_names** on StaticDocumentTemplate if present (e.g. mapping member to field name); otherwise default Lessor for member 1, Lessee for member 2.
- **Dynamic (text-tagging):** Form elements: RefID, Desc, FileName, MimeType, then **TextTagField** entries (e.g. Type DateSigned, AnchorText, bounding box, TagName) and **TextTagSignature** entries (MemberInfoNumber, anchor, box, optional DateSignedTagName/DateSignedFormat) from tagging_data. Emit **date fields before signature tags** (SIGNiX requirement).
- **Template rendering:** The Form XML fragment for all documents is built in Python (one concatenated string per document) and passed into the main Django template as `data.form` rendered with `| safe` (KNOWLEDGE-SIGNiX).

**Building Form XML from tagging_data (mapping):**

- **Static (PDF form fields):** Each entry in `tagging_data` has at least tag_name (or SignField), field_type, member_info_number; optional date_signed_field_name, date_signed_format. Map to SignatureLine with SignField and optional DateSignedField/DateSignedFormat; member_info_number maps to MemberInfoNumber.
- **Dynamic (text-tagging):** Each entry has field_type (date_signed or signature), anchor_text, bounding_box (x_offset, y_offset, width, height), member_info_number; for signature, optional date_signed_field_name, date_signed_format. Map to TextTagField (DateSigned) or TextTagSignature; emit date tags first, then signature tags.
- **Document content:** Read `latest_version.file.open("rb").read()`, encode with `base64.b64encode(bytes).decode("ascii")`. Wrap in the Form's `<Length>` / `<Data>` (or equivalent) per Flex API.

---

## 4. Django template (DTL)

- **Location:** e.g. `apps/deals/templates/signix/submit_document_request.xml` or `templates/signix/submit_document_rq.xml`. Use a path under the app or project templates so the Django template loader finds it.
- **Structure:** Follow the KNOWLEDGE-SIGNiX example: root `SubmitDocumentRq` with xmlns, `CustInfo`, `Data` (TransactionID, DocSetDescription, SubmitterEmail, SubmitterName, ContactInfo, DeliveryType e.g. SDDDC, SuspendOnStart, then loop over signers for MemberInfo in **schema order**: RefID, SSN, DOB, FirstName, MiddleName, LastName, Email, Service, MobileNumber, SMSCount, then `{{ data.form | safe }}`).
- **Escaping:** All `{{ ... }}` values are escaped by Django except `data.form`, which is intentionally XML and passed with `| safe`. Do not use `| safe` on user-controlled text (names, emails, IDs).
- **Demo:** CustInfo uses `{{ data.cust_info.demo }}` — ensure the value is the string `"true"` or `"false"` as required by the API.
- **File name:** Use the document (template) name: **template `ref_id` + `.pdf`** (e.g. `ZoomJetPackLease.pdf`) per document. If the API expects a single FileName at Data level, use the first document's filename or omit per API; if per-Form, use `ref_id.pdf` for each Form.

Reference template snippet (DTL; align with Flex API doc):

```xml
<?xml version="1.0" ?>
<SubmitDocumentRq xmlns="urn:com:signix:schema:sdddc-1-1">
    <CustInfo>
        <Sponsor>{{ data.cust_info.sponsor }}</Sponsor>
        ...
    </CustInfo>
    <Data>
        <TransactionID>{{ data.transaction_data.transactionId }}</TransactionID>
        <DocSetDescription>{{ data.transaction_data.doc_set_description }}</DocSetDescription>
        ...
        {% for signer in data.signers %}
        <MemberInfo>
            <RefID>{{ signer.ref_id }}</RefID>
            <SSN>{{ signer.ssn }}</SSN>
            <DOB>{{ signer.dob }}</DOB>
            <FirstName>{{ signer.first_name }}</FirstName>
            ...
            <Email>{{ signer.email }}</Email>
            <Service>{{ signer.service }}</Service>
            <MobileNumber>{{ signer.phone }}</MobileNumber>
            <SMSCount>{{ signer.sms_count }}</SMSCount>
        </MemberInfo>
        {% endfor %}
        {{ data.form | safe }}
    </Data>
</SubmitDocumentRq>
```

---

## 5. build_submit_document_body

**Signature:** `build_submit_document_body(deal, document_set) -> tuple[str, dict]`

- **Inputs:** `deal` (Deal), `document_set` (DocumentSet). Config and signer data are read from the database (get_signix_config, get_signer_order_for_deal, resolve_signer_slot, get_signer_authentication_for_slot).
- **Behavior:**
  1. Call `validate_submit_preconditions(deal, document_set)`. If it raises, propagate (caller handles).
  2. Load config: `get_signix_config()`.
  3. Build data dict (CustInfo, Data, signers, Form fragments) per Section 3. Form fragments built by iterating `document_set.instances.order_by("order")`, resolving source template (instance's GenericForeignKey), reading latest version file, base64-encoding, and building Form XML per Flex API from template's tagging_data.
  4. Render Django template with data dict.
  5. Return `(xml_string, metadata)` where metadata contains at least `transaction_id` (the client-chosen TransactionID) so Plan 6 can persist it on SignatureTransaction.

**Location:** `apps.deals.signix`.

---

## 6. TransactionID and DocSetDescription

- **TransactionID:** **Max length 36 characters**, **standard UUID format** (e.g. `str(uuid.uuid4())`). Unique per transaction; used for idempotency and correlation. No slug or timestamp format—UUID satisfies length and uniqueness.
- **DocSetDescription:** `"Deal #<deal_id> - <template_display_name>"`. Use **ASCII hyphen** between parts; template name or deal type name; human-readable (no length constraint like TransactionID).

---

## 7. Implementation Order (Checklist)

### Batch 1 — Validation and data dict (steps 1–4)

1. **SignixValidationError and validate_submit_preconditions**
   - In `apps/deals/signix.py`, define `SignixValidationError(Exception)` with `errors: list[str]`. Implement `validate_submit_preconditions(deal, document_set)` that checks all rules in Section 2 and raises with a list of messages (e.g. "Document set has no instances", "Signer slot 2 could not be resolved to a person", "SIGNiX configuration missing submitter email") on failure.

2. **Data dict builder (CustInfo, Data, signers)**
   - Add a function or private helpers that, given deal, document_set, and config, build `cust_info`, `transaction_data` (including transaction_id and doc_set_description), and `signers` list. Use get_signer_order_for_deal, resolve_signer_slot, get_signer_authentication_for_slot. Do not build Form yet. Submitter phone default `"800-555-1234"` when config.submitter_phone is blank.

3. **TransactionID helper**
   - Generate TransactionID as a **UUID** (e.g. `str(uuid.uuid4())`) so it is exactly **36 characters** in standard UUID format. No slug or timestamp; UUID guarantees uniqueness and satisfies the 36-character max length.

4. **Verification (Batch 1)**
   - Unit test: with a fixture deal and document_set that satisfy preconditions, call validate_submit_preconditions; no raise. With document_set belonging to another deal, assert raise with "document set does not belong to deal". With a slot unresolved, assert raise. With no submitter email in config, assert raise.

### Batch 2 — Form XML and template (steps 5–8)

5. **Form XML builder**
   - For each document instance: get source template (Static or Dynamic), get latest version and file, base64-encode content. Build Form XML fragment from the template's `tagging_data`: we have all required data (tag_name, field_type, member_info_number; for Static, PDF field identifiers; for Dynamic, anchor_text or bounding_box). Map these to the Flex API Form elements (AcroForm vs text-tagging) per the [Flex API — SubmitDocument](https://www.signix.com/apidocumentation#SubmitDocument) request XML. Append each `<Form>...</Form>` to `data.form`.

6. **Django template**
   - Create `submit_document_request.xml` (or similar) under app/project templates. CustInfo, Data, MemberInfo loop, then `{{ data.form | safe }}`. Ensure XML declaration and xmlns match Flex API.

7. **build_submit_document_body**
   - Implement full flow: validate, load config, build full data dict (including Form), render template, return (body, metadata) with metadata["transaction_id"].

8. **Verification (Batch 2)**
   - For a fixture deal/document_set/config with two signers and one document, call build_submit_document_body. Assert response is a tuple (str, dict); assert "SubmitDocumentRq" in body, "CustInfo" in body, "MemberInfo" count == 2, "TransactionID" in body, "Form" in body. Assert metadata["transaction_id"] matches the value in the XML.

### Batch 3 — Tests and optional dump (steps 9–11)

9. **Unit tests**
   - Tests: (1) Valid inputs produce XML with expected CustInfo, Data (TransactionID, DocSetDescription, SubmitterEmail, SubmitterName), correct number of MemberInfo, at least one Form. (2) Validation: document_set None, wrong deal, missing instance, missing file, unresolved signer, missing submitter email — each raises SignixValidationError with non-empty errors. (3) Signer order: with deal.signer_order = [2, 1], MemberInfo order in XML matches (second slot first). (4) Auth: get_signer_authentication_for_slot value appears in Service element.

10. **Optional: management command or debug view**
    - Management command: e.g. `python manage.py signix_dump_body <deal_id>` that loads deal and its first document_set (or document_set_id arg), calls build_submit_document_body, and prints XML to stdout or writes to a file. Or a staff-only debug view that returns XML with Content-Type application/xml. Mark optional in plan; implement if time permits.

11. **Verification (Batch 3)**
    - Run full test suite for signix/build_body. All tests pass. If dump command added, run with a valid deal_id and confirm XML is well-formed.

---

## 7a. Implementation Batches and Verification

**Batch 1 — Validation and data dict (no Form)**

**Includes:** SignixValidationError, validate_submit_preconditions, data dict builder for CustInfo/Data/signers, TransactionID helper (UUID, 36 chars).

**How to test after Batch 1:**

1. validate_submit_preconditions: pass with valid deal+document_set; raise with wrong deal, no instances, no file, unresolved signer, no submitter email.
2. Data dict: with valid fixture, assert cust_info and transaction_data and signers list are populated; signers have first_name, email, service, ssn, dob.

**Implementation notes (Batch 1):** SignixValidationError is a custom exception with `errors: list[str]` (and str(err) joins them). validate_submit_preconditions raises immediately when document_set is None; otherwise collects all failures (wrong deal, no template, unresolved slots, no instances / no version / no file per instance, missing submitter email) and raises once. TransactionID is generated with `str(uuid.uuid4())` (36 chars). build_submit_data_dict(deal, document_set, config) returns dict with cust_info, transaction_data, signers, and transaction_id; call validate_submit_preconditions first. Submitter phone defaults to "800-555-1234" when config.submitter_phone is blank. Unit tests live in `apps.deals.tests.test_signix_build_body`.

**Batch 2 — Form XML and build_submit_document_body**

**Includes:** Form XML builder from tagging_data and latest version file, Django template (DTL), build_submit_document_body returning (body, metadata).

**How to test after Batch 2:**

1. build_submit_document_body(deal, document_set) returns (str, dict); XML contains SubmitDocumentRq, CustInfo, Data, MemberInfo (count = signer count), Form(s). metadata["transaction_id"] present.
2. Form section contains base64-looking content and tag/field structure (exact format depends on Flex API).

**Implementation notes (Batch 2):** Branch on template type: Static (AcroForm) vs Dynamic (text-tagging) per Section 3.4; Static uses SignatureLine with SignField and optional DateSignedField/DateSignedFormat, and template's signature_field_names when tag_name missing. Signers in data dict include phone, sms_count, dob "01/01/1990"; MemberInfo in template order: RefID, SSN, DOB, FirstName, MiddleName, LastName, Email, Service, MobileNumber, SMSCount. Form XML is built per document instance: get source template (instance.source_document_template), ref_id for FileName, latest version file read and base64-encoded. Each Form includes at least one SignatureLine (MemberInfoNumber from tagging_data or default 1) so the API’s “at least one SignatureLine or View” is satisfied; tag definitions from tagging_data map to SignatureLine/View elements per Flex API. The full data dict is built by calling build_submit_data_dict then adding a top-level "submitter" dict (email, name, phone) and "form" (concatenated Form XML string). Render with Django’s `django.template.loader.get_template(...).render(context)`; template uses DTL (`{% for signer in data.signers %}`) and `{{ data.form | safe }}`. Template path: `signix/submit_document_request.xml` (resolved from app templates). Form fragment order: RefID, Desc, FileName, MimeType, SignatureLine(s) or TextTagField/TextTagSignature, Length, Data. Branch Static vs Dynamic per Section 3.4. ContactInfo and DeliveryType (SDDDC) in template.

**Batch 3 — Tests and optional dump**

**Includes:** Unit tests for validation, body structure, signer order, auth; optional management command or debug view.

**How to test after Batch 3:**

1. pytest (or Django test) for apps.deals.tests.test_signix_build_body (or test_build_body). All pass.
2. Optional: run dump command and open XML in browser or validator.

**Implementation notes (Batch 3):** Batch 3 adds unit tests for signer order (deal.signer_order = [2, 1] → MemberInfo order in XML reflects second slot first) and auth (Service element contains SelectOneClick or SMSOneClick). Optional management command `signix_dump_body` takes one positional argument (deal_id), loads the deal’s first document_set, calls build_submit_document_body, and writes XML to stdout (or to a file with --output). Command lives in `apps/deals/management/commands/signix_dump_body.py`.

**Completed (Batch 3):** Unit tests added in `test_signix_build_body.py`: `test_signer_order_reflected_in_member_info_order`, `test_service_element_contains_auth_value`, `test_xml_contains_doc_set_description_and_submitter`. Management command `signix_dump_body` implemented: `python manage.py signix_dump_body <deal_id>` prints XML; `--output` / `-o <path>` writes to file. Command validates preconditions and exits with clear errors if deal not found or deal has no document set. All 41 signix/build_body tests pass.

**Manual testing (after Batch 3):**
- **Django shell:** Load a deal that has a document set with instances and latest-version files; call `build_submit_document_body(deal, document_set)` and inspect the returned XML string and metadata (e.g. `transaction_id`). Optionally set `deal.signer_order = [2, 1]` and confirm MemberInfo order and Service values.
- **Dump command:** With a valid deal ID that has a document set: `python manage.py signix_dump_body <deal_id>` (XML to stdout). To save to file: `python manage.py signix_dump_body <deal_id> --output submit.xml`. Confirm XML is well-formed (e.g. open in browser or validator). Run with invalid deal_id or deal with no document set to confirm error messages.

---

## 8. File Summary

| Item | Value |
|------|--------|
| Module | `apps.deals.signix` |
| Exception | `SignixValidationError(errors: list[str])` |
| Functions | `validate_submit_preconditions(deal, document_set)`, `build_submit_document_body(deal, document_set) -> tuple[str, dict]` |
| Template | `apps/deals/templates/signix/submit_document_request.xml` (or project templates) |
| Tests | `apps/deals/tests/test_signix_build_body.py` or `test_build_body.py` |
| Optional | Management command `signix_dump_body` or debug view |

---

## 9. Open Issues / Implementation Decisions

- **Form XML structure:** We have all required data from static and dynamic `tagging_data` to build Form fields (tag_name, field_type, member_info_number; PDF field refs for static, anchor_text/bounding_box for dynamic). **No open issue:** the implementation task is to map that data to the Flex API's published Form XML schema (element names and order from [Flex API — SubmitDocument](https://www.signix.com/apidocumentation#SubmitDocument)). Document the mapping in the Form builder (e.g. which tagging_data keys map to which API elements for Static vs Dynamic).

- **FileName (Data or per-Form):** **Decided:** Take the filename from the document (template) name: **template `ref_id` + `.pdf`** (e.g. `ZoomJetPackLease.pdf`). Use this for each Form's filename when the API expects a name per document; if the API also or only expects a single FileName at Data level, use the first document's filename or omit per Flex API documentation.

- **RefID in MemberInfo:** Design says "Position or role label (e.g. 'Signer 1', 'Signer 2' or stored role label); implementation choice." **Decision:** Use `"Signer 1"`, `"Signer 2"`, etc. (position in the signer order). Optionally switch to role labels from get_role_label_for_slot if SIGNiX displays RefID to users and role is preferred.

- **Return value of build_submit_document_body:** **Decided:** Return `(xml_string, metadata)` with `metadata` dict containing at least `transaction_id` so Plan 6 can persist it without parsing XML.

- **Validation API:** **Decided:** Raise `SignixValidationError` with `errors: list[str]` on failure; no return value on success. Orchestrator catches and returns user-facing message.

- **ContactInfo, DeliveryType:** **Decided:** Output ContactInfo (empty or from config) and **DeliveryType** with value **SDDDC** in the template when the Flex API requires them. See Section 3.2.

- **Slug length / TransactionID max length:** **Decided:** TransactionID **max length 36 characters**, **standard UUID format** (e.g. `str(uuid.uuid4())`). Use a new UUID per transaction; no slug or timestamp format. Satisfies Flex API length constraint and guarantees uniqueness.

- **Optional dump:** Management command vs debug view is optional. **Decision:** Plan includes optional management command `signix_dump_body`; implement if time permits. Debug view can be a follow-up.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-SEND-AND-PERSIST.md (Plan 6).*

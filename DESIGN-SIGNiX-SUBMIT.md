# Design: SIGNiX — Submit

This document captures the design for **submitting** a deal’s document set to SIGNiX (SubmitDocument flow). Users submit a deal’s current document set for signature from the Deal detail page. **Who signs, the order they sign, and what documents each signer sees and signs** are determined by the app’s **signer identification and signing sequence** functionality (Section 5.3): signer slots are derived from the document set template; the Signers table on Deal View shows them resolved to people and allows reordering; that order becomes the SIGNiX **Members** (MemberInfo) in the SubmitDocument call. The first signer in that order can sign via a **separate window** (GetAccessLink); other signers receive SIGNiX email and complete signing in the workflow defined by the templates. The design also defines a signature-transaction dashboard and the link between SIGNiX transactions and Deals. Push notifications, DownloadDocument, and ConfirmDownload are **deferred** (Section 8).

**Design references:** **KNOWLEDGE-SIGNiX.md** (Flex API, SubmitDocument, GetAccessLink, push notifications, XML/template approach; SIGNiX “Members” = MemberInfo in the request). **DESIGN-DOCS.md** (document sets; status flow Draft → Submitted to SIGNiX → Final; DESIGN-DOCS uses member_info_number 1 = lease officer, 2 = first contact as an example). **PLAN-ADD-DOCUMENT-SETS** (deal detail Documents section, Send for Signature stub, `document_set`, `DocumentInstance`, `DocumentInstanceVersion`). **apps.doctemplates** (Static and Dynamic templates expose signer slots via `tagging_data` — form field config and text-tagging config both use `member_info_number`).

---

## 1. Scope and Goals

### In scope

- **Submit from Deal detail** — From the Deal detail (View) page, the user can submit the **current Document Set** for signature. The set can contain any number of documents (e.g. two: lease agreement, safety advisory); all are sent in one SIGNiX transaction.
- **Who signs** — The signers (SIGNiX **Members**) are determined by the **signer identification** functionality: signer slots (1, 2, …) are derived from the document set template (Section 5.3); each slot is resolved to a person from the deal. The app does not hard-code “lease officer” and “one contact”; it takes its instructions from the template-derived signer list and the deal’s resolution of those slots to people (e.g. in the current convention, slot 1 = lease officer, slot 2 = first contact — see Section 5).
- **Signing order** — The **order** in which signers sign is taken from the **Signers table** on Deal View: the user can reorder the list; that order is persisted and used when building the SubmitDocument request. The first entry in the list is the first MemberInfo (first in SIGNiX workflow), the second is the second MemberInfo, and so on.
- **What each signer sees and signs** — Which documents and fields each Member sees and signs is determined by the **document templates**: each Static and Dynamic template’s `tagging_data` assigns fields to signer slots via `member_info_number`. The transaction packager builds Form XML from that; no document is “hard-coded” to one signer — it follows the template configuration.
- **First signer experience** — The **first signer in the signing order** signs by opening the SIGNiX UI in a **separate window** (GetAccessLink), so the user stays in the Lease application.
- **Other signers** — Other signers receive an **email from SIGNiX** inviting them to sign. They click the link and complete the SIGNiX signing process (documents and fields assigned to them in the templates). When the last signer is done, the transaction is complete.
- **Signature transaction tracking** — A **table/dashboard** lists signature transactions submitted to SIGNiX and their status. This is accessible as a **main menu item** (e.g. “Signature transactions” or “Signatures”).
- **Deal ↔ transaction relationship** — A relationship is maintained between SIGNiX transactions and the Deal from which they were generated. On the **Deal View page**, a table **under the Documents section** shows related signature transactions and their status.
- **Signers table on Deal View** — The signers required for the deal’s document set are derived from the **document templates** (Static: form field configuration; Dynamic: text-tagging configuration), where each field specifies a signer via `member_info_number`. A **Signers** table on Deal View lists these signers (resolved to actual people from the deal) in an **ordered list**, with the ability to **change the order** (signing sequence). The same table is used to specify **authentication** per signer: **SelectOneClick** by default for signers that resolve to a **user** (e.g. lease officer), **SMSOneClick** by default for signers that resolve to a **contact**; the user can change the authentication type per signer (e.g. choose between SelectOneClick and SMSOneClick). A **service** that, given a document set template, returns the list of signer slots supports this and the transaction packager.
- **Core implementation first** — Submit transaction (build payload, call SubmitDocument, store DocumentSetID and first-signing link, create local record) is implemented first. **Status updates** depend on **push notifications**; handling push notifications is expected to follow after core submit is in place.

### Out of scope (or later)

- **Push notifications** — Required for reliable status updates (Send, partyComplete, complete, etc.). A solution is needed so the app can receive webhooks when running on a development machine (e.g. **ngrok**). This may be addressed in this design or in a **separate design**; see Section 8.
- **DownloadDocument / ConfirmDownload** — When the transaction is complete, the app should download signed PDFs and call ConfirmDownload (per KNOWLEDGE-SIGNiX). That flow depends on push (or polling) and is part of a later phase.
- **Multiple document sets or re-send** — Each “Send for Signature” action creates one new transaction from the current document set. The **initial version does not limit** how many transactions can be created from the same document set (allowing multiple submissions for thorough testing). We may revisit later to prevent accidentally sending multiple transactions (e.g. disable or warn when one is already in progress). Re-sending after regenerating documents (and cancelling the previous transaction) is a possible future extension.
- **Delete Transaction History** — The “Delete Transaction History” button (dashboard and Deal View) is included for **testing**; it may be removed or hidden in a later stage, as it is typically not needed in production.

---

## 2. References

| Document | Use |
|----------|-----|
| **KNOWLEDGE-SIGNiX.md** | Flex API overview, credentials, endpoints (Webtest/Production), SubmitDocument structure (CustInfo, Data, MemberInfo, Form), GetAccessLink, push notifications, XML request (template + Base64 in Form), response parsing (ElementTree). |
| **DESIGN-DOCS.md** | Document sets, Document Set Template, signer mapping (`member_info_number` 1 = user/lease officer, 2 = first contact as an **example**); status flow (Draft → Submitted to SIGNiX → Final), Deal detail Documents section. |
| **PLAN-ADD-DOCUMENT-SETS** | Deal detail URL `/deals/<pk>/`, Documents section, Send for Signature stub at `POST /deals/<pk>/documents/send-for-signature/`, `document_set`, `DocumentInstance` (order), `DocumentInstanceVersion` (status, file). |
| **DESIGN-DATA-INTERFACE.md** | `get_deal_data(deal)` for deal/contact/lease officer data; first contact = first in `deal.contacts` list for slot→person resolution. |
| **Flex API documentation** | [https://www.signix.com/apidocumentation](https://www.signix.com/apidocumentation) — SubmitDocument request/response XML, GetAccessLink, Form/MemberInfo structure. |

---

## 3. User Flows

### 3.1 Submit for signature

1. User opens **Deal detail** (View) for a deal that has a **Document Set** with at least one document instance and latest versions with PDFs.
2. They click **Send for Signature** (replacing the current stub).
3. System validates: document set exists, has the required document instances, latest version of each has a PDF; every signer slot from the document set template is resolved to a person on the deal (e.g. slot 1 → lease officer, slot 2 → first contact); **SIGNiX configuration present** (credentials and submitter email configured).
4. System builds the SIGNiX transaction from **signer identification and templates**: signer order from the Signers table (Section 4.3, 5.3); who each Member is from slot→person resolution; CustInfo, Data (TransactionID, submitter info, etc.); one **MemberInfo** per signer in that order; one **Form** per document with tag definitions and signer–field assignments from each template’s `tagging_data` (which documents/fields each Member sees and signs).
5. System calls **SubmitDocument**. On success: SIGNiX returns **DocumentSetID** and (in response or via **GetAccessLink**) a link to the **first signer’s** signing experience.
6. System creates a **Signature Transaction** record (Section 4) linked to the Deal and Document Set, stores DocumentSetID and the first-signing URL, sets status to “Submitted” (or equivalent).
7. System marks the relevant Document Instance Versions as **“Submitted to SIGNiX”** (per DESIGN-DOCS status flow).
8. **Open signing in new window** — Open the first signer’s signing URL in a **separate window** (e.g. `window.open` or link with `target="_blank"`) so the user remains on the Deal detail page in the Lease application.

### 3.2 First signer signs

1. After submit, the **first signer in the signing order** opens the SIGNiX UI in a **separate window** (new browser tab or window), so they remain in the Lease application. The signing experience (SIGNiX-hosted) loads in that window for the documents and fields assigned to them by the templates.
2. They complete their assigned documents/fields in the SIGNiX window. SIGNiX advances the workflow to the next signer (if any).
3. **Note (KNOWLEDGE-SIGNiX):** Opening in a separate window avoids iframe limitations (e.g. iOS third-party cookies) and keeps the Lease application in the original tab. No redirect away from the app.

### 3.3 Other signers sign (email)

1. SIGNiX sends an **email** to each subsequent signer (using the email resolved for that slot from the deal) with an invitation to the signing process.
2. The signer clicks the link and is taken to SIGNiX. They see and sign only the documents and fields assigned to their Member (per template `tagging_data`).
3. When the last signer is done, the transaction is **complete**. Status updates (e.g. partyComplete, complete) will be received via **push notifications** once that is implemented.

### 3.4 Dashboard and Deal View

- **Signature transactions dashboard** — Main menu item (e.g. “Signature transactions”). Page shows a table: Deal (link), description/label, SIGNiX DocumentSetID, status, created date, optional link to open signing (if still pending for current user). Enables tracking all submitted transactions.
- **Deal View — Related signature transactions** — Under the Documents section, a second table lists **signature transactions for this deal**: same columns (or subset). Links to the deal and to the dashboard detail if needed.

---

## 4. Data Model

### 4.1 Signature transaction record

We need a local model to represent a SIGNiX transaction tied to a Deal and the document set that was submitted.

**Proposed model: `SignatureTransaction`**

| Field | Type | Purpose |
|-------|------|---------|
| `deal` | ForeignKey(Deal) | Deal from which this transaction was generated. |
| `document_set` | ForeignKey(DocumentSet) | Document set that was submitted (snapshot: the set at submit time). |
| `signix_document_set_id` | CharField | SIGNiX’s DocumentSetID returned from SubmitDocument. |
| `transaction_id` | CharField, optional | Client-chosen TransactionID sent in the request; **max length 36 characters**, **standard UUID format** (e.g. UUID4). See Section 6.1.1. |
| `status` | CharField | One of: **Submitted**, **In Progress**, **Suspended**, **Complete**, **Cancelled**. Until push is implemented, status may remain “Submitted” or be updated manually/polling. |
| `first_signing_url` | URLField, optional | GetAccessLink URL for the **first signer in the signing order**; opened in a separate window so the user stays in the Lease application. |
| `submitted_at` | DateTimeField | When SubmitDocument was called. |
| `completed_at` | DateTimeField, null=True | When transaction was completed (from push or polling; optional until we have push). |

- **App:** Either a new app `apps.signix` (or `apps.signatures`) or a model under `apps.deals`. Keeping it under `apps.deals` avoids a new app for one model; a separate app is better if we expect more SIGNiX-specific logic (credentials, API client, push handler). **Decision:** Prefer **`apps.deals`** for the model and deal-scoped views; SIGNiX API client and payload building can live in a small module (e.g. `apps.deals.signix` or `apps.documents.signix`) to keep views thin. Alternatively **`apps.signix`** if we want a clear boundary for all SIGNiX-related code.
- **Relations:** `Deal` has `related_name='signature_transactions'` (or similar). Deal detail view prefetches or filters `SignatureTransaction.objects.filter(deal=deal)` for the “Related signature transactions” table. **Referential integrity:** Use CASCADE for both `deal` and `document_set` so that deleting a Deal or Document Set removes its signature transactions; every SignatureTransaction always has a valid deal and document_set.

### 4.2 Document Instance Version status

Per DESIGN-DOCS and PLAN-ADD-DOCUMENT-SETS, when documents are sent to SIGNiX, the **latest** Document Instance Version for each instance in the set is updated to status **“Submitted to SIGNiX”**. When the transaction is complete and we download signed PDFs, new Document Instance Versions are created with status **“Final”**. No schema change required; use existing `DocumentInstanceVersion.status`.

### 4.3 Signer order and authentication (for Deal View and transaction packager)

To support **reorderable signers** and **per-signer authentication** on Deal View (Section 5.3), both are persisted on the **Deal**.

**Signer order**

- **Storage:** **Deal** — `signer_order` JSONField (list of slot numbers in display/signing order, e.g. `[1, 2]` or `[2, 1]`), **null=True, blank=True**. When null/empty, **effective order** = `get_signers_for_document_set_template(document_set_template)` (numeric order). The transaction packager uses effective order when building MemberInfo (first in list = first MemberInfo, etc.). Helpers: **`get_signer_order_for_deal(deal, document_set_template)`** returns the effective order.
- **Alternative (not used in initial implementation):** DocumentSet could hold order per set; decided to use Deal for simplicity (see Section 9).

**Signer authentication**

- **Storage:** **Deal** — `signer_authentication` JSONField (dict mapping slot number as **string** to auth type: `{"1": "SelectOneClick", "2": "SMSOneClick"}`), **null=True, blank=True**. When a slot is missing from the dict, **default** by convention: slot 1 → SelectOneClick, slot 2 → SMSOneClick, slot 3+ → SelectOneClick. Helper: **`get_signer_authentication_for_slot(deal, slot_number)`** returns the auth type for the slot (stored or default).
- **User choice** — The Signers table includes an **Authentication** column (dropdown: SelectOneClick, SMSOneClick). User changes are saved via a single “Save signer settings” form that POSTs auth for all slots. When building SubmitDocument, the packager uses the stored value when present, otherwise the slot-based default.
- **SMSOneClick** — If SMSOneClick is selected, the signer must have a phone number (contacts have `phone_number`; users may have it in LeaseOfficerProfile). Other auth types (e.g. KBA) may be added in a later release.

### 4.4 SIGNiX configuration (administrative)

- **Purpose** — Store SIGNiX credentials and settings entered via the administrative UI (Section 7.6) so the transaction packager can read them when building and sending SubmitDocument (and other Flex API calls).
- **Shape** — A **single record** (singleton): e.g. a model `SignixConfig` with one row, or a key-value store. The singleton is typically implemented with a fixed primary key (e.g. `pk=1`) and created on first access via a helper (e.g. `get_or_create(pk=1, defaults={...})`) so no row exists until the config page is opened or submit runs. Fields: **sponsor**, **client**, **user_id**, **password** (store with appropriate protection per security policy; see below), **workgroup**; **demo_only** (boolean, default True); **delete_documents_after_days** (positive integer, default 60); **default_email_content** (text, default `"Your documents for the Sample Application are available online for viewing and signing."`); **submitter_first_name**, **submitter_middle_name**, **submitter_last_name**, **submitter_email**, **submitter_phone** (used when building SubmitDocument; see Section 6.1.1, 7.6). Endpoint URL is derived from `demo_only` (Webtest vs Production) and need not be stored unless an override is desired.
- **Model vs form** — The model may allow blank on credentials and submitter fields so the single row can be created with defaults (e.g. demo_only=True, delete_documents_after_days=60) without requiring credentials at creation time. **Form validation** should require all five credentials and submitter email when saving, so that once saved, the config is valid for submit. Password: require in the form when the instance has no password set (initial save); when editing, a blank password field means “keep existing” and must not overwrite the stored password.
- **Password storage** — Use a password-style input in the UI so the value is not visible in the browser. For the **initial release**, the password may be stored in the database (e.g. plain text) with the above UI protection. **Before deploying to a Production environment**, the password storage approach must be addressed in a later release (e.g. encryption at rest, secrets manager, or environment-based secrets) per security policy.
- **App** — Same app as the transaction packager (e.g. `apps.deals`) or a small `apps.signix` if used. The packager imports or calls a helper that returns the current config: **`get_signix_config()`**, implemented in e.g. `apps.deals.signix`. This helper returns the single SignixConfig instance and creates it with default values if no row exists (so submit and the config page can always obtain a record; validation then enforces required credentials and submitter email before allowing submit).

---

## 5. Signer and Document Mapping

**Source of truth:** The app takes its instructions on **who signs**, **the order they sign**, and **what documents/fields each signer sees and signs** from:

1. **Signer slots** — Derived from the document set template via `get_signers_for_document_set_template` (Section 5.3): which Member slots (1, 2, …) are needed.
2. **Signing order** — The ordered list from the Signers table (and stored signer order, Section 4.3): first in list = first MemberInfo in SubmitDocument = first in SIGNiX workflow.
3. **Slot → person resolution** — Each slot is resolved to a real person (name, email, etc.) from the deal. The current convention (example) is slot 1 = lease officer, slot 2 = first contact (DESIGN-DOCS); the app uses this (or a configurable mapping) to populate MemberInfo.
4. **Authentication per signer** — Each Member’s authentication method (SIGNiX `<Service>`, e.g. SelectOneClick, SMSOneClick) is taken from the **Signers table**: stored per slot (Section 4.3), with defaults by signer type (user → SelectOneClick, contact → SMSOneClick). The user can change it per signer in the table.
5. **What each Member sees and signs** — Determined entirely by the **document templates**: each Static and Dynamic template’s `tagging_data` assigns fields to `member_info_number`. The transaction packager builds Form XML so that each Form includes only the SignatureLine/View elements for the Members that template assigns to that document. No hard-coded “document 1 = officer, document 2 = contact”; it follows the template configuration.

These map directly to SIGNiX’s **Members** (MemberInfo in the SubmitDocument request) and to the Form structure (which Member signs/views which document).

### 5.1 Signers (MemberInfo) — example mapping

The following is the **current convention** (e.g. DESIGN-DOCS and “Lease - Single Signer” deal type). The app may use this or a configurable mapping; the rule is that each signer slot must resolve to a person from the deal.

| Signer slot | Example role | Example source in app | Example default auth |
|-------------|--------------|------------------------|----------------------|
| 1 | Lease officer | `deal.lease_officer` (User); name/email from user or LeaseOfficerProfile. | SelectOneClick |
| 2 | Lessee / first contact | First contact: `deal.contacts` ordered by id; first contact’s name, email, phone. | SMSOneClick |

Other deal types or configurations may map slots differently (e.g. slot 1 = contact, slot 2 = lease officer); the signer identification and Signers table drive the actual list, order, and authentication.

### 5.2 Documents (Forms) — driven by template tagging

- **Which documents each Member sees and signs** is determined by the **template** for that document: the template’s `tagging_data` lists fields (signature, date, etc.) each with a `member_info_number`. The transaction packager builds one Form per document; for each Form, it includes SignatureLine/View elements only for the Members that appear in that template’s tagging_data. So if a document’s template has no fields with `member_info_number` = 1, that document is not shown to Member 1; if it has fields for both 1 and 2, both signers see and sign that document (workflow order is still determined by the Signers table order).
- **Example:** Document 1 (e.g. lease agreement) might have tagging_data with fields for both slot 1 and slot 2; Document 2 (e.g. safety advisory) might have tagging_data only for slot 2. Then Member 1 sees only Document 1, and Member 2 sees Document 1 and Document 2. This is an example, not a fixed rule — the templates define it.

Tag definitions (signature/date fields) come from the document templates (Static: AcroForm fields; Dynamic: text tagging). The **transaction packager** (Section 6) builds Form XML from each document instance’s source template and its tagging_data; it does not hard-code which document is for which signer.

### 5.3 Signers derived from document set template (Deal View and service)

Signer slots (1, 2, …) are defined in the **document templates** that make up the document set:

- **Static templates** — Form field configuration (`tagging_data`) includes `member_info_number` per field (see apps.doctemplates).
- **Dynamic templates** — Text-tagging configuration (`tagging_data`) includes `member_info_number` per signature/date field.

The **document set template** (DocumentSetTemplate) for the deal’s deal type defines which templates are in the set and in what order. From it we can derive **which signer slots are required** by scanning every Static and Dynamic template in the set and collecting the distinct `member_info_number` values from their `tagging_data`.

**Service: `get_signers_for_document_set_template(document_set_template)`**

- **Input:** A `DocumentSetTemplate` instance (e.g. the one for the deal’s deal type). If `None` is passed, the function returns `[]` so callers need not check.
- **Behavior:** For each item in `document_set_template.items.all()` (in order), resolve the template (Static or Dynamic via GenericForeignKey), read `tagging_data`, and collect all **integer** `member_info_number` values (1, 2, …). Return an **ordered list of unique signer slot numbers** (e.g. `[1, 2]`) in **numeric ascending** order so the list is stable and matches SIGNiX MemberInfo ordering. If an item’s template is missing or the wrong type, skip that item (collect no member_info_number from it).
- **Output:** e.g. `[1, 2]`. Used by: (1) Deal View to know how many signers to show and which slots to resolve to people; (2) transaction packager to build the correct number of MemberInfos and to respect signer order (see below).
- **Location:** Implemented in **`apps.deals.signix`** (same module as the transaction packager and signer resolution).

**Resolving slots to people on the Deal**

Each signer slot (1, 2, …) must be resolved to a person (name, email, phone as needed) from the deal. The app uses a **slot→person mapping** implemented as **`resolve_signer_slot(deal, slot_number)`**, which returns a single record (first_name, middle_name, last_name, email, phone) or **`None`** when the slot cannot be resolved (e.g. slot 2 but no contact on the deal). **Current convention:** slot 1 = lease officer (`deal.lease_officer`; name/email from **LeaseOfficerProfile** when present, otherwise from User: split `get_full_name()` — first word = first_name, remainder = last_name — or use username if `get_full_name()` is empty); slot 2 = first contact (`deal.contacts` ordered by id; first contact). **Slot 3 and beyond** return `None` in the current convention (extend later if needed). The Signers table and the transaction packager both use this resolution so that the list on Deal View matches the Members sent in SubmitDocument.

**Signers table on Deal View**

- **Placement** — On the Deal detail (View) page, a **Signers** card sits **above** the Documents section (between deal summary and Documents). Implemented in the same template as deal detail.
- **Content** — One row per signer slot, in **effective order** (from `get_signer_order_for_deal`). Columns: Order (1, 2, …), Role label (e.g. “Lease officer”, “Lessee”), Name, Email, optionally Phone, **Authentication** (dropdown: SelectOneClick, SMSOneClick). Data from `get_signers_for_document_set_template(deal’s document set template)`, **slot→person resolution** (`resolve_signer_slot`), and **`get_signer_authentication_for_slot`**. If a slot does not resolve to a person (e.g. no contact for slot 2), show a **placeholder** (e.g. “— No contact —”) but keep the row so the user sees the gap and can still save order/auth. **Saving:** One form with all auth dropdowns and a “Save signer settings” button (POST to update-auth endpoint); reorder via “Move up” / “Move down” buttons that POST immediately to reorder endpoint. If there is no document set template for the deal type, hide the section or show an empty state.
- **When document set exists** — If the deal has a document set, the template used is `document_set.document_set_template`. If the deal has no document set yet, use the template for `deal.deal_type` (same lookup as “Generate Documents”) so the signers table is still meaningful before generation.
- **Reorder** — The user changes order via up/down controls; the new order is saved to `deal.signer_order` and defines the **signing sequence** for SIGNiX (first entry = first MemberInfo in SubmitDocument). Reordering does not change template field assignments (member_info_number); the packager maps “position 1 in list” to the person for the slot at position 1. See “Signer order override” below.

**Signer order override**

- **Requirement** — Store the user’s chosen order on **Deal** (`signer_order` JSONField). When null/empty, effective order = `get_signers_for_document_set_template(template)`. The packager and Signers table use **`get_signer_order_for_deal(deal, document_set_template)`** for the effective order.
- **Implementation** — See Section 4.3 and PLAN-SIGNiX-SIGNERS-TABLE (Plan 4).

**Signer authentication (stored with order)**

- Stored on **Deal** (`signer_authentication` JSONField). The Signers table displays the current value (from **`get_signer_authentication_for_slot(deal, slot_number)`** or default) and allows the user to change it via a single form; changes are saved with “Save signer settings” (POST to update-auth endpoint). When building SubmitDocument, the packager uses the stored value when present, otherwise the slot-based default (slot 1 → SelectOneClick, slot 2 → SMSOneClick).

---

## 6. Transaction Packager (Submit Flow)

### 6.1 Responsibilities

- **Inputs:** Deal, Document Set (with instances and latest version PDFs per instance).
- **Validation:** Document set belongs to deal; required document instances present; each instance has a latest version with a file; **every signer slot** from the document set template is resolved to a person on the deal (validation fails if e.g. slot 2 is required but the deal has no contact); **SIGNiX configuration is present** (all required credentials and **submitter email** entered via the administrative UI). Validation runs **before** building the body; the same validation is used by the body builder and the orchestrator so that on failure no HTTP request is made and the caller receives a clear list of errors (e.g. via an exception such as `SignixValidationError` with an `errors` list).
- **Build SubmitDocument request:** CustInfo (from **stored SIGNiX configuration**: Sponsor, Client, User id, Password, Workgroup, Demo, DelDocsAfter, EmailContent), Data (TransactionID, **submitter info from SignixConfig** (Section 4.4, 7.6), DocSetDescription, etc.); **one MemberInfo per signer** in the **signer order** (Section 4.3, 5.3), each resolved to a person from the deal using the slot→person mapping (e.g. slot 1 = lease officer, slot 2 = first contact) and with **authentication** (SIGNiX `<Service>`) taken from the Signers table / stored signer authentication (Section 4.3): SelectOneClick or SMSOneClick per signer, defaulting by type (user → SelectOneClick, contact → SMSOneClick) when not set; one Form per document with tag definitions and signer–field assignments from that document’s template `tagging_data`. Use **template-based XML** (Django template / DTL) per KNOWLEDGE-SIGNiX; documents Base64-encoded inside Form.
- **Signer order:** When building MemberInfo elements, use the **signer order** for the deal (or document set): first entry in the ordered list is the first MemberInfo (first signer in SIGNiX workflow), second entry is the second MemberInfo, etc. Resolve each slot to the correct person from the deal (Section 5.1 example: slot 1 → lease officer, slot 2 → first contact).
- **Call Flex API:** POST to configured endpoint (Webtest or Production). Parse response with **ElementTree**; extract DocumentSetID and any first-signer link if present in response.
- **GetAccessLink:** If the SubmitDocument response does not include the first-signing URL, call **GetAccessLink** for the **first signer** (in signing order; Flex API uses **MemberInfoNumber 1** for the first signer). On **GetAccessLink failure** after SubmitDocument success: still create the **SignatureTransaction** with **empty** `first_signing_url`, persist DocumentSetID and transaction_id, and log the failure — so we do not leave a transaction in SIGNiX with no local record; the user sees the transaction and can obtain the signing link by other means or contact support.
- **Persistence:** Create `SignatureTransaction` (deal, document_set, signix_document_set_id, transaction_id [client-chosen ID sent in request], status=Submitted, first_signing_url, submitted_at). Update latest `DocumentInstanceVersion` for each instance to status “Submitted to SIGNiX”.
- **Return:** SignatureTransaction and first_signing_url so the client can open it in a separate window.

#### 6.1.1 SubmitDocument data sourcing

Every element of the SubmitDocument request has a defined source so there are no ambiguities when implementing the packager.

| Payload area | Field / element | Source or rule |
|--------------|-----------------|----------------|
| **CustInfo** | Sponsor, Client, UserId, Pswd, Workgroup, Demo, DelDocsAfter, EmailContent | SignixConfig (admin UI); Section 4.4, 6.2, 7.6. **Workgroup** must match the **exact value** assigned by SIGNiX (case-sensitive; typo causes "workgroup does not exist"). |
| **Data** | TransactionID | Client-chosen; **max length 36 characters**, **standard UUID format** (e.g. `str(uuid.uuid4())`). Unique per transaction; used for idempotency and correlation. Persisted on SignatureTransaction. |
| **Data** | DocSetDescription | Derived from deal and **document set template name**: e.g. `"Deal #&lt;deal_id&gt; - &lt;template_name&gt;"` (use **ASCII hyphen** between parts to avoid encoding issues in signer email subject; avoid Unicode en dash/em dash). Template name from `document_set.document_set_template.name`, or deal type name if template name is blank. Implementation may use a configurable template. |
| **Data** | FileName | Per-document: **template `ref_id` + `.pdf`** (e.g. ZoomJetPackLease.pdf). If Flex expects a single FileName at Data level, use first document's filename or omit per API. |
| **Data** | SubmitterEmail, SubmitterName | **SignixConfig**: `submitter_email`; SubmitterName = submitter first + middle + last name from config (trimmed, space-separated). Section 4.4, 7.6. |
| **Data** | Submitter phone | **SignixConfig**: `submitter_phone`. When required by Flex and config value is blank, default **`"800-555-1234"`**. |
| **Data** | ContactInfo | Omit if not required by Flex for this integration; if required, use submitter email or phone from SignixConfig, or a config field. |
| **Data** | DeliveryType | When required by Flex, use a valid enum value (e.g. **SDDDC**). |
| **Data** | SuspendOnStart | Constant **false** (we send immediately; no suspend). |
| **MemberInfo** | One per signer, in signer order | Order from stored signer order (Section 4.3, 5.3); first in list = first MemberInfo. **Element order** per Flex schema: RefID, SSN, DOB, FirstName, MiddleName, LastName, Email, **Service**, **MobileNumber**, **SMSCount**, then optional (e.g. KBA, Notary). |
| **MemberInfo** | RefID | Position or role label (e.g. `"Signer 1"`, `"Signer 2"` or stored role label); implementation choice. |
| **MemberInfo** | FirstName, MiddleName, LastName | Slot→person resolution (Section 5.1): from Contact (`first_name`, `middle_name`, `last_name`) or User/LeaseOfficerProfile (first_name, last_name; middle blank or from profile if available). |
| **MemberInfo** | Email, Service | Slot→person resolution for email; Service (auth type) from Signers table / stored signer_authentication (Section 4.3). |
| **MemberInfo** | MobileNumber, SMSCount | **MobileNumber** required for SMS/SharedSecret (e.g. SMSOneClick); send signer's phone from slot→person. **SMSCount**: 1 for SMSOneClick, 0 for SelectOneClick; required by schema. |
| **MemberInfo** | SSN, DOB | Default/placeholder when not provided: **SSN** e.g. `"910000000"`; **DOB** format **MM/DD/YYYY** (e.g. `"01/01/1990"`) for SelectOneClick/SMSOneClick. Override if/when KBA or another auth source is used. |
| **MemberInfo** | Phone (for SMSOneClick) | Contact.phone_number; User/LeaseOfficerProfile if needed for user-resolved signers. |
| **Form** | Document count and order | document_set.instances (Section 6.1). |
| **Form** | Structure (Static vs Dynamic) | **Static (AcroForm):** One Form per document; elements per Flex schema: RefID, Desc, FileName, MimeType, SignatureLine(s) with SignField (PDF AcroForm field name) and optional DateSignedField/DateSignedFormat, Length, Data. Use **signature_field_names** on StaticDocumentTemplate when tag_name is missing (e.g. default Lessor/Lessee by member). **Dynamic (text-tagging):** Branch on DynamicDocumentTemplate; emit TextTagField (e.g. DateSigned) and TextTagSignature from tagging_data (anchor_text, bounding_box, date_signed_field_name, date_signed_format); emit **date tags before signature tags** per SIGNiX requirement. |
| **Form** | Document filename/name | Per document: source template **`ref_id` + `.pdf`** (e.g. ZoomJetPackLease.pdf). |
| **Form** | Tag definitions, signer–field assignments | Template tagging_data (Section 5.2, 5.3). |
| **Form** | Document content | Latest DocumentInstanceVersion.file, Base64 (Section 5.2; KNOWLEDGE-SIGNiX). |

### 6.2 Configuration

- **Source of configuration** — SIGNiX credentials and related settings are entered and stored via an **administrative UI** (Section 7.6). The transaction packager (and `build_submit_document_body`) read from this stored configuration via **`get_signix_config()`** (Section 4.4). No reliance on Django settings or environment variables for these values in the initial version (optional env override can be added later if needed).
- **Credentials (used in SIGNiX calls):** Sponsor, Client, User id, Password, Workgroup. All required for SubmitDocument (CustInfo). The config form should require all five when saving so that a saved config is valid for submit.
- **Additional settings:** **Demo only** (default **yes**): when yes, use SIGNiX Webtest endpoint; when no, use Production endpoint. **Delete Documents After** (days) (default **60**): maps to Flex API DelDocsAfter / retention. **Default Email Content** (default **"Your documents for the Sample Application are available online for viewing and signing."**): used when building the request (e.g. EmailContent or equivalent in the payload).
- **Submitter:** Submitter name, email, and phone are stored in **SignixConfig** (Section 4.4, 7.6): Submitter First Name, Submitter Middle Name, Submitter Last Name, Submitter email, Submitter phone. The transaction packager uses these when building the SubmitDocument request (SubmitterName = first + middle + last trimmed; SubmitterEmail; submitter phone). If submitter phone is required by Flex and the config value is blank, use default `"800-555-1234"`. Validation before submit should require at least submitter email (and optionally name) to be present in config.

### 6.3 Error handling

- **Validation errors** — e.g. a signer slot cannot be resolved to a person (e.g. slot 2 required but no contact on deal), missing PDF: return a clear message; do not call SIGNiX.
- **SubmitDocument API errors** — e.g. HTTP 4xx/5xx or error element in response: do not create SignatureTransaction; do not update version status. Raise a **structured exception** (e.g. `SignixApiError`) so the view can show a generic user-facing message (e.g. “SIGNiX request failed; try again or contact support.”) and log details for debugging **without** exposing credentials or full request/response.
- **GetAccessLink failure after SubmitDocument success** — If SubmitDocument succeeds but GetAccessLink fails: **still create** the SignatureTransaction with **empty** `first_signing_url` (Section 6.1); persist DocumentSetID and transaction_id. Log the GetAccessLink failure. Do not leave a transaction in SIGNiX with no local record; the user sees the transaction and may obtain the signing link by other means or contact support.

### 6.4 Separation of body construction and send

**Rationale:** Separate **building the SubmitDocument request body** (XML) from **sending the request to SIGNiX and handling the synchronous response**. This supports:

- **Debugging** — The request body can be inspected, logged, or saved (e.g. to a file or debug UI) **without** making an HTTP call. Useful when verifying payload structure, credentials, or tag definitions.
- **Testability** — Unit tests can assert on the constructed XML without mocking the network. Integration tests can still exercise the full send/parse flow.
- **Single responsibility** — One function produces the payload from deal + document set + signer config; another (or the same module) performs POST and response parsing.

**Service boundary:**

- **Body construction** — Implement in a **service** (e.g. in the same module as the transaction packager, such as `apps.deals.signix` or `apps.documents.signix`). A function such as **`build_submit_document_body(deal, document_set, ...)`** (or equivalent) takes the validated inputs and returns **(xml_string, metadata)** with **metadata** containing at least **transaction_id** (the client-chosen TransactionID) so the orchestrator can persist it on SignatureTransaction without parsing XML. No HTTP is performed here. This function can be called from the full submit flow and, for debugging, from a management command or a debug view that dumps the XML without sending.
- **Send and response** — A separate function (e.g. **`send_submit_document(body, endpoint_url, credentials)`** or **`post_to_signix(body)`**) takes the body (and endpoint/credentials), performs the POST (e.g. `application/x-www-form-urlencoded` per Flex API), and returns the raw response or a parsed result (DocumentSetID, first-signing link, or error). The **same endpoint and transport** are used for **GetAccessLink** when the first-signing URL is not in the SubmitDocument response; see KNOWLEDGE-SIGNiX for transport and parameter details. The **orchestrator** (the “transaction packager” entry point used by the view) then: (1) validates, (2) calls `build_submit_document_body`, (3) optionally logs or stores the body for debugging, (4) calls the send function, (5) parses response, (6) calls GetAccessLink if needed, (7) persists SignatureTransaction and version status, (8) returns. So the **construction of the body lives in a service**; the send/response and persistence can be in the same service layer or split further as long as the body-building step is callable on its own.
- **Debugging features** — A future debug view or management command can call only `build_submit_document_body` and display or save the XML (e.g. “Preview SubmitDocument body” without sending). Implementation details (where to store dumps, log level, etc.) can be decided in the PLAN.

---

## 7. UI

### 7.1 Deal detail — Send for Signature

- **Replace stub** — The existing "Send for Signature" button currently POSTs to `deals:deal_send_for_signature_stub` and shows "SIGNiX integration will be available in a future release." Replace with real action: POST to the same URL (or rename to `deal_send_for_signature`) that calls the transaction packager. On success: create SignatureTransaction, set first_signing_url, and **open the first signer's signing URL in a separate window** (so the user stays on the deal detail page). On failure: show error message, stay on deal detail.
- **Error handling on submit** — **Validation errors** (e.g. SignixValidationError): show the validation errors so the user knows what to fix; **re-render** deal detail with the errors so the user stays on the page. **API errors** (e.g. SignixApiError): show a **generic** user-facing message (e.g. "SIGNiX request failed; try again or contact support.") and redirect to deal detail; do not expose API details or credentials.
- **Empty first_signing_url** — When the transaction is created but the first-signing URL could not be obtained (GetAccessLink failure, Section 6.1): still show **success** and redirect to deal detail; **do not** open a new window. Optionally inform the user that the signing link could not be retrieved and they can check the transaction or contact support.
- **When to show button** — Show when a document set exists with at least one document instance, **SIGNiX configuration is present** (Section 7.6), and validation would pass (e.g. all signer slots resolved to a person, submitter email configured). If no SignixConfig exists, the button should be disabled or show a clear message that SIGNiX configuration is required. Use the **same validation as submit** (`validate_submit_preconditions`) to determine whether the button is enabled and to supply the reason when disabled (e.g. tooltip or inline message). **Initial version:** do not disable or hide the button based on how many SignatureTransactions already exist for this document set — multiple transactions can be created from the same set to support thorough testing. We may revisit later (e.g. disable or warn when a transaction is already "In Progress" or "Complete") to prevent accidental duplicate sends.

### 7.2 First signer signing experience

- **Open in separate window** — After submit success, **open the SIGNiX UI in a separate window** (e.g. new tab or `window.open(first_signing_url)`). The user remains in the Lease application (e.g. on the Deal detail page); the signing experience runs in the other window. No redirect away from the app. This avoids iframe limitations (e.g. iOS) and keeps the workflow clear. **Implementation:** The recommended approach is to pass the signing URL back (e.g. via session) and have the deal detail page open it in a new window when the user lands back on the page after redirect. The alternative is a dedicated “Sign in new window” page that opens the URL via script and then redirects the current tab to deal detail.

### 7.3 Signature transactions dashboard

- **Main menu** — Add a main navigation item (e.g. "Signature transactions" or "Signatures"). **URL:** `/deals/signatures/` under the deals app (decided per Plan 8).
- **List view** — Table columns: Deal (link to deal detail), description (derived from deal id and document set template name; no stored label), SIGNiX DocumentSetID, Status, Submitted at, optional "Open link" when the transaction has a first-signing URL and status is Submitted or In Progress. **Initial implementation:** show "Open link" to all authenticated users when the link is present and status allows; restricting to "current user is first signer" is a possible enhancement (Plan 8).
- **Delete Transaction History** — A **"Delete Transaction History"** button that deletes **all** signature transactions. Use a **separate confirmation URL** (e.g. GET confirmation page, POST to perform delete, then redirect to list). Confirmation step: e.g. "Are you sure? This will remove all transaction records." This is **useful for testing**. The option may be removed or hidden in a later stage (Plan 8).
- **Access:** Authenticated users only.

### 7.4 Deal View — Signers table

- **Placement** — On the Deal detail page, a **Signers** card is shown **above** the Documents section (Section 5.3). It lists the signers required for the deal’s document set, derived from the document set template and resolved to actual people from the deal (slot→person via `resolve_signer_slot`). If a slot does not resolve (e.g. no contact), show a placeholder but keep the row.
- **Columns** — Order (1, 2, …), Role (e.g. “Lease officer”, “Lessee”), Name, Email, optionally Phone, **Authentication** (dropdown: SelectOneClick, SMSOneClick). Data from `get_signer_order_for_deal`, `resolve_signer_slot`, and `get_signer_authentication_for_slot` (Section 4.3). User saves auth via one form (“Save signer settings”); reorder via “Move up” / “Move down” buttons that POST to update-auth and reorder endpoints.
- **When to show** — Show when the deal has a deal type for which a document set template exists (same condition as “Generate Documents”); if the deal has a document set, use its template; otherwise use the template for the deal’s deal type. If no template exists, hide the section or show an empty state.

### 7.5 Deal View — Related signature transactions

- **Placement** — Below the **Documents** section (and below the documents table), add a **separate card** with heading **“Signature transactions”** (or “Related signature transactions”). The subsection is always shown on deal detail; when there are no transactions, show an empty state (e.g. “No signature transactions for this deal.”) and hide the Delete button.
- **Content** — Table of signature transactions for this deal: columns e.g. Submitted at, SIGNiX DocumentSetID, Status, link to “Open signing” when applicable (same rule as dashboard: show to all authenticated users when `first_signing_url` is non-empty and status is Submitted or In Progress). Link to full dashboard: “View all signature transactions”.
- **Delete Transaction History** — A **“Delete Transaction History”** button that deletes **all signature transactions for this deal**. Use a **separate deal-scoped confirmation URL** (e.g. GET confirmation page, POST to perform delete, then redirect to deal detail). Confirmation: e.g. “Are you sure? This will remove all transaction records for this deal.” Shown only when the deal has at least one transaction; hidden when the list is empty. Useful for testing. The option may be removed or hidden in a later stage, as it is typically not needed in production.

### 7.6 Administrative — SIGNiX configuration

- **Purpose** — An administrative UI for entering and editing **SIGNiX credentials and settings** that are used in all SIGNiX API calls (SubmitDocument, GetAccessLink, etc.). Stored configuration is the source of truth for the transaction packager (Section 6.2), loaded via **`get_signix_config()`** (Section 4.4).
- **Placement** — Accessible as a **sidebar or main menu** item (e.g. **“SIGNiX Configuration”** or under a “Settings” / “Admin” area). URL **`/signix/config/`**. Restrict to staff/superuser or a dedicated “configurator” permission; initial implementation may use staff-only.
- **Fields:**
  - **Credentials:** Sponsor, Client, User id, Password, Workgroup (all required for CustInfo). **Form validation:** require all five when saving so that once saved, the config is valid for submit. Use a password-style input for Password (value not visible in browser). **Password handling:** require the password field when creating the record (no existing password); when editing, a blank password field means “keep existing” and must not overwrite the stored value. Storage: per Section 4.4 (initial release may store in database; before Production, address storage).
  - **Submitter (for SubmitDocument):** **Submitter First Name**, **Submitter Middle Name**, **Submitter Last Name**, **Submitter email**, **Submitter phone**. Used when building every SubmitDocument request (Section 6.1.1). **Submitter email is required** in form validation; other submitter fields optional. If submitter phone is blank and Flex requires it, the packager uses default `"800-555-1234"`. SubmitterName in the request is built from first + middle + last (trimmed, space-separated).
  - **Demo only** — Boolean; default **Yes**. When Yes, use SIGNiX **Webtest** endpoint; when No, use **Production** endpoint. Display as checkbox or Yes/No dropdown.
  - **Delete Documents After (days)** — Integer; default **60**. Maps to Flex API retention (e.g. DelDocsAfter). Only relevant when SIGNiX retention is used; see KNOWLEDGE-SIGNiX.
  - **Default Email Content** — Text; default **“Your documents for the Sample Application are available online for viewing and signing.”** Used when building the request (e.g. EmailContent in the payload).
- **Storage** — A single **configuration record** (singleton, e.g. `SignixConfig` with one row created on first access via `get_signix_config()` as in Section 4.4). The app loads this record when building SubmitDocument or sending to SIGNiX. If no record exists, the helper creates one with defaults; “Send for Signature” (and any SIGNiX-dependent action) should be disabled or show a clear message until credentials and submitter email are saved.
- **Access:** Authenticated users with appropriate permission (e.g. staff only or a dedicated “SIGNiX config” permission).

---

## 8. Push Notifications and Status (Deferred)

- **Requirement** — To show accurate status (In Progress, Complete) and to trigger DownloadDocument/ConfirmDownload, the app must receive **push notifications** from SIGNiX (Send, partyComplete, complete, etc.). See KNOWLEDGE-SIGNiX and [Push Notifications](https://www.signix.com/pndocumentation).
- **Development** — When the app runs on a development machine, SIGNiX cannot reach it unless the endpoint is publicly reachable. **ngrok** (or similar) can expose a local URL and forward to the Django server so SIGNiX can POST webhooks. Configuration (URL registration with SIGNiX, secret verification) may be documented here or in a **separate design** (e.g. “Design: SIGNiX push notifications and dev setup”).
- **Decision:** Core design assumes status is stored as “Submitted” until we implement push (or polling). The dashboard and Deal View still show the list of transactions; status column can show “Submitted” or “Pending” until push is in place. **Push notification handling (endpoint, auth, idempotency, updating SignatureTransaction status and DocumentInstanceVersion, and DownloadDocument/ConfirmDownload) can be a follow-on design** so that this document stays focused on submit and UI structure.

---

## 9. Open Issues and Decisions

1. **App location for SignatureTransaction** — **Resolved:** Use **`apps.deals`** for the model and deal-scoped URLs; SIGNiX API client and payload building in `apps.deals.signix` (or `signix` module inside deals). Plans 1–9 implement under apps.deals. A dedicated `apps.signix` remains an option for a later refactor if desired.
2. **TransactionID format** — **Resolved:** Use a **UUID** (e.g. `str(uuid.uuid4())`) so TransactionID is **36 characters**, standard UUID format. Unique per transaction; used for idempotency and correlation. Persisted on SignatureTransaction. No slug or timestamp format.
3. **Authentication method** — Per-signer authentication is configured in the **Signers table** (Section 5.3, 7.4): default **SelectOneClick** for signers that resolve to a user (e.g. lease officer), default **SMSOneClick** for signers that resolve to a contact; the user can select between these two per signer. Other auth types (e.g. KBA) may be added later; Flex API supports them.
4. **Document visibility per Member** — Which documents (and fields) each Member sees and signs is determined entirely by the template `tagging_data` (which Form fields reference which `member_info_number`). No separate rule or hard-coding; the packager builds Form XML from the templates.
5. **ngrok / push** — **Resolved:** Section 8 documents push notifications as deferred and notes ngrok for development; full push design is a follow-on.
6. **Signer order storage** — **Resolved:** Store on **Deal**: `signer_order` and `signer_authentication` JSONFields (null/blank when no override). Effective order from `get_signers_for_document_set_template` when empty; auth defaults by slot (1 → SelectOneClick, 2 → SMSOneClick). Helpers: `get_signer_order_for_deal(deal, document_set_template)`, `get_signer_authentication_for_slot(deal, slot_number)`. Signers table saves auth via one form + “Save signer settings”; reorder via move up/down that POST to reorder endpoint. See Section 4.3, 5.3, 7.4 and PLAN-SIGNiX-SIGNERS-TABLE (Plan 4).
7. **GetAccessLink failure after SubmitDocument success** — **Resolved:** When SubmitDocument succeeds but GetAccessLink fails, still create the SignatureTransaction with empty `first_signing_url`; persist DocumentSetID and transaction_id; log the failure. User sees the transaction; we avoid leaving SIGNiX with no local record. See Section 6.1, 6.3. (Plan 6 — PLAN-SIGNiX-SEND-AND-PERSIST.)
8. **Send for Signature — error handling and button visibility** — **Resolved:** Validation errors (SignixValidationError): re-render deal detail with validation errors so the user can fix issues. API errors (SignixApiError): show a generic message and redirect to deal detail; do not expose API details or credentials. Use the same validation as submit (`validate_submit_preconditions`) to enable/disable the button and to supply the reason when disabled. When first_signing_url is empty (GetAccessLink failure), show success and do not open a new window. Recommended implementation for opening the URL: pass URL back (e.g. via session) and have deal detail open it in a new window; alternative is a dedicated opener page. See Section 7.1, 7.2. (Plan 7 — PLAN-SIGNiX-SEND-FOR-SIGNATURE.)
9. **Signature transactions dashboard (Plan 8)** — **Resolved:** URL `/deals/signatures/` under deals app. List description derived from deal id and document set template name (no stored label). Delete all: separate confirmation URL (GET confirm, POST delete, redirect to list). "Open link" shown to all authenticated users when first_signing_url present and status Submitted/In Progress; restricting to first signer is a possible enhancement. Access: authenticated users only. See Section 7.3.
10. **Deal View — Related signature transactions (Plan 9)** — **Resolved:** Subsection is a **separate card** below the Documents card, always shown on deal detail (empty state when no transactions; hide Delete button when empty). Delete for this deal: **separate deal-scoped URL** (e.g. `/deals/<pk>/signatures/delete-all/`) with GET = confirmation, POST = delete, redirect to deal detail. "Open signing" link: same rule as dashboard (all authenticated users when first_signing_url present and status Submitted/In Progress). Context: add `signature_transactions` in the view or in `_deal_detail_context`; ensure every path that renders deal detail (including Plan 7 re-render) includes it. Empty state: "No signature transactions for this deal." See Section 7.5 and PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS (Plan 9).

---

*End of design. Implementation will follow a PLAN document. For Flex API details, see KNOWLEDGE-SIGNiX.md and the official SIGNiX documentation.*

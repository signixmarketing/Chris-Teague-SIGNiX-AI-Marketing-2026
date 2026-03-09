# User Profiles and Value Proposition

This document describes the **users in the application domain** (the usage scenario): who they are, what they expect to do, what **pains** the system addresses for them, and what **gains** (benefits) the application can deliver. Each profile is then **mapped to the functional requirements** in [40-REQUIREMENTS.md](40-REQUIREMENTS.md) so that “why we build this feature” is traceable to “who it serves and what value it provides.” The structure is inspired by **Strategyzer’s value proposition design** (jobs to be done, pains, gains) and supports both **education** (product thinking alongside implementation) and **template reuse** (see below).

**Read this after** [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) (why and who at a high level) and **before** [20-APPROACH.md](20-APPROACH.md) and [40-REQUIREMENTS.md](40-REQUIREMENTS.md) when reviewing intent and tracing user value to requirements. Requirements should **consider and align with** these profiles and the value proposition when determining or updating what the system must do (see [20-APPROACH.md](20-APPROACH.md) Section 5.5 and 6.3).

---

## Using this document as a template

When this project is used as a **template** for another document-centric application (e.g. personal loans, wealth management onboarding), the **project lead should replace the personas and content below** with those specific to the new project. Keep the same **structure** (profile → jobs → pains → gains → mapping to requirements) but change the **role names**, **tasks**, **pains**, and **gains** to match the new domain—e.g. *loan officer* instead of *lease officer*, *borrower* instead of *lessee*, and a configuration role appropriate to that application. Update the “Maps to requirements” section to reference the new project’s requirements (or keep the requirement IDs if the new project reuses the same numbering). This ensures the value proposition and requirements traceability remain clear and useful for the new application.

**Role patterns to carry over:** Your primary user in a different domain may not be a "lease officer," but you will likely have **one or more primary users** whose job is to drive the system—creating or managing transactions, generating documents, and sending for signature (and possibly multiple such roles depending on the complexity of the use case). Your customer may not be a "lessee," but you will likely have **a customer (or other party) who signs documents** and who may not log into your application. You may not have a formal "Compliance Officer," but you will likely have **someone who cares about compliance**—ensuring that the right documents are used, policies are followed, and there is a defensible audit trail. You may not have a "lease team leader," but you will likely have **a management stakeholder** who is the decision maker, budget owner, and **executive sponsor** for the system and who cares about efficiency, compliance support, and the signer experience. When adapting this document, map each persona here to the equivalent role in your domain so that the same structure continues to guide product thinking and requirements traceability.

---

## Persona 1: Lease officer

**Who:** An employee who manages lease deals from creation through to signed documents. The **primary user** of the application in the scenario: they create and edit deals, associate vehicles and contacts, generate documents from templates, send documents for signature, and track signing status. In practice, demos and learning may be done by staff demonstrating the integration or by developers playing this role.

### Jobs to be done (tasks they perform)

- **Set up and maintain deal data** — Create deals, link vehicles and contacts, set lease terms (dates, payment, deposit, insurance, governing law), assign themselves as lease officer.
- **Generate documents for a deal** — Trigger document generation from the deal’s document set template; get draft PDFs (lease agreement, safety advisory, etc.) populated with current deal data.
- **Correct and regenerate** — When deal data changes, regenerate documents so the PDFs are up to date before sending for signature.
- **Send for signature** — Initiate the signing process: submit the document set to SIGNiX, open the first signer’s signing link (e.g. in a new window), and optionally reorder signers or set authentication per signer.
- **Track progress** — See which transactions are submitted, in progress, or complete; see related transactions on the deal detail page; open the signature transaction detail to view signers, documents, timeline, and download signed documents and artifacts.

### Pains (frustrations or risks the system can address)

- **Manual errors** — Copy-pasting data into documents or rekeying leads to mistakes and inconsistent documents. The system addresses this by generating documents from a single source of truth (deal data + templates).
- **No visibility into signing status** — Not knowing whether the customer has signed or where the process is stuck. The system provides a signature transactions dashboard and related transactions on the deal, with status and per-signer progress.
- **Scattered workflow** — Deal data in one place, documents elsewhere, signing via email or a different tool. The system keeps deal, documents, and signing in one application with a clear flow (deal detail → Documents section → Send for Signature).
- **Losing context when signing** — Being sent away from the app to sign. The first signer (lease officer) can sign in a **separate window** so they stay in the lease application.

### Gains (benefits the application can deliver)

- **One place for deal and documents** — Deal detail shows summary, vehicles, contacts, and the Documents section (generate, regenerate, view, download, send for signature). No switching between systems.
- **Consistent, professional documents** — Templates and data mapping ensure correct, repeatable output; regeneration keeps documents in sync with deal data.
- **Clear signing flow** — Signers identified from templates; order and authentication configurable; first signer opens in new window; dashboard and deal view show status and links.
- **Audit and compliance** — Document instances and versions (draft, submitted, final) and signature transaction detail (timeline, audit trail, certificate of completion) support traceability.

### Maps to requirements

| Area | Requirements |
|------|--------------|
| Access and shell | R-B1 (auth), R-B2 (profile, timezone), R-B3 (app shell) |
| Deal and domain data | R-D1 (vehicles), R-D2 (contacts), R-D3 (deals, detail view), R-D4 (deal type) |
| Document sets | R-T4 (generate, regenerate, view, download, delete document set; instances and versions) |
| Generation | R-G1 (HTML-to-PDF) |
| Signing | R-X1 (submit to SIGNiX), R-X2 (signers, reorder, authentication), R-X3 (Send for Signature, first signer link), R-X4 (dashboard, related transactions), R-X5 (push, status), R-X6 (download on complete), R-X7 (transaction detail page) |
| Data for documents | R-S1, R-S2 (schema, get_deal_data used by generation) |

---

## Persona 2: Lessee (signer)

**Who:** The customer/contact who signs the lease documents (e.g. the lessee). They **do not log into** the lease application. They receive an email from SIGNiX with a link to the signing experience; they sign in SIGNiX’s hosted flow and may receive signed copies or confirmations according to SIGNiX and the application’s behavior.

### Jobs to be done (tasks they perform)

- **Receive the signing request** — Get an email from SIGNiX (or equivalent) with a link to view and sign the documents.
- **Open and sign** — Click the link, complete the SIGNiX signing process (view documents, fill/sign assigned fields, authenticate as required).
- **Complete signing** — Finish their part; SIGNiX advances the workflow to the next signer or marks the transaction complete.
- **Obtain signed documents** — When the transaction is complete, the application (and SIGNiX) can make signed PDFs, audit trail, and certificate of completion available; the lessee may receive these via SIGNiX or from the lease officer.

### Pains (frustrations or risks the system can address)

- **Confusion about what to do** — Unclear links, multiple emails, or unclear order of steps. The system and SIGNiX provide a single, clear link per signer and a defined flow.
- **Trust and legitimacy** — Wanting assurance that the process is secure and the documents are official. SIGNiX provides authentication options and audit trail; the application stores final versions and certificates.

### Gains (benefits the application can deliver)

- **Sign from email** — One link in the email leads to the correct set of documents and fields for that signer (per template configuration).
- **Clear, focused experience** — SIGNiX-hosted flow shows only the documents and fields assigned to that signer (no need to log into the lease application).
- **Signed copies and proof** — When the transaction completes, the application downloads and stores signed documents and artifacts so the lease officer (and organization) have a record; signers benefit from a completed, traceable process.

### Maps to requirements

The lessee interacts with the **result** of application features rather than the UI directly. Requirements that enable their experience:

| Area | Requirements |
|------|--------------|
| Correct signer and documents | R-X1 (submit with correct document set and signers), R-X2 (slots resolved to people; signer order and auth) |
| Invitation and link | R-X1, R-X3 (submit produces first signer link; other signers receive SIGNiX email) |
| Status and completion | R-X5 (push updates status), R-X6 (download on complete; signed docs and audit stored) |
| Data in documents | R-S2, R-T4, R-G1 (documents generated with correct deal data so what they sign is accurate) |

---

## Persona 3: System administrator (configuration)

**Who:** Staff who **configure** the application: document templates (static and dynamic), document set templates, deal types, SIGNiX credentials and settings, and (via the admin area) users and roles. In a **small deployment** this may be the same person as the lease officer; in larger environments a dedicated admin or “power user” fills this role. For this project we use the term **system administrator** to align with [40-REQUIREMENTS.md](40-REQUIREMENTS.md) (R-B4).

### Jobs to be done (tasks they perform)

- **Manage users** — Create or disable users, assign staff access; ensure at least one user exists for initial setup (e.g. via idempotent setup command).
- **Configure deal types and document set templates** — Associate document set templates with deal types so that “generate documents for this deal” uses the right set of templates (e.g. “Lease - Single Signer” → lease agreement + safety advisory).
- **Upload and configure document templates** — Add static templates (PDFs with form fields) and dynamic templates (HTML with placeholders); configure mapping of template variables to deal data; configure text tagging (signature/date fields, signer slots) for SIGNiX.
- **Configure SIGNiX** — Set credentials, workgroup, submitter info, default email content, and other SIGNiX-specific settings so that “Send for Signature” can call the SIGNiX API.
- **Upload images or assets** — Add logos or other assets that templates reference (e.g. company logo in the header of generated PDFs).

### Pains (frustrations or risks the system can address)

- **Having to change code to change documents** — If document structure or mapping were hardcoded, every change would require a developer. The system uses **configurable** templates, mapping, and tagging so admins can update templates and configuration without code changes.
- **Wrong or missing configuration causes failures** — Submit fails if SIGNiX credentials or submitter email are missing; generation fails if mapping or templates are misconfigured. The application can **validate** and show clear messages (e.g. “No document set template configured for this deal type”; “SIGNiX configuration incomplete”) so the admin knows what to fix.
- **No single place for configuration** — Scattered settings across systems. The application provides an **admin area** (users) and configuration pages (templates, document set templates, SIGNiX config, images) so configuration is findable and manageable.

### Gains (benefits the application can deliver)

- **Configure, don’t code** — Document set templates, deal types, template mapping, and tagging are configuration; SIGNiX settings are form-driven. Admins can adapt the application to new deal types or document sets without developer involvement (within the designed flexibility).
- **Clear ownership of configuration** — Admin area and in-app configuration pages give a single place to manage users and signing/document setup.
- **Reusable patterns** — Once a template and document set template are configured for one deal type, every deal of that type gets the same document set; adding a new deal type is a matter of adding a document set template and associating it with the deal type.

### Maps to requirements

| Area | Requirements |
|------|--------------|
| Admin and users | R-B4 (admin area, navigation app ↔ admin), R-B5 (initial user setup) |
| Deal types and document set templates | R-D4 (deal type), R-T3 (document set templates, ordered list, associated with deal type) |
| Document templates | R-T1 (static: upload, metadata, form field config), R-T2 (dynamic: upload, mapping, text tagging) |
| Images/assets | R-I1 (upload, storage, stable URLs for templates) |
| SIGNiX configuration | R-X1 (submit uses config; credentials, submitter, etc. from configuration) — see also SIGNiX config plan in 07-SIGNiX-SUBMIT |
| Data interface (for mapping UI) | R-S1 (schema for mapping dropdowns and validation) |

---

## Persona 4: Compliance officer

**Who:** A **stakeholder who does not use the application day-to-day**. The compliance officer (or equivalent—e.g. risk, legal, or quality assurance) is responsible for ensuring that lease officers create and execute leases in accordance with **regulations** (e.g. consumer leasing disclosure requirements, state or federal leasing laws) and **company policies and standards**. Without a solid system that guides the lease officer through a consistent, auditable process, the compliance officer finds it hard to ensure that every deal follows the required document set, disclosures, and signing workflow.

### Jobs to be done (tasks they perform)

- **Define and maintain policies and standards** — Establish which documents must be included in a lease (e.g. lease agreement, safety advisory, disclosure forms), what content or disclosures they must contain, and in what order signers should execute them. Work with the system administrator (or configuration role) so that document set templates and deal types reflect these policies.
- **Review and sample for compliance** — Periodically review deals and generated documents to confirm that the right templates were used, data was applied correctly, and the signing process was followed. May request access to transaction history, signed documents, or audit trail for specific deals.
- **Respond to audits and regulators** — When auditors or regulators ask for evidence of process (e.g. “What document set was sent for this deal?” “Who signed and when?” “Can we see the signed PDFs and certificate?”), provide or facilitate access to the application’s stored document instances, versions, and signature transaction detail (timeline, audit trail, certificate of completion).
- **Ensure process is repeatable and defensible** — Reduce reliance on individual lease officers “doing it right” by ensuring the system enforces the use of approved templates and a consistent signing flow, so that exceptions and one-off documents are minimized.

### Pains (frustrations or risks the system can address)

- **No consistent process** — Without a system that guides lease officers through a defined workflow (deal → generate from template → send for signature), officers may use ad-hoc documents, skip required disclosures, or sign in inconsistent ways. The application addresses this by tying document generation to **document set templates** and **deal types**, so the right set of documents is generated every time for a given deal type.
- **No visibility into what was actually sent and signed** — If documents are created in Word or PDFs are emailed manually, the compliance officer cannot easily see what was sent to the customer or prove what was signed. The system stores **document instances and versions** (draft, submitted to SIGNiX, final) and **signature transaction detail** (signers, timeline, audit trail, certificate of completion), so there is a single place to see what was generated, submitted, and signed.
- **Template and policy changes are hard to enforce** — When policies change (e.g. a new disclosure is required), ensuring every officer uses the updated document is difficult if templates are maintained locally or in code. The application uses **configurable** document templates and document set templates managed by the system administrator, so policy updates can be reflected in approved templates and applied to all deals of that type.
- **Weak or missing audit trail** — Regulators and auditors expect evidence of who signed what and when. The application, together with SIGNiX, stores signed documents, event timeline, and certificate of completion per transaction, supporting a defensible audit trail.

### Gains (benefits the application can deliver)

- **Standardized document set per deal type** — Deal type → document set template ensures that every lease of a given type uses the same ordered set of approved documents. Compliance can define “for this deal type, these documents are required” and have the system enforce it at generation time.
- **Single source of truth for deal data in documents** — Documents are generated from deal data via templates (no manual copy-paste), so the content is consistent and traceable to the deal. Regeneration when deal data changes keeps documents aligned and reduces the risk of sending outdated or incorrect terms.
- **Traceable signing process** — Signature transaction detail page and stored artifacts (signed PDFs, audit trail, certificate of completion) give the compliance officer (or auditor) a clear record of what was sent, who signed, and when. SIGNiX provides authentication and signing evidence; the application persists it per transaction.
- **Configurable templates, not code** — When regulations or policies change, the system administrator can update or add templates and document set templates. Compliance can work with that role to embed policy in the configuration, so the organization can adapt without developer-led releases for every document change.

### Maps to requirements

The compliance officer benefits from **how** the application is built and what it stores, rather than from using the UI directly. Requirements that support their goals:

| Area | Requirements |
|------|--------------|
| Standard document set per deal type | R-D4 (deal type), R-T3 (document set template, ordered list, associated with deal type), R-T4 (generate from template) |
| Approved templates and content | R-T1 (static templates), R-T2 (dynamic templates, mapping), R-T4 (document instances and versions) |
| Traceability and audit | R-T4 (document instances and versions: draft, submitted, final), R-X6 (download on complete; signed docs, audit trail, certificate stored), R-X7 (signature transaction detail: timeline, signers, documents, audit trail, certificate) |
| Consistent data in documents | R-S2 (get_deal_data as single source), R-G1 (HTML-to-PDF), R-T4 (regenerate when deal data changes) |

---

## Persona 5: Lease team leader (executive sponsor)

**Who:** The **leader of the lease team**—job title varies by organization size (e.g. Director, VP, SVP, CEO, COO, or another C-level). They do **not** create leases in the system day-to-day but may **log in periodically** to assess the situation. They are the **decision maker** on what systems the team uses, typically **own the budget** for those systems, and act as **executive sponsor** for new projects and change management. Although the application may not address this persona fully in the first release or two, their needs become **increasingly important as the application matures** and should inform roadmap and prioritization.

### Jobs to be done (tasks they perform)

- **Assess how the team is doing** — Log in periodically to see deal volume, signature transaction status, and where work is stuck or delayed. Use the signature transactions dashboard and deal-level views to get a sense of pipeline and completion.
- **Support efficiency and compliance** — Ensure lease officers can do their work efficiently (standardized process, one place for deal and documents, clear signing flow) and that the compliance officer has the tools and visibility to do their job (standard templates, audit trail). Advocate for or approve system investments that enable both.
- **Care about the customer/signer experience** — Want lessees and other signers to have a clear, trustworthy signing experience so that deals complete and relationships stay positive. Influence process and system design so the signer journey is smooth and professional.
- **Troubleshoot when the process breaks down** — When something goes wrong (e.g. a customer hasn’t signed after a period of time, a transaction is stuck, or an officer needs help), want **tools for troubleshooting and getting processes back on track**—e.g. identifying transactions that have been pending for too long, or seeing which deals have no signed documents. Such capabilities may be in scope in later releases.
- **Use reports and metrics to manage the business** — Like to have **reports and key metrics** (e.g. deals created, documents sent, completion rates, time-to-sign) to track performance and manage the team. Reporting and dashboards beyond the current signature transactions list are often a **later-phase** capability.
- **Own system selection and sponsorship** — Decide which systems the team uses, own the budget, and sponsor new projects (including this application) and change management so adoption succeeds.

### Pains (frustrations or risks the system can address)

- **No visibility into pipeline and status** — Without a system, hard to know how many deals are in progress, how many documents are awaiting signature, or where bottlenecks are. The application provides a **signature transactions dashboard** and **related transactions on the deal view**, so the leader (or anyone with access) can see submitted and in-progress transactions. Deeper reporting and metrics may follow in later releases.
- **Process breakdowns are hard to detect and fix** — When a customer hasn’t signed after a period of time, or a transaction is stuck, the leader wants to identify and act. Today the dashboard and transaction detail page support **manual** inspection; **proactive** tools (e.g. “unsigned after X days,” alerts, or lists of stale transactions) are a natural evolution as the application matures.
- **Efficiency and compliance depend on the right system** — If lease officers work in scattered tools or ad-hoc documents, the leader cannot easily ensure efficiency or support compliance. A single application with a defined workflow (deal → generate → send for signature → track) gives the leader a **basis** to expect consistent process and to support the compliance officer’s needs.
- **Budget and sponsorship need a clear value story** — When evaluating or sponsoring a new system, the leader needs to see how it improves efficiency, supports compliance, and improves the signer experience. The value proposition for lease officers, compliance, and signers (as in this document) helps the leader justify investment and drive adoption.

### Gains (benefits the application can deliver)

- **Current release:** **Visibility** — Signature transactions dashboard and related transactions on the deal view let the leader (or a delegate) see what has been submitted, what is in progress, and what has completed. Transaction detail page provides signers, timeline, and documents for troubleshooting. Consistent workflow (deal → documents → signing) supports efficiency and gives compliance a foundation to work with.
- **As the application matures:** **Reports and metrics** — Key metrics (deals, documents sent, completion rates, time-to-sign) and simple reports to manage the business. **Troubleshooting tools** — Identify transactions or deals that have been pending too long (e.g. customer hasn’t signed after X days), so the team can follow up and get processes back on track. **Better support for the leader role** — Optional features such as read-only or summary views, or role-based access that lets the leader see aggregate data without day-to-day use, may be added in later versions.

### Maps to requirements

**Today (first release(s)):** The leader benefits mainly from the **same visibility** that supports lease officers and compliance: a single application with a clear workflow, plus the signature transactions dashboard and deal-level related transactions. Requirements that support this:

| Area | Requirements |
|------|---------------|
| Visibility into transactions | R-X4 (signature transactions dashboard, related transactions on deal view), R-X7 (transaction detail: signers, timeline, documents, audit trail, certificate) |
| Consistent process and workflow | R-D3–D4, R-T3–T4, R-X1–X3 (deal → document set template → generate → send for signature) |

**Later / future:** Reporting, key metrics, proactive troubleshooting (e.g. “unsigned after X days”), and dedicated leader or executive views are **not** in scope for the first version (see [30-SCOPE.md](30-SCOPE.md)) but align with this persona’s needs as the application matures. Prioritization of such features can be traced back to the lease team leader persona.

---

## Summary: persona → requirement areas

| Persona | Primary requirement areas |
|----------|---------------------------|
| **Lease officer** | R-B1–B3, R-D1–D4, R-T4, R-G1, R-S1–S2, R-X1–X7 |
| **Lessee (signer)** | R-X1–X6, R-S2, R-T4, R-G1 (indirect: correct docs and flow) |
| **System administrator** | R-B4–B5, R-D4, R-T1–T3, R-I1, R-S1, R-X1 (config); SIGNiX config plans |
| **Compliance officer** | R-D4, R-T1–T4, R-S2, R-G1, R-X6–X7 (indirect: standardized process, audit trail, configurable templates) |
| **Lease team leader** | R-X4, R-X7 (visibility today); R-D3–D4, R-T3–T4, R-X1–X3 (consistent process). Reporting, metrics, and troubleshooting tools are later/future. |

---

*For the high-level “who we serve” narrative, see [10-PROJECT-PITCH.md](10-PROJECT-PITCH.md) Section 3. For the system capabilities that satisfy these profiles, see [40-REQUIREMENTS.md](40-REQUIREMENTS.md). For how we build and document, see [20-APPROACH.md](20-APPROACH.md).*

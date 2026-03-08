# Knowledge: Vehicle Leasing (Jet Packs) — This Application’s Domain

This document describes the **business domain** of this specific application: a company that **leases jet packs** (and potentially other vehicles). It clarifies the business objects, their relationships, and the terminology used in the product. This is the **instantiation** of the general document-centric pattern described in [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md): here, “products” are **Vehicles** (jet packs), “customers” are **Contacts** (lessees, co-signers), and “deals” are **Deals** (lease origination records).

**Design and implementation:** For this application’s design decisions (entity model, UI conventions, deal-centric workflow), see [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md). For implementation order and deliverables, see [PHASE-PLANS-BIZ-DOMAIN.md](PHASE-PLANS-BIZ-DOMAIN.md) and the individual PLAN-ADD-VEHICLES, PLAN-ADD-CONTACTS, and PLAN-ADD-DEALS files.

---

## 1. What This Application Does (Domain Summary)

The application supports **lease origination** for a company that leases jet packs. An employee (the **lease officer**) uses the app to:

- Maintain a **catalog of vehicles** (jet packs) that can be leased—each with an identifier (SKU), year, and JPIN.
- Maintain **contacts**—people who may be lessees or co-signers on a lease.
- Create and manage **deals**—each deal is one lease: it links to one or more vehicles, one or more contacts (e.g. lessee and co-signer), and has lease terms (dates, payment, deposit, insurance, governing law). The lease officer is the internal user responsible for the deal.
- When the deal is ready, **generate documents** from templates (populated with deal data) and **send them for signature** (lessee, co-signer, and optionally the lease officer). When signing is complete, the app stores the final, signed documents.

So in the language of [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md): **products** = Vehicles (jet packs), **customers** = Contacts, **deals** = Deals (lease origination records). The rest of the stack (data interface, document templates, document sets, signing) is the same pattern.

---

## 2. Business Objects and Why They Matter

### 2.1 Vehicle (jet pack)

- **What it is:** A leaseable asset—in this app, a **jet pack**. The company has a catalog of jet packs that can be attached to lease deals.
- **Key attributes:** **SKU** (product identifier, e.g. “Skyward Personal Jetpack P-2024”), **year** (e.g. “2024”), **JPIN** (Jet Pack Identification Number—a unique identifier for the unit, used for registration, tracking, and documents).
- **Why it matters:** Every lease deal is for one or more specific vehicles. The deal’s vehicles appear in generated documents (e.g. lease agreement, safety advisory) and in the deal’s data used for signing. Vehicles are managed once and reused across deals.
- **In the data model:** `Vehicle` in `apps.vehicles`; `Deal` has a ManyToMany `vehicles`. See [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md) and [10-PLAN-ADD-VEHICLES.md](10-PLAN-ADD-VEHICLES.md).

### 2.2 Contact

- **What it is:** A **person** who can be a party to a lease—typically the **lessee** (primary customer) or a **co-signer** (e.g. guarantor). Contacts are not necessarily “customers” in a CRM sense; they are the people whose names, emails, and phone numbers appear on the deal and in the documents, and who may be signers.
- **Key attributes:** First name, middle name (optional), last name, email, phone number. The app may use email/phone for signing invitations (e.g. SIGNiX).
- **Why it matters:** The deal links to one or more contacts. Document templates and signing workflows use these contacts (e.g. “first contact” = primary lessee, “second contact” = co-signer). Contacts are managed once and attached to deals as needed.
- **In the data model:** `Contact` in `apps.contacts`; `Deal` has a ManyToMany `contacts`. See [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md) and [20-PLAN-ADD-CONTACTS.md](20-PLAN-ADD-CONTACTS.md).

### 2.3 Deal type

- **What it is:** A **classification** of the lease deal. In this application there is one type in v1: **“Lease - Single Signer”**—meaning a single primary signer (plus the lease officer if configured). Other types could be added later (e.g. “Lease - Multi Signer” for multiple lessees/co-signers).
- **Why it matters:** The **document set template** (which documents to generate and in what order, and which signer slots they use) is associated with **deal type**. So “Lease - Single Signer” determines the set of documents and signer configuration for this app’s leases. See [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md).
- **In the data model:** `DealType` in `apps.deals`; `Deal` has a ForeignKey `deal_type`. The default is set automatically; not shown in user forms in v1. See [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md) and [30-PLAN-ADD-DEALS.md](30-PLAN-ADD-DEALS.md).

### 2.4 Deal (lease origination record)

- **What it is:** One **lease transaction**—the central record that ties together which vehicles are being leased, which people are parties (lessee, co-signer), which employee is the lease officer, and the lease terms (dates, payment, deposit, insurance, governing law).
- **Key attributes:**
  - **Relations:** Lease officer (User), deal type, vehicles (M2M), contacts (M2M).
  - **Properties:** Date entered, lease start date, lease end date, payment amount, payment period (e.g. monthly), security deposit, insurance amount, governing law (e.g. state).
- **Why it matters:** The deal is the **root object** for document generation and signing. “Generate documents for this deal” means: take this deal’s data (and its vehicles, contacts, lease officer) and populate the document set template. “Send for signature” means: send the deal’s current document set to the signers (derived from the deal’s contacts and lease officer). All downstream features (DESIGN-DATA-INTERFACE, DESIGN-DOCS, SIGNiX) are deal-centric.
- **In the data model:** `Deal` in `apps.deals`. See [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md) and [30-PLAN-ADD-DEALS.md](30-PLAN-ADD-DEALS.md).

---

## 3. Terminology Glossary

| Term | Meaning in this application |
|------|-----------------------------|
| **Lease officer** | The **employee** (internal user) responsible for the deal. They create the deal, enter data, attach vehicles and contacts, and trigger document generation and sending for signature. Stored as `Deal.lease_officer` (ForeignKey to User). |
| **Lessee** | The **customer** who is the primary party to the lease—typically the first contact on the deal. May be the first signer in the signing order. |
| **Lessor** | The company that owns the jet packs and leases them (the organization using this application). Not a separate entity in the data model; implied by context. |
| **Co-signer** | A second (or subsequent) party to the lease—e.g. guarantor. Represented as an additional **Contact** on the deal. Signing order and roles are configured in document templates (e.g. `member_info_number` in DESIGN-DOCS / DESIGN-SIGNiX-SUBMIT). |
| **JPIN** | **Jet Pack Identification Number**—a unique identifier for each vehicle (jet pack). Used in documents and for tracking. Stored as `Vehicle.jpin` (unique). |
| **Deal type** | Classification of the deal (e.g. “Lease - Single Signer”). Drives which document set template applies. Not to be confused with “type of vehicle”; it’s the type of *lease transaction*. |
| **Security deposit** | Amount the lessee puts down as security for the lease. Stored as `Deal.security_deposit`. |
| **Insurance amount** | Amount or level of insurance the lessee must maintain for the vehicle. Stored as `Deal.insurance_amount`. |
| **Governing law** | Jurisdiction (e.g. state) that governs the lease agreement. Stored as `Deal.governing_law`. |
| **Document set** | The set of documents generated for a deal (from the document set template) and optionally sent for signature. See [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md). |

---

## 4. Relationships at a Glance

- **Deal → Lease officer:** One deal has one lease officer (User). Defaults to the current user when creating.
- **Deal → Deal type:** One deal has one deal type. Default “Lease - Single Signer” in v1.
- **Deal → Vehicles:** One deal can have zero or more vehicles (the jet packs being leased). ManyToMany.
- **Deal → Contacts:** One deal can have zero or more contacts (lessee, co-signer(s)). ManyToMany.

Vehicles and contacts have **no** direct relationship to each other; they are linked only through deals. The order of contacts on a deal may matter for signing (e.g. first contact = primary lessee, second = co-signer); the app and document/signing design use that convention. See [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) (e.g. `deal.contacts` order) and [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) (signer slots).

---

## 5. References

| Document | Content |
|----------|---------|
| [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) | General pattern: products, customers, deals, document generation, signing. This app is one instance of that pattern. |
| [DESIGN-BIZ-DOMAIN.md](DESIGN-BIZ-DOMAIN.md) | This application’s design: entities, relationships, UI conventions, deal-centric workflow. |
| [PHASE-PLANS-BIZ-DOMAIN.md](PHASE-PLANS-BIZ-DOMAIN.md) | Implementation order for Vehicles, Contacts, Deals; links to PLAN-ADD-VEHICLES, PLAN-ADD-CONTACTS, PLAN-ADD-DEALS. |
| [04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md](../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md) | Deal-centric schema and `get_deal_data(deal)`—how deal, vehicles, contacts, and lease officer are exposed for document population. |
| [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) | Document templates and document sets; association with deal type; workflow toward signing. |

---

*This knowledge file describes the **leasing / jet-pack domain** of this application. For the general pattern of document-centric business apps and how to reuse this project in other domains, see [GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md).*

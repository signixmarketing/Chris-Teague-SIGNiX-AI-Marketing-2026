# SIGNiX Market Research & Buyer Journey

**Last updated:** April 2, 2026  
**Purpose:** Synthesized research on SIGNiX's target market, regulatory landscape, buyer personas, and customer journey. Use this document to guide messaging, ad targeting, landing page copy, outbound sales lists, and campaign strategy.

---

## Sources Used

| Source | URL | Key use |
|--------|-----|---------|
| FINRA Books & Records | finra.org/rules-guidance/key-topics/books-records | Regulatory obligations for broker-dealers |
| FINRA FinTech Hub | finra.org/rules-guidance/key-topics/fintech | RegTech, AI fraud, cybersecurity guidance |
| SEC Exchange Act Rule 17a-4 | govinfo.gov | Electronic recordkeeping requirements |
| ThinkAdvisor | thinkadvisor.com | Wealth management industry news and advisor pain points |
| Investment News | investmentnews.com | RIA and broker-dealer technology coverage |

---

## Regulatory Landscape (What Creates Urgency for Our Buyers)

### The live compliance trigger

The SEC amended Exchange Act Rule 17a-4 in October 2022. The compliance deadline was May 3, 2023. Every registered broker-dealer in the US had to update how they store, retrieve, and audit electronic records. Many firms are still catching up or facing exam findings because of it.

**This is live urgency — not historical anxiety.** FINRA's 2025 and 2026 Annual Regulatory Oversight Reports both flagged books and records as an active examination area. Every compliance officer at a broker-dealer reads this report. The fear is being activated by FINRA itself, right now.

### What the rules actually require

**FINRA Rule 4511** requires broker-dealers to:
- Maintain books and records in a format that complies with Exchange Act Rule 17a-4
- Default retention period: 6 years for records without a specified retention period

**Exchange Act Rule 17a-4 (as amended 2022–2023)** requires electronic records to:
- Include a **complete time-stamped audit trail** — who created, modified, or deleted the record, and when
- Be stored in either WORM format (non-rewriteable, non-erasable) or with a full audit trail
- Be immediately retrievable and producible on demand from SEC or FINRA
- Automatically verify completeness and accuracy of stored records
- Support download/transfer in human-readable and machine-readable format

**The compliance gap SIGNiX closes:** A generic click-to-sign tool (DocuSign, Adobe Sign) does not automatically satisfy Rule 17a-4. It can produce a certificate of completion, but it does not inherently prove *who* signed using verified identity. SIGNiX's PKI-based digital signatures, built-in authentication (KBA, OTP, biometric), and Fraud Alert tool do. That claim is legally defensible.

### Key penalty context

Failure to meet FINRA and SEC recordkeeping requirements results in:
- Fines and monetary sanctions
- Disciplinary actions including suspension or bar
- Reputational damage from public FINRA enforcement actions

**One FINRA fine can cost more than years of SIGNiX.** This is a closing line that works.

---

## Buyer Personas

### Persona 1: Chief Compliance Officer (CCO) at a broker-dealer or RIA

**Job title variations:** CCO, VP of Compliance, Director of Compliance, Compliance Manager

**Primary fear:** FINRA or SEC exam findings. A books-and-records deficiency is career risk.

**Primary job:** Make sure the firm's electronic records are defensible on the first request in an audit.

**What keeps them up at night:**
- "If FINRA walked in tomorrow, could we produce every signed document with full identity proof?"
- "Are our e-signatures actually compliant with Rule 17a-4, or are we just assuming they are?"
- "We had an incident — can we prove what was signed?"

**What triggers them to search for a solution:**
- A FINRA exam flag on electronic records
- Seeing a peer firm receive a public enforcement action
- Reading the FINRA Annual Regulatory Oversight Report (published every January)
- An internal audit finding
- A client dispute where they can't verify a signature

**Search behavior:** Compliance-first keywords. They search for the rule name, not the product category.
- `SEC Rule 17a-4 compliant e-signature`
- `FINRA compliant digital signature`
- `non-repudiation e-signature financial services`
- `electronic signature audit trail broker dealer`

**Message that works:** "After that signature, can you prove in a FINRA exam exactly who signed it? SIGNiX can."

---

### Persona 2: VP / Director of Operations at a bank, credit union, or financial institution

**Primary fear:** Operational and fraud risk. A dispute they lose because they can't produce proof.

**Primary job:** Make workflows fast and defensible without adding compliance risk.

**What keeps them up at night:**
- A customer disputes a wire authorization or beneficiary change and claims they didn't sign
- AI-generated fraud — a deepfake or impersonated client signature
- An internal process that's slow and paper-heavy but the replacement creates risk

**What triggers them to search:**
- A fraud incident or near-miss
- A customer complaint that can't be resolved
- A vendor asking if they're using e-sign (TruStage / CSI prompt)
- A competitor FI going digital and their own customers asking why they aren't

**Search behavior:** Workflow + fraud keywords.
- `secure e-signature for wire transfers`
- `identity verification for document signing`
- `AI fraud e-signature financial services`
- `authentication for high-risk transactions`

**Message that works:** "Anyone can click a button. SIGNiX proves it was your customer."

---

### Persona 3: Financial Advisor / RIA (individual practice or team)

**Primary fear:** Client dispute with no paper trail. Practice liability.

**Primary job:** Protect client relationships and protect the practice.

**What triggers them:**
- A difficult client situation where the advisor can't prove what was authorized
- A compliance reminder from their broker-dealer about record-keeping
- Reading about AI fraud targeting advisor-client relationships

**Search behavior:** Workflow-specific, less technical.
- `esignature for rollover forms`
- `wealth management document signing`
- `secure client signature beneficiary changes`
- `DocuSign alternative for financial advisors`

**Message that works:** "Protect your practice. Every form, every signature, every time — with proof of who signed."

---

### Persona 4: ISV Product Manager (Flex API buyer)

**Primary fear:** Building a signing workflow that fails a customer's compliance audit and damages the relationship.

**Primary job:** Ship product that works in regulated industries without creating liability.

**What triggers them:**
- A regulated-industry customer demands compliant e-sign
- A prospect asks "are you FINRA/SEC compliant?" and they don't have a good answer
- Competitive gap — a competitor's platform has compliant signing and they don't

**Message that works:** "Your customers live in regulated industries. SIGNiX's Flex API is built for that. Compliance is in the platform, not your problem to build."

---

## Customer Journey Maps

### Journey A: CCO / Compliance buyer

| Stage | What happens | SIGNiX touch point |
|-------|-------------|---------------------|
| **Trigger** | FINRA exam flag, enforcement news, Annual Oversight Report, internal audit | None yet — they become aware of their gap |
| **Problem definition** | Ask: "Are our e-signatures actually Rule 17a-4 compliant?" | None yet |
| **Google search** | `SEC 17a-4 compliant e-signature`, `FINRA electronic signature audit trail` | **Google Ad appears here** |
| **Landing page** | 30-second scan: Does this solve my specific compliance problem? Do I trust them? | Compliance-forward landing page with Fraud Alert proof point |
| **Form fill** | Low-commitment CTA: "Talk to a compliance specialist" or "See how Fraud Alert works" | HubSpot captures lead, routes to sales |
| **Sales engagement** | Discovery call, demo, internal champion presents to IT and legal | Mike's fraud insights email nurtures if not ready to buy |
| **Decision** | Procurement, compliance sign-off, contract | |
| **Activation** | Implementation, first transactions signed | |
| **Growth (depth lever)** | Authentication adoption grows — every new auth is incremental revenue | |

---

### Journey B: Wealth management / financial advisor buyer

| Stage | What happens | SIGNiX touch point |
|-------|-------------|---------------------|
| **Trigger** | Client dispute on rollover, beneficiary change they can't verify, AI fraud story | |
| **Problem definition** | "How do I prove my client actually signed this?" | |
| **Google search** | `esignature rollover forms`, `wealth management document signing`, `secure signature beneficiary change` | **Google Ad — wealth management bucket** |
| **Landing page** | Workflow-specific messaging: "Built for the forms advisors use every day" | |
| **Form fill** | Demo request or contact form | |
| **Sales** | Short cycle if individual advisor; longer if firm-level | |

---

### Journey C: Existing TruStage FI customer (depth lever)

| Stage | What happens | SIGNiX touch point |
|-------|-------------|---------------------|
| **Awareness** | FI already has SIGNiX available via TruStage / CSI but hasn't activated authentication | |
| **Trigger** | Fraud incident, compliance reminder, or direct outreach from SIGNiX | **Mike's email / direct outreach** |
| **Engagement** | "You already have this — here's how to turn it on" | |
| **Activation** | Authentication added to existing signing workflows | |
| **Growth** | Each authenticated transaction = incremental revenue | |

---

## Messaging Framework

| Buyer | Fear opener | SIGNiX answer | Proof point |
|-------|------------|----------------|-------------|
| CCO / Compliance | FINRA exams are flagging electronic records right now | SIGNiX produces a tamper-proof audit trail that satisfies Rule 17a-4 on the first request | Fraud Alert built to FINRA guidance |
| VP Operations | One disputed transaction you can't prove costs more than the platform | Every signature is identity-bound and verifiable | PKI-based, non-repudiation standard |
| Financial Advisor | AI fraud is targeting client accounts | SIGNiX verifies who signed, not just that something was signed | KBA, biometric, OTP built in |
| ISV / Product Manager | Your customers operate in regulated industries — your platform needs to prove it | Flex API with compliance built in, not bolted on | White-label, FINRA/SEC-ready out of the box |

---

## Google Ad Keyword Buckets (CEO-approved $3,000/month budget)

Ranked by priority. Budget weighted toward top buckets.

| Priority | Bucket | Example keywords | Rationale |
|---------|--------|-----------------|-----------|
| 1 | Compliance / Regulatory | `SEC compliant e-signature`, `FINRA Rule 17a-4 digital signature`, `non-repudiation financial services`, `electronic recordkeeping compliance` | Highest intent, highest-value buyer, CEO-prioritized |
| 2 | Fraud / Authentication | `AI fraud e-signature`, `identity verification document signing`, `multi-factor authentication e-sign`, `SIGNiX Fraud Alert` | Connects to Fraud Alert; feeds Mike's email audience |
| 3 | Wealth Management Workflows | `esignature rollover forms`, `IRA distribution signature`, `beneficiary change form signing`, `wealth management document workflow` | CEO keyword doc; new segment, lower competition |
| 4 | Competitor Displacement | `DocuSign alternative financial services`, `Adobe Sign alternative compliance`, `better than DocuSign regulated industries` | Mid-funnel; captures buyers already in evaluation |
| 5 | RON Institutional | `remote online notarization platform`, `RON software broker dealer` | Keep small; $200–300 max |

---

## Outbound Sales List Sources (Free, Public)

These databases let your sales team build targeted outbound lists without buying a data subscription.

| Source | URL | What it gives you |
|--------|-----|-------------------|
| **FINRA BrokerCheck** | brokercheck.finra.org | Every registered broker-dealer in the US; filterable by firm type and state |
| **SEC IAPD** | adviserinfo.sec.gov | Every SEC-registered investment adviser (RIAs); AUM, location, employee count |
| **NCUA Credit Union Data** | ncua.gov/analysis | All federally insured credit unions with asset size, member count, location |
| **FDIC BankFind** | banks.data.fdic.gov | All FDIC-insured banks; filterable by asset size, state, charter type |

**Recommended outbound priority order:**
1. Broker-dealers with 50–500 registered reps (big enough to have compliance staff, small enough to need help)
2. RIAs with $100M–$5B AUM (high transaction volume, compliance-sensitive)
3. Credit unions with $500M+ assets (TruStage relationship overlap)
4. Community banks with $250M+ assets (digital transformation budget)

---

## Open Questions (Answers Sharpen Everything Above)

1. **Who are SIGNiX's best current customers?** Firm type, size, and which workflow they use SIGNiX for. Two or three examples create a pattern to replicate.
2. **Does SIGNiX have compliance certifications or published case studies?** Trust signals for landing pages and outbound emails.
3. **How exactly does Fraud Alert work?** Specifically: which FINRA guidance was it built against? This makes the compliance claim precise and defensible.
4. **What is the sales team's preferred outbound method?** Cold email, LinkedIn InMail, phone, or mix? This shapes the list format and the outbound sequence.
5. **What is a typical deal ACV for a non-notary customer?** Even a rough range tells us how much we can spend per lead before it stops making sense.
6. **Does HubSpot already have a lead source field for paid search?** If not, tracking daily lead volume (as the CEO wants) requires a setup step before launch.
7. **Who manages the Google Ads account day-to-day?** Chris, an agency, or someone else? This affects how granular the build plan needs to be.

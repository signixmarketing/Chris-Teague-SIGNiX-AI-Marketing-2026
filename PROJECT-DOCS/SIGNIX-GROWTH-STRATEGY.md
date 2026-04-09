# SIGNiX Growth Strategy — Living Document

**Owner:** Chris (Head of Growth and Marketing)  
**Started:** April 1, 2026  
**Purpose:** Record key decisions, strategic frameworks, open questions, and action items emerging from marketing and growth work. Update as decisions are made and validated.

---

## 1. Business Problem Statement

SIGNiX has a **structural transaction-volume gap** with TruStage, its primary channel partner. The contract was built on volume assumptions the current integration model cannot reach on its own because:

- SIGNiX sits at the **end of a four-party value chain**: Bank/CU (buyer) → CSI/Hawthorn River LOS → TruStage (loan docs) → SIGNiX (e-sign).
- SIGNiX owns no direct customer relationship at any step before the signing event.
- Many TruStage-enabled FIs have **not embedded SIGNiX into their daily workflows**.
- Customers who do use e-sign are largely **using zero authentications**, leaving incremental revenue uncaptured.

---

## 2. Two Growth Levers (CEO-confirmed, April 2026)

| Lever | Definition | Primary vehicle |
|-------|------------|-----------------|
| **Depth** | Activate authentication on transactions already being signed by TruStage FI customers | Mike's email campaign → direct discovery calls |
| **Width** | Expand SIGNiX into workflows beyond loan documents within TruStage accounts (and new prospects) | Direct FI outreach + Google Ads + analyst relations |

---

## 3. The Value Chain (structural context)

```
Bank / Credit Union (buyer)
        ↓
CSI / Hawthorn River — Loan Origination System (LOS)
        ↓
TruStage — Loan Document Software
        ↓
SIGNiX — Electronic Signature & Authentication
```

**Implication:** Volume growth cannot rely solely on TruStage's sales motion. SIGNiX must build a direct reason for FIs to call us and direct relationships that operate alongside, not against, the TruStage relationship.

---

## 4. Key Decisions Made

| Date | Decision | Source |
|------|----------|--------|
| April 2026 | SIGNiX is **cleared to contact TruStage end customers (FIs) directly** | CEO, leadership meeting |
| April 2026 | CEO wants to know **% of existing transactions that include authentications** | CEO, leadership meeting — pending CTO data |
| April 2026 | CEO wants a **full opportunity map** beyond LOS workflows | CEO, leadership meeting |
| April 2026 | **Info-Tech Research Group** analyst briefing secured at no cost | Chris, discovery call |
| March 2026 | **Mike's fraud insights email** launched in HubSpot with A/B testing | Mike + Chris |

---

## 5. Open Questions & Owner

| Question | Owner | Status |
|----------|-------|--------|
| What % of SIGNiX transactions (all accounts) include authentications? | CTO | Pending data request |
| Which loan document types are being signed via SIGNiX in TruStage accounts? | CTO / TruStage | Unknown — needs telemetry or TruStage report |
| What does the TruStage contract allow in terms of FI data sharing for campaigns? | CRO / Legal | Confirm before using account-level data in targeting |
| Is a joint QBR or business review scheduled with TruStage? | CRO | Confirm timing; Chris should be included or briefed |

---

## 6. Active Initiatives

### Marketing Plan (full detail)
The full three-track marketing plan — authentication activation, Flex API partner strategy, and omnichannel demand generation — is documented in **[SIGNIX-MARKETING-PLAN-2026.md](SIGNIX-MARKETING-PLAN-2026.md)**. The sections below summarize active initiatives; refer to the plan for complete tactic tables, keyword buckets, KPIs, and budget summary.

---

### 6A. Mike's Fraud Insights Email Campaign
- **Goal:** Drive TruStage FI contacts to request a workflow review conversation with Mike (Client Success Manager).
- **Channel:** HubSpot email; A/B tested for length and structure.
- **Audience:** Account admins and operational champions at TruStage-enabled FIs.
- **Variants in production:** BLEND (recommended), CONDENSED, SKIM. Template available for monthly reuse.
- **CTA:** "Review your top three transaction types with Mike."
- **Files:** `PROJECT-DOCS/06-DOCS/`
- **Next step:** Monitor opens/clicks → prioritize reply outreach from engagements.

### 6B. Google Ads — E-Signature Platform
- **Budget:** ~$3,000/month
- **Strategy:** Avoid generic head-to-head vs. DocuSign/Adobe on broad terms (too expensive). Compete on specificity.

**Keyword buckets:**

| Bucket | Budget allocation | Example terms |
|--------|------------------|---------------|
| Competitor displacement | ~$800–1,000 | `docusign alternative for banks`, `adobe sign alternative compliance` |
| Industry / use-case specific | ~$900–1,100 | `electronic signature for banks`, `loan document electronic signature`, `e-signature for credit unions` |
| Authentication & security angle | ~$500–700 | `e-signature with identity verification`, `electronic signature fraud prevention`, `signer identity verification software` |
| RON adjacency | ~$300–400 | `remote online notary and e-signature`, `RON platform with electronic signature` |

**Ad message principles:**
- Lead with PKI, authentication, regulated industries — not generic "easy signing."
- Competitor displacement: lead with price or compliance specificity.
- Each bucket should land on a **dedicated or tailored landing page**, not the generic homepage.

### 6C. Info-Tech Research Group — Analyst Relations
- **Status:** No-cost analyst briefing path confirmed.
- **Value:** Visibility with IT buyer community (IT directors, VPs at mid-market companies, including FIs).
- **Next step:** Schedule analyst briefing; prepare SIGNiX product narrative focused on regulated industries and authentication differentiation.
- **Competitive intelligence opportunity:** Ask Info-Tech what their analysts are currently recommending for e-sign to FI IT buyers.

---

## 7. "Beyond LOS" Opportunity Map (in progress)

The CEO has directed a review of the full transaction opportunity across all SIGNiX customer accounts — not just loan workflows. Initial mapping of FI workflows where SIGNiX e-sign and/or authentication apply:

| Workflow | E-sign opportunity | Auth opportunity | Priority signal |
|---|---|---|---|
| New account / membership opening | Account agreements, disclosures | Identity verification at enrollment | High |
| Wire transfer authorization | Standing wire instructions | Step-up auth at time of request | High |
| Beneficiary changes | IRA, 401k, insurance designations | Strong auth to prevent account takeover | High |
| Power of attorney / trust docs | Estate documents | High-assurance identity | Medium |
| HR / employee onboarding | Offer letters, policy acknowledgments | Credential issuance | Medium |
| Vendor / third-party contracts | Operational agreements | Counterparty auth | Medium |
| ACH / payment authorizations | Recurring payment setups | Auth at enrollment or change | Medium |
| Regulatory / compliance docs | BSA, audit acknowledgments | Staff identity logs | Low–Medium |

**Validation path:** Direct discovery calls with FI contacts (enabled by CEO clearance). Use Mike's email engagement as the warm-in.

---

## 8. Discovery Call Guide (for Mike and Chris)

Use for any direct FI conversation following the email campaign or warm outreach.

**Three core questions:**
1. "Walk me through how you currently use electronic signatures in your loan process — start to finish."
2. "Outside of loans, where in your institution are documents still being printed, signed by hand, or emailed as PDFs?"
3. "Where do you have the most anxiety about a signer being who they say they are?"

**Target:** 10–15 conversations → builds credible workflow opportunity map by institution type.

---

## 9. Positioning Principles

- **Regulated industry focus:** Financial services, banking, credit unions, lending — not generic horizontal.
- **Authentication differentiation:** PKI-based digital signatures + configurable signer authentication = genuinely different from DocuSign/Adobe's default click-to-sign.
- **Partner-first language:** "Helping you get more value from what you already have" — not "you're doing it wrong."
- **Fear opens doors; clarity closes them:** Fraud education (Mike's email) starts the conversation; workflow specificity and audit-trail proof convert it.
- **RON as a wedge:** Proven lead-gen channel; use it to introduce e-sign and authentication to net-new prospects.

---

## 10. Potential Future Initiatives (not committed)

| Idea | Description | Prerequisite |
|------|-------------|-------------|
| Authentication self-assessment tool | Lightweight guided survey → outputs prioritized list of riskiest loan flows for the FI | Product/legal alignment; CEO appetite confirmed as "interesting" |
| Workflow opportunity map (sales asset) | Structured view of e-sign + auth use cases by institution type and loan category | 10–15 discovery calls completed |
| Joint campaign with TruStage | Co-branded outreach to TruStage FI customers on authentication benefits | QBR / TruStage partnership conversation |
| Side-by-side signing demo (synthetic) | Show audit log difference: email-only vs step-up authentication | Product + legal review; partner alignment |

---

*Last updated: April 1, 2026. Update this document as decisions are confirmed, data is received, and campaigns produce results.*

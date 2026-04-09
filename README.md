# SIGNiX AI Marketing — Chris Teague (AI Summit 2026 Q2)

This repo shows what AI-assisted marketing looks like in practice.

Everything here was built using **[Cursor](https://cursor.com)** and a custom AI workflow over roughly three weeks. The work spans campaign strategy, paid media, email, and sales collateral.

---

## What's in here

### Sales Collateral (ABS / CoPilot)
Two one-pagers built for our sales rep covering Banks and Credit Unions. Corrected April 9, 2026.

- [SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT.pdf](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT.pdf) — Partner overview one-pager
- [SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT.pdf](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT.pdf) — Authentication one-pager

### Marketing Dashboard
A live HTML dashboard that pulls from Google Ads, HubSpot, and LinkedIn exports and renders all three in one view. Open in any browser — no server needed.

- [SIGNiX_Dashboard_April2026.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_Dashboard_April2026.html)

**What it shows:**
- Google Ads: spend, clicks, conversions, CPC, cost-per-lead, campaign comparison, keyword performance, off-hours spend analysis
- HubSpot: lead response time per rep (color-coded by urgency)
- LinkedIn: impressions, engagement rate, post-by-post performance

### Campaign Measurement Doc
A 90-day measurement framework with ROI targets, decision rules, and phase-by-phase benchmarks.

- [SIGNiX_CampaignMeasurement_April2026.docx](PROJECT-DOCS/DELIVERABLES/SIGNiX_CampaignMeasurement_April2026.docx)

### Mike's Fraud Insights Email — Email 1 and Email 2
Operator-voice email series sent to 70 TruStage Financial Institution customers.

- [Mike-March-2026-Fraud-Insights-Email1-SHORT.pdf](PROJECT-DOCS/DELIVERABLES/Mike-March-2026-Fraud-Insights-Email1-SHORT.pdf) — Email 1 (March 2026)
- [Mike-April-2026-Fraud-Email2-Outlook.pdf](PROJECT-DOCS/DELIVERABLES/Mike-April-2026-Fraud-Email2-Outlook.pdf) — Email 2 (April 2026)

**Email 1 results (sent March 2026):**
- Open rate: 19.7% (industry avg: 14%)
- CTR: 15.38% (industry avg: 2–5%)
- +2 new contacts added within 7 days

---

## How it was built

All deliverables were generated using Python build scripts in `PROJECT-DOCS/build-scripts/`. Each script produces a `.docx`, `.pptx`, `.xlsx`, or `.html` file using SIGNiX brand tokens. The dashboard script reads CSV exports from Google Ads and LinkedIn directly — no API keys required.

The AI workflow (Cursor + custom rules) handled strategy, copywriting, data analysis, and document generation. Chris directed, reviewed, and refined everything.

---

## About SIGNiX

[SIGNiX](https://www.signix.com) provides PKI-based digital signatures, e-sign, and authentication via the Flex API. Primary markets: financial services, lending, wealth management, and Remote Online Notary (RON).

---

*Prepared for AI Summit 2026 Q2 Show-and-Tell | Chris Teague, Head of Growth and Marketing*

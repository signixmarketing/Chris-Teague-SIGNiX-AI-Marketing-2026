# SIGNiX AI Marketing — Chris Teague (AI Summit 2026 Q2)

This repo shows what AI-assisted marketing looks like in practice.

Everything here was built using **[Cursor](https://cursor.com)** and a custom AI workflow. The work spans campaign strategy, paid media, email, sales collateral, dashboards, and competitive demo tools.

---

## What's in here

### PDF Signature Inspector — Sales Demo Tool
An interactive browser-based tool that compares what lives inside a SIGNiX-signed document versus a standard e-signature document at the PKI level. Built for sales reps to use in front of prospects. No server, no login — open the file in Chrome.

- [SIGNiX_PDF_Inspector.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_PDF_Inspector.html)
- Build script: [build_signix_pdf_inspector.py](PROJECT-DOCS/build-scripts/build_signix_pdf_inspector.py)

**What it shows:**
- Certificate chains: GlobalSign AATL (SIGNiX, signer-level) vs. DigiCert DS Technical Operations (standard server export seal)
- ByteRange tamper coverage — how much of the PDF is cryptographically sealed
- Signer metadata embedded in the SIGNiX document: IP address, device, transaction ID, signing time
- Evidence Layer 2: SIGNiX PKI-signed audit trail vs. standard Certificate of Completion (no PKI signatures)
- Drag-and-drop to inspect any PDF live

**Seven audience scenarios (one-click switch):**
Elder Financial Protection, Banks and Credit Unions, Wealth Management / RIA, Government / County, Healthcare, Legal, Debt Buying / Affidavit.

**The core argument:** A SIGNiX-signed document proves who signed it — from the file itself, without calling SIGNiX. Standard server export seals prove the platform sent it. They do not prove who signed.

---

### MyDox Interactive Demo v2 — Sales Demo Tool
A 23-screen offline HTML demo simulating the full MyDox signing workflow including signature tagging and the complete ID Verify authentication flow. Built for Aspen, Pem, and ABS partner reps. No internet required — open the file in Chrome.

- [SIGNiX_MyDox_Demo.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_MyDox_Demo.html)
- Build script: [build_mydox_demo_v2.py](PROJECT-DOCS/build-scripts/build_mydox_demo_v2.py)

**What it shows:**
- Full transaction creation flow: Dashboard → Add Signer → Documents → **Signature Tagging** → Send → Signer Email → Legal Consent → ID Verify → **Full Persona Flow** → **ID Passed** → **Create Signature** → Document View → Signature Placed → Confirmation
- **Quick View / Full Flow toggle** in the control bar. Quick View (14 steps, default) is built for rep-led demos. Full Flow (23 steps) shows every step of the Persona ID Verify sub-flow — built for ABS partner reps doing self-sufficient customer demos.
- **Signature Tagging screen:** Rendered Signatures wizard tab with document, draggable field toolbar (Signature, Initial, Date, Text, Checkbox, Acknowledge), and live-placed fields.
- **Full Persona ID Verify flow (9 sub-screens):** Getting Started → Country → ID Type → Expiry Date → Front of ID → Back of ID → Liveness Check → Face Scan → Verification Complete. Persona-branded UI rendered in HTML.
- **Create Your Signature:** Password creation and four signature style options — signer name carries through all previews.
- **Confirmation screen with QR code:** Inline QR code links to Aspen's calendar. Contact name, phone, and email appear beside it. Update the calendar URL in the build script variable to change the link.
- Authentication dropdown with ID Verify, KBA, 2FA, and Password options — ID Verify triggers a "highest assurance" badge
- "I Am The Signer" checkbox auto-fills presenter info in one click
- Signer name and email carry through all 23 screens dynamically
- Speaker notes panel (toggle on/off) with guidance for Aspen (sales), Pem (executive), and ABS reps (partner)
- All decorative UI buttons are non-hoverable — nothing breaks mid-demo
- Fully self-contained, works offline on phone, tablet, or laptop

**The core argument:** Before anyone signs, SIGNiX verifies who they are. The signature is PKI-embedded and cryptographically tied to the document. You own and control your documents.

---

### PDF Signature Inspector One-Pager
Print-ready one-pager explaining the PDF Signature Inspector tool. Focuses on signer-level PKI differentiation. Contact: Aspen Arias.

- [SIGNiX-PDFInspector-OnePager-Aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX-PDFInspector-OnePager-Aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX-PDFInspector-OnePager-Aspen.pdf)
- Build script: [build_pdf_inspector_onepager.py](PROJECT-DOCS/build-scripts/build_pdf_inspector_onepager.py)

---

### Self-Proving Signatures One-Pager (DocuSign Comparison)
Print-ready one-pager comparing SIGNiX's PKI-based signature technology to DocuSign's server export seal. Side-by-side visual from the Inspector tool. Core message: you don't need SIGNiX to prove your document. If we ever go out of business, your document still proves itself. Contact: Aspen Arias.

- [SIGNiX-SelfProving-OnePager-Aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX-SelfProving-OnePager-Aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX-SelfProving-OnePager-Aspen.pdf)
- Build script: [build_self_proving_onepager.py](PROJECT-DOCS/build-scripts/build_self_proving_onepager.py)

---

### Marketing Dashboard
A live HTML dashboard combining Google Ads, HubSpot lead response, LinkedIn performance, and sales pipeline in one view. Open in any browser — no server needed.

- [SIGNiX_Dashboard_April2026.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_Dashboard_April2026.html)
- Build script: [build_signix_dashboard.py](PROJECT-DOCS/build-scripts/build_signix_dashboard.py)

**What it shows:**
- Google Ads: spend, clicks, conversions, CPC, cost-per-lead, campaign comparison, keyword performance, off-hours spend analysis
- HubSpot: lead response time per rep (color-coded by urgency)
- LinkedIn: impressions, engagement rate, post-by-post performance
- Sales pipeline: funnel from clicks to pipeline (pending HubSpot export to populate)

---

### TruStage Portfolio Dashboards
Two dashboards built to support the TruStage depth-play strategy: activate authentication on existing accounts and quantify the expansion opportunity.

- [SIGNiX_TruStage_Dashboard_April2026.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_TruStage_Dashboard_April2026.html) — 39-account portfolio, transaction volume, auth rates, zero-auth opportunity map
- [SIGNiX_TruStage_Expansion_Model_April2026.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_TruStage_Expansion_Model_April2026.html) — share of wallet model: 28% current, 72% addressable gap across 5 workflow categories

---

### One-Pagers — Signer-Level PKI Positioning (v2)
Two headline versions for team feedback. Both updated with the PKI distinction (server export vs. signer-level), broadened subhead for any regulated institution, and Aspen's contact details filled in. PDFs generated via Chrome headless for accurate rendering.

- [SIGNiX-OnePager-VersionA-Aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX-OnePager-VersionA-Aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX-OnePager-VersionA-Aspen.pdf) — "When the signature gets challenged, SIGNiX holds up."
- [SIGNiX-OnePager-VersionB-Aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX-OnePager-VersionB-Aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX-OnePager-VersionB-Aspen.pdf) — "When authority is questioned, SIGNiX answers." (recommended)
- Build script: [build_signix_onepager_v2.py](PROJECT-DOCS/build-scripts/build_signix_onepager_v2.py)

---

### CCISDA Conference Package
Full conference marketing package for the California County Information Services Directors Association (CCISDA) 2026. Audience: county IT directors and CIOs. Attendees: Aspen Arias and Pem. One-pager replaced by the v2 PKI positioning pieces above.

- [CCISDA-2026-Lead-Capture.html](PROJECT-DOCS/DELIVERABLES/CCISDA-2026-Lead-Capture.html) — Mobile-friendly booth lead capture form. Generates a HubSpot-ready lead card on tap.
- [CCISDA-Email-1-PKI-Fear.html](PROJECT-DOCS/DELIVERABLES/CCISDA-Email-1-PKI-Fear.html) — Day 1: PKI / AI fear hook
- [CCISDA-Email-2-Data-Custody.html](PROJECT-DOCS/DELIVERABLES/CCISDA-Email-2-Data-Custody.html) — Day 4: No data custody
- [CCISDA-Email-3-LA-County-Proof.html](PROJECT-DOCS/DELIVERABLES/CCISDA-Email-3-LA-County-Proof.html) — Day 9: Social proof
- [CCISDA-Email-4-Calendar-Ask.html](PROJECT-DOCS/DELIVERABLES/CCISDA-Email-4-Calendar-Ask.html) — Day 14: Direct calendar ask

---

### Email Campaigns

**Mike's Fraud Insights — TruStage Drip Sequence**
Operator-voice email series sent to TruStage Financial Institution customers. Designed to drive authentication activation conversations with Mike (CSM).

- [Mike-March-2026-Finalized-Fraud-Email-1.html](PROJECT-DOCS/DELIVERABLES/Mike-March-2026-Finalized-Fraud-Email-1.html) — Email 1 (March 2026): 19.7% open rate, 15.38% CTR
- [Mike-April-2026-Fraud-Email-2.html](PROJECT-DOCS/DELIVERABLES/Mike-April-2026-Fraud-Email-2.html) — Email 2: Loan dispute scenario
- [Mike-April-2026-Fraud-Email-3.html](PROJECT-DOCS/DELIVERABLES/Mike-April-2026-Fraud-Email-3.html) — Email 3: Social proof (Margaret Glover, Atlanta Postal Credit Union)

**ACS eNotary Auto-Response Sequence**
Four-email automated sequence for eNotary / RON platform leads.

- [eNotary-Email-1-Confirmation.html](PROJECT-DOCS/DELIVERABLES/eNotary-Email-1-Confirmation.html) — Immediate: confirmation + product overview
- [eNotary-Email-2-PKI-Difference.html](PROJECT-DOCS/DELIVERABLES/eNotary-Email-2-PKI-Difference.html) — Day 3: Server export vs. signer-level PKI
- [eNotary-Email-3-Social-Proof.html](PROJECT-DOCS/DELIVERABLES/eNotary-Email-3-Social-Proof.html) — Day 7: Margaret Glover quote
- [eNotary-Email-4-Final-Ask.html](PROJECT-DOCS/DELIVERABLES/eNotary-Email-4-Final-Ask.html) — Day 14: Direct calendar ask
- Build script: [build_enotary_emails.py](PROJECT-DOCS/build-scripts/build_enotary_emails.py)

---

### LinkedIn Content
Two posts drafted for the SIGNiX LinkedIn page, paired with the Mike fraud email sequence.

- [SIGNiX-LinkedIn-CreditUnion-SocialProof-April2026.md](PROJECT-DOCS/DELIVERABLES/SIGNiX-LinkedIn-CreditUnion-SocialProof-April2026.md) — Credit union social proof post (Wednesday Apr 16)
- [SIGNiX-LinkedIn-WealthMgmt-RIA-April2026.md](PROJECT-DOCS/DELIVERABLES/SIGNiX-LinkedIn-WealthMgmt-RIA-April2026.md) — Wealth management / RIA compliance post (Thursday Apr 17)
- [SIGNiX-LinkedIn-PullQuote-CreditUnion-April2026.png](PROJECT-DOCS/DELIVERABLES/SIGNiX-LinkedIn-PullQuote-CreditUnion-April2026.png) — Pull quote graphic

---

### Sales Collateral (ABS / CoPilot)
Two one-pagers for the American Bank Systems CoPilot integration. Rebuilt with Chrome headless. Contact info updated to Aspen's direct phone, email, and calendar link. "Draft" label removed.

- [SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.pdf) — Partner overview (workflow, trust, capabilities)
- [SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html) / [PDF](PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.pdf) — Authentication focus (ID Verify, KBA, OTP, risk tiers)
- Build script: [build_abs_onepagers.py](PROJECT-DOCS/build-scripts/build_abs_onepagers.py)

---

### Meeting Talking Points
Internal prep doc for stakeholder meetings.

- [SIGNiX_MeetingTalkingPoints_4.13.26.docx](PROJECT-DOCS/DELIVERABLES/SIGNiX_MeetingTalkingPoints_4.13.26.docx)
- Build script: [build_signix_meeting_talking_points_4.13.26.py](PROJECT-DOCS/build-scripts/build_signix_meeting_talking_points_4.13.26.py)

---

### Campaign Measurement Doc
A 90-day measurement framework with ROI targets, decision rules, and phase-by-phase benchmarks.

- [SIGNiX_CampaignMeasurement_April2026.docx](PROJECT-DOCS/DELIVERABLES/SIGNiX_CampaignMeasurement_April2026.docx)

---

## How it was built

All deliverables were generated using Python build scripts in `PROJECT-DOCS/build-scripts/`. Each script produces a `.docx`, `.pptx`, `.xlsx`, `.html`, or `.pdf` file using SIGNiX brand tokens. The dashboard scripts read CSV exports from Google Ads and LinkedIn directly — no API keys required. PDFs for designed collateral (one-pagers, ABS brochures) are generated via Chrome headless for accurate CSS rendering.

The AI workflow (Cursor + custom rules) handled strategy, copywriting, data analysis, and document generation. Chris directed, reviewed, and refined everything.

---

## About SIGNiX

[SIGNiX](https://www.signix.com) provides PKI-based digital signatures, e-sign, and authentication via the Flex API. Primary markets: financial services, lending, wealth management, and Remote Online Notary (RON).

---

*Prepared for AI Summit 2026 Q2 Show-and-Tell | Chris Teague, Head of Growth and Marketing*

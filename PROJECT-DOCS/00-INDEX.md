# SIGNiX Marketing Toolkit — Document Index

This project is a strategy, content, and reporting toolkit for SIGNiX growth and marketing. Everything here supports Chris Teague's work as Head of Growth and Marketing.

For session context and active initiatives, start with **[BRIEFING.md](BRIEFING.md)**.

---

## Navigation

| Section | What's there |
|---------|-------------|
| [Strategy docs](#strategy-and-planning) | Marketing framework, paid media plan, positioning, market research, growth strategy |
| [Deliverables](#deliverables) | PDFs, DOCX, PPTX, XLSX, HTML — ready to use or share |
| [Build scripts](#build-scripts) | Python scripts that generate every deliverable |
| [Reference and setup](#reference-and-setup) | Design guidelines, writing voice, wkhtmltopdf, SIGNiX API |
| [Demos](#demos) | n8n lead routing demo |
| [Archive](#archive) | Older files kept for reference |

---

## Strategy and Planning

| File | Description |
|------|-------------|
| **[BRIEFING.md](BRIEFING.md)** | **Living session briefing — active initiatives, decisions log, open questions. Read this first every session.** |
| [SIGNIX-MARKETING-FRAMEWORK.md](SIGNIX-MARKETING-FRAMEWORK.md) | Source of truth for all campaigns — 6Bs applied to SIGNiX: brand, business category, five target segments, belief changes, behaviors, benchmarks, competitive landscape |
| [SIGNIX-MARKETING-PLAN-2026.md](SIGNIX-MARKETING-PLAN-2026.md) | Executive marketing plan — three growth tracks (authentication activation, Flex API partners, omnichannel), keyword strategy, KPIs, budget summary |
| [SIGNIX-PAID-MEDIA-PLAN-2026.md](SIGNIX-PAID-MEDIA-PLAN-2026.md) | Full paid media plan (Rev 3, April 6 2026) — budget reallocation rationale, Google keyword buckets, LinkedIn audiences, landing page strategy, 90-day launch plan |
| [SIGNIX-PAID-MEDIA-EXEC-SUMMARY.md](SIGNIX-PAID-MEDIA-EXEC-SUMMARY.md) | One-page executive summary — current vs. proposed state, budget, target audiences, top keywords, measurement |
| [SIGNIX-GROWTH-STRATEGY.md](SIGNIX-GROWTH-STRATEGY.md) | Living strategy doc — business problem, growth levers (depth + width), active initiatives, discovery call guide, opportunity map |
| [SIGNIX-POSITIONING-STRATEGY.md](SIGNIX-POSITIONING-STRATEGY.md) | Multi-sector positioning — financial services, healthcare, lending; why security messaging failed; partnership-first angle; competitive positioning |
| [SIGNIX-MARKET-RESEARCH-BUYER-JOURNEY.md](SIGNIX-MARKET-RESEARCH-BUYER-JOURNEY.md) | Market research and buyer journey — regulatory landscape, 4 buyer personas, 3 journey maps, messaging framework, keyword buckets |
| [SIGNIX-TRUSTAGE-CSM-BRIEF.md](SIGNIX-TRUSTAGE-CSM-BRIEF.md) | TruStage email briefing and CSM game plan — three asks, three-action plan, suggested reply, strategic note for CEO |
| [GOOGLE-ADS-SETUP-GUIDE.md](GOOGLE-ADS-SETUP-GUIDE.md) | Step-by-step Google Ads campaign setup guide — navigation tips, bidding strategy rationale, settings to fix post-launch, common pitfalls |

---

## Deliverables

### Paid Media and Campaign Documents

| File | Description |
|------|-------------|
| **[SIGNiX_PaidMedia_4.6.26.docx](SIGNiX_PaidMedia_4.6.26.docx)** | Paid media plan Word doc — Rev 3, April 6 2026. Updated keyword list, Legal/Debt Collection replaces Mortgage |
| **[SIGNiX_PaidMedia_4.6.26.pptx](SIGNiX_PaidMedia_4.6.26.pptx)** | Paid media slides — Rev 3, 6 slides, ready to present |
| [SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx](SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx) | CEO-trimmed version — simplified slide 4, 3 headline KPIs on slide 5 |
| [SIGNIX-PAID-MEDIA-SLIDES.html](SIGNIX-PAID-MEDIA-SLIDES.html) | HTML presentation deck — keyboard/click navigation, PDF-exportable |
| **[SIGNiX_Keyword_Master_4.6.26.xlsx](SIGNiX_Keyword_Master_4.6.26.xlsx)** | Keyword master Excel — 60+ keywords, color-coded status, search volume, CPC, budget allocation, negative keywords |
| **[SIGNiX_CampaignMeasurement_April2026.docx](SIGNiX_CampaignMeasurement_April2026.docx)** | 90-day measurement framework — ROI targets, decision rules, phase-by-phase benchmarks |
| **[SIGNiX_GoogleAds_4.9.26.docx](SIGNiX_GoogleAds_4.9.26.docx)** | Google Ads copy doc — full ad copy for 5 campaigns (Compliance/Legal, RON Institutional, Healthcare/Consent, Wealth Mgmt, Auth/PKI) |
| **[SIGNiX_Dashboard_April2026.html](SIGNiX_Dashboard_April2026.html)** | Marketing dashboard — Google Ads + HubSpot + LinkedIn in one HTML file, open in any browser |

### Sales and ABM Documents

| File | Description |
|------|-------------|
| **[SIGNiX_MarketingPlan_4.7.26.pptx](SIGNiX_MarketingPlan_4.7.26.pptx)** | Leadership marketing plan deck — 6 slides, two-strategy framework, 5 segments, belief changes, active initiatives, 60-day benchmarks |
| [SIGNiX_SlideC_Audiences.pptx](SIGNiX_SlideC_Audiences.pptx) | Standalone audience hub-and-spoke slide — Option C |
| **[SIGNiX_ABM_Scorecard.docx](SIGNiX_ABM_Scorecard.docx)** | ABM scorecard — 35-account landscape tracker with weekly activity columns |
| **[SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx](SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx)** | CFO one-pager — answers "will this generate enough leads?" with keyword data, volume math, ROI frame |
| **[SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx](SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx)** | CRO one-pager — addresses lead volume and team activity concerns, 90-day projections, ROI math, 24-hr response ask |

---

## Deliverables folder (DELIVERABLES/)

All collateral, email files, and print-ready PDFs live in **[DELIVERABLES/](DELIVERABLES/)**.

### ABS / CoPilot Partner Collateral

| File | Description |
|------|-------------|
| **[DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html](DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html)** | Source HTML — ABS CoPilot partner overview one-pager. Edit to regenerate PDF. |
| **[DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT.pdf](DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT.pdf)** | PDF — partner overview one-pager. Corrected April 9 2026. |
| **[DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html](DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html)** | Source HTML — authentication one-pager. Edit to regenerate PDF. |
| **[DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT.pdf](DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT.pdf)** | PDF — authentication one-pager. Corrected April 9 2026. |
| [DELIVERABLES/aspen-contact.png](DELIVERABLES/aspen-contact.png) | Aspen headshot used in the CTA section of both one-pagers. |

### Mike's Fraud Insights Email Series

| File | Description |
|------|-------------|
| [DELIVERABLES/PROJECT-MIKE-MARKET-INSIGHTS-EMAIL.md](DELIVERABLES/PROJECT-MIKE-MARKET-INSIGHTS-EMAIL.md) | Project brief — persona, pattern, source mapping |
| **[DELIVERABLES/Mike-March-2026-Finalized-Fraud-Email-1.html](DELIVERABLES/Mike-March-2026-Finalized-Fraud-Email-1.html)** | Email 1 — final HTML send version |
| [DELIVERABLES/Mike-March-2026-Fraud-Insights-Email1-SHORT.pdf](DELIVERABLES/Mike-March-2026-Fraud-Insights-Email1-SHORT.pdf) | Email 1 — PDF version |
| **[DELIVERABLES/Mike-April-2026-Fraud-Email-2.html](DELIVERABLES/Mike-April-2026-Fraud-Email-2.html)** | Email 2 — final HTML send version |
| [DELIVERABLES/Mike-April-2026-Fraud-Email2-Outlook.pdf](DELIVERABLES/Mike-April-2026-Fraud-Email2-Outlook.pdf) | Email 2 — PDF version |
| [DELIVERABLES/mike-fraud-insights-email-TEMPLATE.html](DELIVERABLES/mike-fraud-insights-email-TEMPLATE.html) | Reusable template with «placeholders» for future emails |
| [DELIVERABLES/mike-march-2026-fraud-insights-email.html](DELIVERABLES/mike-march-2026-fraud-insights-email.html) | Email 1 variant — original |
| [DELIVERABLES/mike-march-2026-fraud-insights-email-SKIM.html](DELIVERABLES/mike-march-2026-fraud-insights-email-SKIM.html) | Email 1 variant — skim-optimized |
| [DELIVERABLES/mike-march-2026-fraud-insights-email-BLEND.html](DELIVERABLES/mike-march-2026-fraud-insights-email-BLEND.html) | Email 1 variant — blend (v1 look + skim structure) |
| [DELIVERABLES/mike-march-2026-fraud-insights-email-CONDENSED.html](DELIVERABLES/mike-march-2026-fraud-insights-email-CONDENSED.html) | Email 1 variant — condensed |

### LinkedIn and Social

| File | Description |
|------|-------------|
| [DELIVERABLES/SIGNiX-LinkedIn-DimeBank-April2026.md](DELIVERABLES/SIGNiX-LinkedIn-DimeBank-April2026.md) | LinkedIn post draft — Dime Bank angle, April 2026 |
| [DELIVERABLES/SIGNiX-LinkedIn-PullQuote-April2026.png](DELIVERABLES/SIGNiX-LinkedIn-PullQuote-April2026.png) | Pull quote graphic for LinkedIn |

### Executive Greeting Card

| File | Description |
|------|-------------|
| [DELIVERABLES/SIGNiX-EXECUTIVE-GREETING-CARD-VISTAPRINT/](DELIVERABLES/SIGNiX-EXECUTIVE-GREETING-CARD-VISTAPRINT/) | Print-safe card files for Vistaprint — inside and outside spreads, README with print specs |

---

## Build Scripts

All scripts live in **[build-scripts/](build-scripts/)**. Each generates a branded deliverable using SIGNiX brand tokens.

| Script | Output |
|--------|--------|
| [build-scripts/build_signix_dashboard.py](build-scripts/build_signix_dashboard.py) | `SIGNiX_Dashboard_April2026.html` — reads CSV exports from Google Ads and LinkedIn |
| [build-scripts/build_signix_keyword_master_xlsx.py](build-scripts/build_signix_keyword_master_xlsx.py) | `SIGNiX_Keyword_Master_4.6.26.xlsx` — keyword master with budget allocation |
| [build-scripts/build_signix_google_ads_docx.py](build-scripts/build_signix_google_ads_docx.py) | `SIGNiX_GoogleAds_4.9.26.docx` — Google Ads copy for all 5 campaigns |
| [build-scripts/build_signix_marketing_plan_pptx.py](build-scripts/build_signix_marketing_plan_pptx.py) | `SIGNiX_MarketingPlan_4.7.26.pptx` — leadership marketing plan deck |
| [build-scripts/build_signix_paid_media_4_6_26_pptx.py](build-scripts/build_signix_paid_media_4_6_26_pptx.py) | `SIGNiX_PaidMedia_4.6.26.pptx` — paid media slides |
| [build-scripts/build_signix_paid_media_4_6_26_docx.py](build-scripts/build_signix_paid_media_4_6_26_docx.py) | `SIGNiX_PaidMedia_4.6.26.docx` — paid media Word doc |
| [build-scripts/build_signix_measurement_timeline_docx.py](build-scripts/build_signix_measurement_timeline_docx.py) | `SIGNiX_CampaignMeasurement_April2026.docx` — 90-day measurement framework |
| [build-scripts/build_signix_abm_scorecard.py](build-scripts/build_signix_abm_scorecard.py) | `SIGNiX_ABM_Scorecard.docx` — 35-account ABM tracker |
| [build-scripts/build_signix_cfo_brief_4_6_26.py](build-scripts/build_signix_cfo_brief_4_6_26.py) | `SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx` — CFO one-pager |
| [build-scripts/build_signix_cro_brief_4_6_26.py](build-scripts/build_signix_cro_brief_4_6_26.py) | `SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx` — CRO one-pager |
| [build-scripts/build_signix_docx.py](build-scripts/build_signix_docx.py) | Base template for new Word documents |
| [build-scripts/build_signix_pptx.py](build-scripts/build_signix_pptx.py) | Base template for new PowerPoint decks |
| [build-scripts/build_signix_slide_c.py](build-scripts/build_signix_slide_c.py) | `SIGNiX_SlideC_Audiences.pptx` — standalone audience hub slide |
| [build-scripts/update_slide5_keyword_analysis.py](build-scripts/update_slide5_keyword_analysis.py) | Updates keyword analysis slide in the paid media deck |
| [build-scripts/README.md](build-scripts/README.md) | How to use the build scripts — helper functions, brand tokens, usage instructions |

---

## Reference and Setup

| File | Description |
|------|-------------|
| [DESIGN-GUIDELINES.md](DESIGN-GUIDELINES.md) | SIGNiX brand tokens — color palette, font stack, type scale, spacing, logo, design principles |
| [SIGNIX-WRITING-VOICE.md](SIGNIX-WRITING-VOICE.md) | SIGNiX writing voice — plain language rules, human tone, words to avoid |
| [COLLABORATION-AND-FEEDBACK.md](COLLABORATION-AND-FEEDBACK.md) | Working agreement — star feedback, partner-first messaging, deliverable standards *(local only — not pushed to GitHub)* |
| [05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md) | wkhtmltopdf setup — how to install and use for HTML-to-PDF generation |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) | HTML-to-PDF reference — wkhtmltopdf, pdfkit options |
| [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) | SIGNiX Flex API reference — integration patterns, authentication types, API structure |

---

## Demos

| Path | Description |
|------|-------------|
| [../demos/n8n-notary-lead-routing/README.md](../demos/n8n-notary-lead-routing/README.md) | SIGNiX-style lead form → n8n webhook; routes low/high notary volume and sends email alerts |

---

## Archive

Older files kept for reference — not part of active work.

| Path | What it contains |
|------|-----------------|
| [ARCHIVE/README.md](ARCHIVE/README.md) | Index of archived files and why each was kept |
| [ARCHIVE/20-APPROACH.md](ARCHIVE/20-APPROACH.md) | AI-assisted document-driven development methodology — useful template for extending this project |
| [ARCHIVE/GENERAL-KNOWLEDGE/](ARCHIVE/GENERAL-KNOWLEDGE/) | App foundation, document-centric patterns, file/media handling — reference for future toolkit features |
| [ARCHIVE/build_signix_pptx_ceo.py](ARCHIVE/build_signix_pptx_ceo.py) | CEO-trimmed paid media slide script — reference for CEO slide formatting |

---

*Last updated: April 9, 2026 — project restructured from lease origination app to SIGNiX Marketing Toolkit*

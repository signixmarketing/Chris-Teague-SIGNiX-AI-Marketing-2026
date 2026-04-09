# Project: Mike’s market insights email (fraud & identity)

Partner marketing asset for **SIGNiX** integration partners (e.g. **TruStage**, **ABS**). Goal: position **Mike** (Client Success Manager) as a credible voice on fraud and identity trends, humanize SIGNiX, and drive **authentication** adoption without feeling like a heavy product blast.

Primary audience: **account admins and operational champions** (not always the economic buyer). Content should be easy to forward internally (“here’s why we should tighten signer assurance”).

---

## Source document (canonical copy)

- **File:** `Mike's March Newsletter_CT_V2.docx` (Desktop `S 2026/`)
- **Title in doc:** Mike’s Monthly Market Insights: Fraud and Identity Protection, March 2026 Edition

---

## Email design pattern (agreed)

1. **Subject:** `3 fraud trends worth 6 minutes ([Month])`
2. **Opening:** Short operator voice; connect partner context (verification, consent, regulator expectations).
3. **Reading list:** Three links; **one sentence per link** in Mike’s words (why it matters for FI admins).
4. **Bridge + ask:** Translate trend → **identity at moment of consent**; offer **review of top three transaction types** for where authentication typically pays off.
5. **Optional product line:** Single link to SIGNiX (e.g. Flex API capabilities) for internal sharing.
6. **Footer:** Light disclaimer (not legal advice), opt-out of tone via reply.

Branding tokens match SIGNiX collateral: green `#6da34a`, ink `#2e3440`, body `#545454`, rules `#d8dee9`, panels `#eceff4`, canvas `#f8fafb`. Logo: HubSpot-hosted PNG from signix.com (see HTML template).

---

## March 2026: three points from the Word doc → web sources

Mike’s **“SIGNiX Perspective”** bullets in the doc were mapped to **three curated links**. The doc’s **“Sources & References”** list named: **Entrust, Experian, Verizon DBIR, FTC, SentiLink, Sumsub**, and leading research firms. The March email uses **Experian**, **U.S. News**, and **FTC** for a balanced, one-click reading list (no large downloads in the body).

| # | Theme (from Mike’s bullets) | Source | URL | Notes |
|---|----------------------------|--------|-----|--------|
| 1 | Layered identity verification & authentication | **Experian** | https://www.experian.com/blogs/ask-experian/identity-theft-statistics/ | Ungated Ask Experian piece summarizing FTC fraud/ID theft volumes and channels, with useful context for why **layered** controls show up in risk conversations. |
| 2 | Adaptive authentication; moving beyond SMS/email-only | **U.S. News** | https://www.usnews.com/banking/articles/with-ais-help-fraudsters-are-targeting-smaller-banks | Short banking article on **AI-enabled fraud** pressuring smaller institutions; supports the case for **step-up** and non-static channels without a long PDF. |
| 3 | Education & awareness (phishing, staff discipline) | **FTC** | https://consumer.ftc.gov/articles/how-recognize-and-avoid-phishing-scams | Practical, shareable employee-facing baseline. |

**Also cited in the Word doc** (optional follow-on sends or appendix):

| Source | Suggested URL | Role |
|--------|----------------|------|
| **Experian** (gated deep dive) | https://www.experian.com/thought-leadership/business/identity-and-fraud-report | 2025 U.S. Identity & Fraud Report (**form required** to download); good for execs who will register. |
| **Sumsub** | https://sumsub.com/blog/guides-reports/identity-fraud-report-2025-2026/ | **Identity Fraud Report 2025–2026** (large industry report / PDF-style download). Keep for deep dives; **not** linked in the customer-facing email to avoid a heavy file. |
| **Verizon** | https://www.verizon.com/business/resources/reports/dbir/ | **DBIR** hub: threat landscape, credentials, social engineering. |
| **SentiLink** | https://resources.sentilink.com/blog/building-blocks-to-improve-fraud-detection-and-enhance-modeling | Fraud detection / modeling perspective. |
| **Entrust** | https://www.entrust.com/blog | **Blog hub.** Use a current identity or verification post as needed (direct article URLs vary; automated fetches sometimes return 403, though human browsers work). |

---

## Deliverables in this repo

| File | Purpose |
|------|---------|
| `mike-march-2026-fraud-insights-email.html` | March 2026 send: copy and links filled in; inbox-tested layout. |
| `mike-march-2026-fraud-insights-email.txt` | Plain-text version for CRM “text” body or multipart email. |
| `mike-march-2026-fraud-insights-email-SKIM.html` | **Skim version:** “If you skim, start here,” Mike/SIGNiX framing, compact three reads with “Mike’s use” lines. |
| `mike-march-2026-fraud-insights-email-SKIM.txt` | Plain-text skim version; subject suggests Mike at SIGNiX. |
| `mike-march-2026-fraud-insights-email-BLEND.html` | **Blend:** v1 visual style (logo rule, gray read cards, full narrative) + skim box, byline, “Mike’s use” lines per read, IT callout. **Recommended default** for busy inboxes. |
| `mike-march-2026-fraud-insights-email-BLEND-OUTLOOK.html` | Same body as blend; HTML comment with steps for Mike to open in a browser, copy all, and paste into Outlook. |
| `mike-march-2026-fraud-insights-email-BLEND.txt` | Plain-text blend. |
| `mike-march-2026-fraud-insights-email-BLEND-from-html.pdf` | **Team PDF:** print-from-HTML export (clickable links); regenerate from updated BLEND HTML if copy changes. |
| `Mike-March-2026-Finalized-Fraud-Email-1.html` | **Final Outlook paste:** single file from `MIke's Newsletter Edits_FINAL.docx`; same BLEND layout; also copied to Desktop `Mike-Final-March-2026-Fraud-1/`. |
| `mike-march-2026-fraud-insights-email-CONDENSED.html` | **Short:** same visual system as blend, tighter copy (fewer sentences, lean skim box, one-line read blurbs). |
| `mike-march-2026-fraud-insights-email-CONDENSED.txt` | Plain-text condensed. |
| `mike-fraud-insights-email-MARCH-2026-complete.zip` | **Handoff:** all files above inside folder `mike-fraud-insights-email-MARCH-2026/` (attach from SIGNiX email). |
| `mike-fraud-insights-email-TEMPLATE.html` | Reusable shell: `«placeholders»` for future months. |

**Mike** should replace `«MIKE_EMAIL»` and `«MIKE_PHONE»` in the March files if those placeholders remain.

---

## QA before send

- Send test to **Outlook** and **Gmail**; confirm images (logo) load and links resolve.
- Spot-check links in an incognito window (corporate proxies sometimes differ).
- Preheader matches first line strategy from stakeholder discussion.

---

## Revision history

- **2026-03-26:** Project doc created; March email executed from `Mike's March Newsletter_CT_V2.docx` with verified URLs (Experian blog, Sumsub report, FTC phishing).
- **2026-03-26:** Email copy revised for more natural sentence flow (reduced em-dash usage; clearer connective phrasing in HTML and plain text).
- **2026-03-26:** Skim HTML/TXT added; **BLEND** variant combines v1 aesthetics with skim-first structure and “Mike’s use” lines.
- **2026-03-26:** **CONDENSED** variant: blend aesthetics with reduced word count for heavy inboxes.
- **2026-03-27:** Read #2 in all March variants now points to **U.S. News** (AI-enabled fraud targeting smaller banks); **Sumsub** report moved to optional follow-on table only.
- **2026-03-30:** BLEND HTML/TXT updated from `MIke's Newsletter Edits.docx` (skim box “why / what / want help,” regulator paragraph + PKI bridge, read #2 Mike’s use → behavioral biometrics, “brief leadership” fix). Added **BLEND-OUTLOOK.html** and **BLEND-from-html.pdf** (linked PDF for internal review); handoff folder copies refreshed.
- **2026-03-30:** **`Mike-March-2026-Finalized-Fraud-Email-1.html`:** Outlook-only deliverable from **`MIke's Newsletter Edits_FINAL.docx`**; read #1 adds parenthetical on layered verification (signature authentication + digital certificate). Saved under Desktop **`Mike-Final-March-2026-Fraud-1/`**; BLEND/OUTLOOK/TXT in repo aligned on that sentence.

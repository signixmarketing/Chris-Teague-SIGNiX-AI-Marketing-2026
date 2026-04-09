# Project Structure Recommendations
**Date:** April 9, 2026
**Status:** DRAFT — awaiting Chris's review and go-ahead before any changes are made

---

## Summary

The cleanup pass removed the bulk of the lease app. But four issues remain. Two are leftover lease app files that were missed. Two are structural improvements that will make the project easier to navigate.

---

## Issue 1 — Lease app leftovers still present (DELETE)

These were missed in the first cleanup pass.

### `config/` folder
Django project configuration — settings, URLs, ASGI, WSGI. Pure lease app code. No marketing relevance.

Files to delete:
- `config/__init__.py`
- `config/settings.py`
- `config/asgi.py`
- `config/wsgi.py`
- `config/urls.py`

### `.vscode/` folder
VS Code launch configurations for the Django app — `runserver`, `ngrok tunnel`. These reference deleted scripts and the deleted lease app. They will cause confusion if clicked.

Files to delete:
- `.vscode/launch.json`
- `.vscode/settings.json`
- `.vscode/tasks.json`

### `db.sqlite3`
SQLite database file for the lease app. Already gitignored, but still sitting on disk at the project root. Delete it.

---

## Issue 2 — `05-SETUP-WKHTMLTOPDF/` numbered folder (CONSOLIDATE)

This folder contains one file: `SETUP-WKHTMLTOPDF.md`. The `05-` prefix is a holdover from the lease app's numbered phase structure. There's no Phase 05 anymore.

**Recommendation:** Move `SETUP-WKHTMLTOPDF.md` into `GENERAL-KNOWLEDGE/` alongside the HTML-to-PDF and SIGNiX reference docs where it logically belongs. Then delete the now-empty `05-SETUP-WKHTMLTOPDF/` folder.

---

## Issue 3 — Generated output files mixed with strategy docs at PROJECT-DOCS root (REORGANIZE)

The root of `PROJECT-DOCS/` currently mixes two types of content:
1. **Strategy markdown docs** (`SIGNIX-MARKETING-FRAMEWORK.md`, `SIGNIX-PAID-MEDIA-PLAN-2026.md`, etc.)
2. **Generated output files** (`SIGNiX_PaidMedia_4.6.26.docx`, `SIGNiX_MarketingPlan_4.7.26.pptx`, etc.)

This makes the root noisy and harder to navigate. The `DELIVERABLES/` folder already exists for output files — it just needs the root-level output files moved into it.

**Files to move from `PROJECT-DOCS/` → `PROJECT-DOCS/DELIVERABLES/`:**

| File | Type |
|------|------|
| `SIGNiX_ABM_Scorecard.docx` | Output |
| `SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx` | Output |
| `SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx` | Output |
| `SIGNiX_CampaignMeasurement_April2026.docx` | Output |
| `SIGNiX_Dashboard_April2026.html` | Output |
| `SIGNiX_GoogleAds_4.9.26.docx` | Output |
| `SIGNiX_Keyword_Master_4.6.26.xlsx` | Output |
| `SIGNiX_MarketingPlan_4.7.26.pptx` | Output |
| `SIGNiX_PaidMedia_4.6.26.docx` | Output |
| `SIGNiX_PaidMedia_4.6.26.pptx` | Output |
| `SIGNiX_SlideC_Audiences.pptx` | Output |
| `SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx` | Output |
| `SIGNIX-PAID-MEDIA-SLIDES.html` | Output |

After this move, `PROJECT-DOCS/` root will contain only:
- **Navigation:** `00-INDEX.md`, `BRIEFING.md`, `COLLABORATION-AND-FEEDBACK.md`
- **Strategy docs:** `SIGNIX-*.md`, `GOOGLE-ADS-SETUP-GUIDE.md`, `DESIGN-GUIDELINES.md`, `SIGNIX-WRITING-VOICE.md`, `SIGNIX-CEO-PROFILE.md`
- **Planning doc:** `project-structure-recommendations.md` (until implemented, then archived)
- **Folders:** `ARCHIVE/`, `DELIVERABLES/`, `GENERAL-KNOWLEDGE/`, `build-scripts/`, `05-SETUP-WKHTMLTOPDF/` (last one removed per Issue 2)

---

## Issue 4 — `project-cleanup.md` still active (ARCHIVE)

The cleanup plan has been fully implemented. Move `project-cleanup.md` to `ARCHIVE/` so it doesn't clutter the active docs.

---

## What the clean structure looks like after all four fixes

```
proj-template-and-lease-SIGNiX-app/
├── README.md
├── .gitignore
├── demos/
│   └── n8n-notary-lead-routing/
└── PROJECT-DOCS/
    ├── 00-INDEX.md
    ├── BRIEFING.md               (gitignored — local only)
    ├── COLLABORATION-AND-FEEDBACK.md  (gitignored — local only)
    ├── DESIGN-GUIDELINES.md
    ├── GOOGLE-ADS-SETUP-GUIDE.md
    ├── SIGNIX-CEO-PROFILE.md     (gitignored — local only)
    ├── SIGNIX-GROWTH-STRATEGY.md
    ├── SIGNIX-MARKET-RESEARCH-BUYER-JOURNEY.md
    ├── SIGNIX-MARKETING-FRAMEWORK.md
    ├── SIGNIX-MARKETING-PLAN-2026.md
    ├── SIGNIX-PAID-MEDIA-EXEC-SUMMARY.md
    ├── SIGNIX-PAID-MEDIA-PLAN-2026.md
    ├── SIGNIX-POSITIONING-STRATEGY.md
    ├── SIGNIX-TRUSTAGE-CSM-BRIEF.md
    ├── SIGNIX-WRITING-VOICE.md
    ├── ARCHIVE/
    │   ├── README.md
    │   ├── 20-APPROACH.md
    │   ├── project-cleanup.md
    │   ├── project-structure-recommendations.md
    │   ├── build_signix_pptx_ceo.py
    │   ├── mike-march-*-BLEND-*.pdf (x2)
    │   └── GENERAL-KNOWLEDGE/ (app, doc-centric, file-assets)
    ├── DELIVERABLES/
    │   ├── SIGNiX_ABM_Scorecard.docx
    │   ├── SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx
    │   ├── SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx
    │   ├── SIGNiX_CampaignMeasurement_April2026.docx
    │   ├── SIGNiX_Dashboard_April2026.html
    │   ├── SIGNiX_GoogleAds_4.9.26.docx
    │   ├── SIGNiX_Keyword_Master_4.6.26.xlsx
    │   ├── SIGNiX_MarketingPlan_4.7.26.pptx
    │   ├── SIGNiX_PaidMedia_4.6.26.docx
    │   ├── SIGNiX_PaidMedia_4.6.26.pptx
    │   ├── SIGNiX_SlideC_Audiences.pptx
    │   ├── SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx
    │   ├── SIGNIX-PAID-MEDIA-SLIDES.html
    │   ├── SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html + DRAFT.pdf
    │   ├── SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html + DRAFT.pdf
    │   ├── aspen-contact.png
    │   ├── Mike-March-2026-*.html + .pdf
    │   ├── Mike-April-2026-*.html + .pdf
    │   ├── mike-march-2026-fraud-insights-email-*.html/.txt (variants)
    │   ├── mike-fraud-insights-email-TEMPLATE.html
    │   ├── PROJECT-MIKE-MARKET-INSIGHTS-EMAIL.md
    │   ├── SIGNiX-LinkedIn-DimeBank-April2026.md
    │   ├── SIGNiX-LinkedIn-PullQuote-April2026.png
    │   └── SIGNiX-EXECUTIVE-GREETING-CARD-VISTAPRINT/
    ├── GENERAL-KNOWLEDGE/
    │   ├── KNOWLEDGE-HTML-TO-PDF.md
    │   ├── KNOWLEDGE-SIGNiX.md
    │   └── SETUP-WKHTMLTOPDF.md    ← moved from 05-SETUP-WKHTMLTOPDF/
    └── build-scripts/
        ├── README.md
        └── build_signix_*.py (all active scripts)
```

---

## Files affected by this plan

After implementation, all links to moved files in `00-INDEX.md`, `BRIEFING.md`, and `README.md` will be updated to reflect the new paths.

---

## Review checklist (for Chris before go-ahead)

- [ ] OK to delete `config/` (Django settings) and `.vscode/` (Django launch configs)?
- [ ] OK to delete `db.sqlite3` from disk?
- [ ] OK to move all DOCX/PPTX/XLSX/HTML output files into `DELIVERABLES/`?
- [ ] OK to consolidate `SETUP-WKHTMLTOPDF.md` into `GENERAL-KNOWLEDGE/`?

---

*Once you say "go ahead," I will implement this in one pass, update all links, commit, and give you the push command.*

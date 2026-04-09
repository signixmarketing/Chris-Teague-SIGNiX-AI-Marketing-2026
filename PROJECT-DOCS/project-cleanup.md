# Project Cleanup Plan
**Date:** April 9, 2026
**Prepared by:** Delford (AI strategic partner)
**Status:** DRAFT — awaiting Chris's review and go-ahead before any changes are made

---

## What this project has become

This project started as a Django-based Lease Origination Application built for an AI Summit classroom exercise. That gave us a solid structure: project docs, build scripts, a working SIGNiX integration, and a disciplined approach to AI-assisted development.

Over the last three weeks, it has evolved into a **SIGNiX Marketing Toolkit** — a set of strategy documents, branded deliverables, Python build scripts, and operational guides that support Chris's work as Head of Growth and Marketing.

The lease app code and docs are no longer needed for daily work. They add confusion and noise. This plan cleans them out while preserving anything that provides a useful example or foundation for future marketing toolkit work.

---

## Guiding rules for this cleanup

1. **Keep** anything directly useful for SIGNiX marketing strategy, deliverables, or operations.
2. **Archive** anything that was part of the lease app but could be a useful reference or example in the future (methodology docs, SIGNiX API integration code, HTML-to-PDF patterns).
3. **Delete** anything that is purely lease app scaffolding with no reuse value (Django app code, media files, student setup guides, app backup scripts).
4. **Consolidate** the messy `06-DOCS/` email file duplication — same files are in three places.
5. **Rename** `06-DOCS/` → `DELIVERABLES/` to better describe what's there.

---

## Part 1 — DELETE (no marketing value, no reuse value)

### Django application code
The entire Django lease origination app. None of this is part of the marketing toolkit.

| Path | Reason |
|------|---------|
| `apps/` (entire folder) | Django models, views, forms, migrations for the lease app. Not relevant to marketing. |
| `templates/` (entire folder) | Django HTML templates for the lease app UI. |
| `media/` (entire folder) | Sample Zoom Jetpack lease documents and media files. |
| `manage.py` | Django entry point. |
| `requirements.txt` | Django dependencies. |

### Distribution and setup
Setup guides for AI Summit students running the lease app.

| Path | Reason |
|------|---------|
| `distribution/` (entire folder) | Student setup guides, db.sqlite3, media.tar.gz. No marketing relevance. |

### App maintenance scripts
Python scripts for backing up, restoring, and maintaining the lease app.

| Path | Reason |
|------|---------|
| `scripts/backup_app_state.py` | App backup — lease app only. |
| `scripts/restore_app_state.py` | App restore — lease app only. |
| `scripts/capture_distribution.py` | Creates the distribution package for students. |
| `scripts/restore_distribution.py` | Restores the distribution package. |
| `scripts/verify_app_backups.py` | Verifies app backups. |
| `scripts/run_ngrok.py` | ngrok tunnel for the lease app demo. |
| `scripts/verify_ngrok.sh` | ngrok verification script. |
| `scripts/doc_refs_to_links.py` | Doc reference link converter for the lease app docs. |
| `scripts/update_doc_refs.py` | Doc reference updater for the lease app docs. |
| `scripts/verify_doc_links.py` | Link verifier for the lease app docs. |

### Lease app PROJECT-DOCS — phase plans and designs
All phase plans and design docs specific to the lease origination application.

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/01-BASELINE/` (entire folder) | Baseline auth, profile, and app shell design for the lease app. |
| `PROJECT-DOCS/02-BIZ-DOMAIN/` (entire folder) | Vehicles, Contacts, Deals domain for the lease app, including Zoom Jetpack knowledge. |
| `PROJECT-DOCS/03-IMAGES/` (entire folder) | Image upload phase for the lease app. |
| `PROJECT-DOCS/04-DATA-INTERFACE/` (entire folder) | Data schema viewer for the lease app. |
| `PROJECT-DOCS/07-SIGNiX-SUBMIT/` (entire folder) | SIGNiX submit flow design for the lease app deal workflow. |
| `PROJECT-DOCS/08-NGROK/` (entire folder) | ngrok setup for the lease app webhook listener. |
| `PROJECT-DOCS/09-SIGNiX-DASHBOARD-SYNC/` (entire folder) | SIGNiX dashboard and sync for the lease app. |
| `PROJECT-DOCS/10-PROJECT-PITCH.md` | Project pitch for the lease origination app. |
| `PROJECT-DOCS/15-USER-PROFILES-VALUE-PROPOSITION.md` | Personas for the lease app (car dealers, leasing agents). |
| `PROJECT-DOCS/30-SCOPE.md` | Scope for the lease app. |
| `PROJECT-DOCS/40-REQUIREMENTS.md` | Requirements for the lease app. |
| `PROJECT-DOCS/50-WBS.md` | Work breakdown structure for the lease app. |
| `PROJECT-DOCS/60-LOE.md` | Level of effort for the lease app. |
| `PROJECT-DOCS/70-PLAN-MASTER.md` | Master plan for the lease app phases. |
| `PROJECT-DOCS/80-FUTURE-ROADMAP.md` | Future roadmap for the lease app. |

### Lease app document template plans (inside 06-DOCS)
These plans describe how to add document templates to the lease app, not the marketing toolkit.

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/06-DOCS/DESIGN-DOCS.md` | Document template design for the lease app. |
| `PROJECT-DOCS/06-DOCS/PHASE-PLANS-DOCS.md` | Document phase plans for the lease app. |
| `PROJECT-DOCS/06-DOCS/10-PLAN-ADD-STATIC-DOC-TEMPLATES.md` | Lease app plan. |
| `PROJECT-DOCS/06-DOCS/20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md` | Lease app plan. |
| `PROJECT-DOCS/06-DOCS/30-PLAN-ADD-DOC-SET-TEMPLATES.md` | Lease app plan. |
| `PROJECT-DOCS/06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md` | Lease app plan. |

### Personal build scripts (not SIGNiX marketing)

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/build-scripts/build_ct2026_jobplan_docx.py` | Personal job plan document. Not SIGNiX marketing. |
| `PROJECT-DOCS/build-scripts/build_ct2026plan_docx.py` | Personal plan document. Not SIGNiX marketing. |
| `PROJECT-DOCS/build-scripts/build_teague_resume_docx.py` | Chris's resume. Not SIGNiX marketing. |
| `PROJECT-DOCS/build-scripts/build_teague_resume_v2_docx.py` | Chris's resume v2. Not SIGNiX marketing. |

### Duplicate and stale build scripts

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/build-scripts/build_signix_pptx_rev2.py` | Earlier revision of the paid media PPT script. Superseded by `build_signix_paid_media_4_6_26_pptx.py`. |

### Duplicate and stale email files in 06-DOCS
The Mike email files exist in three places: the root of 06-DOCS, `Mike's 1st Email/`, and `mike-fraud-insights-email-MARCH-2026/`. The canonical versions are the ones at the root of 06-DOCS. The subfolder copies and zip archives are duplicates.

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/06-DOCS/Mike's 1st Email/` (entire folder) | Duplicate of root-level files. Folder name has a space — messy. |
| `PROJECT-DOCS/06-DOCS/mike-fraud-insights-email-MARCH-2026/` (entire folder) | Duplicate of root-level files. |
| `PROJECT-DOCS/06-DOCS/Mikes-1st-Email.zip` | Zip archive of email files. Already in project unzipped. |
| `PROJECT-DOCS/06-DOCS/mike-fraud-insights-email-MARCH-2026-complete.zip` | Zip archive. Already in project unzipped. |
| `PROJECT-DOCS/06-DOCS/mike-fraud-insights-email-kit.zip` | Zip archive. Already in project unzipped. |
| `PROJECT-DOCS/06-DOCS/_FINAL_WORD_EXTRACT.txt` | Scratch file. No clear purpose. |

### Installer package

| Path | Reason |
|------|---------|
| `wkhtmltox.pkg` | macOS installer for wkhtmltopdf. Already installed. Excluded from git via .gitignore. Can delete the file from disk; the tool remains installed. |

### Empty placeholder

| Path | Reason |
|------|---------|
| `docs/` (entire folder — just contains `2026 Marketing AI/.gitkeep`) | Empty placeholder folder. |

### Older PDF versions now superseded

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT_lowres.pdf` | Replaced by the corrected `_DRAFT.pdf` version (April 9 fix). |
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT_lowresV1.pdf` | Replaced by the corrected `_DRAFT.pdf` version (April 9 fix). |

### Older Word/PPT deliverables superseded by April 6+ versions

| Path | Reason |
|------|---------|
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-PLAN-2026.docx` | Rev 2 Word doc. Superseded by `SIGNiX_PaidMedia_4.6.26.docx` (Rev 3). |
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-SLIDES.pptx` | Rev 2 PPT. Superseded by `SIGNiX_PaidMedia_4.6.26.pptx` (Rev 3). |
| `PROJECT-DOCS/SIGNiX_GoogleAds_April2026.docx` | Earlier Google Ads copy doc. Superseded by `SIGNiX_GoogleAds_4.9.26.docx`. |

---

## Part 2 — ARCHIVE (move to `PROJECT-DOCS/ARCHIVE/`)

These files are from the lease app era but contain useful patterns, methodology, or examples that could inform future marketing toolkit work.

| Path | Archive reason |
|------|---------------|
| `PROJECT-DOCS/20-APPROACH.md` | Describes the AI-assisted document-driven development methodology. Directly applicable to how the marketing toolkit is built and extended. Worth keeping as a reference. |
| `PROJECT-DOCS/GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md` | General app structure patterns. Could be useful if the marketing toolkit ever needs a web interface (e.g. a live dashboard app). |
| `PROJECT-DOCS/GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md` | Document-centric patterns. Has overlap with how the build scripts generate branded documents. |
| `PROJECT-DOCS/GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md` | File storage and media handling. Potentially relevant if dashboard or email builder needs file uploads. |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-BLEND-from-html.pdf` | PDF render of the email blend. Duplicate of what can be regenerated, but harmless to keep in archive. |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-BLEND-interactive.pdf` | Interactive PDF version. Same — archive, not delete, since it was a deliberate artifact. |
| `PROJECT-DOCS/build-scripts/build_signix_pptx_ceo.py` | CEO-trimmed version of the paid media slides script. No longer the primary script, but shows the CEO slide format. Archive rather than delete. |

---

## Part 3 — KEEP (no changes)

### Core marketing strategy documents
| Path |
|------|
| `PROJECT-DOCS/BRIEFING.md` |
| `PROJECT-DOCS/COLLABORATION-AND-FEEDBACK.md` |
| `PROJECT-DOCS/DESIGN-GUIDELINES.md` |
| `PROJECT-DOCS/GOOGLE-ADS-SETUP-GUIDE.md` |
| `PROJECT-DOCS/SIGNIX-CEO-PROFILE.md` |
| `PROJECT-DOCS/SIGNIX-GROWTH-STRATEGY.md` |
| `PROJECT-DOCS/SIGNIX-MARKET-RESEARCH-BUYER-JOURNEY.md` |
| `PROJECT-DOCS/SIGNIX-MARKETING-FRAMEWORK.md` |
| `PROJECT-DOCS/SIGNIX-MARKETING-PLAN-2026.md` |
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-EXEC-SUMMARY.md` |
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-PLAN-2026.md` |
| `PROJECT-DOCS/SIGNIX-POSITIONING-STRATEGY.md` |
| `PROJECT-DOCS/SIGNIX-TRUSTAGE-CSM-BRIEF.md` |
| `PROJECT-DOCS/SIGNIX-WRITING-VOICE.md` |

### Deliverables
| Path |
|------|
| `PROJECT-DOCS/SIGNiX_ABM_Scorecard.docx` |
| `PROJECT-DOCS/SIGNiX_CFO_PaidMedia_Brief_4.6.26.docx` |
| `PROJECT-DOCS/SIGNiX_CRO_PaidMedia_Brief_4.6.26.docx` |
| `PROJECT-DOCS/SIGNiX_CampaignMeasurement_April2026.docx` |
| `PROJECT-DOCS/SIGNiX_Dashboard_April2026.html` |
| `PROJECT-DOCS/SIGNiX_GoogleAds_4.9.26.docx` |
| `PROJECT-DOCS/SIGNiX_Keyword_Master_4.6.26.xlsx` |
| `PROJECT-DOCS/SIGNiX_MarketingPlan_4.7.26.pptx` |
| `PROJECT-DOCS/SIGNiX_PaidMedia_4.6.26.docx` |
| `PROJECT-DOCS/SIGNiX_PaidMedia_4.6.26.pptx` |
| `PROJECT-DOCS/SIGNiX_SlideC_Audiences.pptx` |
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx` |
| `PROJECT-DOCS/SIGNIX-PAID-MEDIA-SLIDES.html` |

### Marketing collateral (06-DOCS / DELIVERABLES)
| Path |
|------|
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html` |
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_OnePager_v2_aspen_DRAFT.pdf` |
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html` |
| `PROJECT-DOCS/06-DOCS/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen_DRAFT.pdf` |
| `PROJECT-DOCS/06-DOCS/aspen-contact.png` |
| `PROJECT-DOCS/06-DOCS/SIGNiX-LinkedIn-DimeBank-April2026.md` |
| `PROJECT-DOCS/06-DOCS/SIGNiX-LinkedIn-PullQuote-April2026.png` |
| `PROJECT-DOCS/06-DOCS/SIGNiX-EXECUTIVE-GREETING-CARD-VISTAPRINT/` (entire folder) |
| `PROJECT-DOCS/06-DOCS/Mike-April-2026-Fraud-Email-2.html` |
| `PROJECT-DOCS/06-DOCS/Mike-April-2026-Fraud-Email2-Outlook.pdf` |
| `PROJECT-DOCS/06-DOCS/Mike-March-2026-Finalized-Fraud-Email-1.html` |
| `PROJECT-DOCS/06-DOCS/Mike-March-2026-Fraud-Insights-Email1-SHORT.pdf` |
| `PROJECT-DOCS/06-DOCS/PROJECT-MIKE-MARKET-INSIGHTS-EMAIL.md` |
| `PROJECT-DOCS/06-DOCS/mike-fraud-insights-email-TEMPLATE.html` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email.html` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email.txt` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-SKIM.html` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-SKIM.txt` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-BLEND.html` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-BLEND.txt` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-CONDENSED.html` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-CONDENSED.txt` |
| `PROJECT-DOCS/06-DOCS/mike-march-2026-fraud-insights-email-BLEND-OUTLOOK.html` (if present) |

### Build scripts (SIGNiX marketing)
| Path |
|------|
| `PROJECT-DOCS/build-scripts/README.md` |
| `PROJECT-DOCS/build-scripts/build_signix_abm_scorecard.py` |
| `PROJECT-DOCS/build-scripts/build_signix_cfo_brief_4_6_26.py` |
| `PROJECT-DOCS/build-scripts/build_signix_cro_brief_4_6_26.py` |
| `PROJECT-DOCS/build-scripts/build_signix_dashboard.py` |
| `PROJECT-DOCS/build-scripts/build_signix_docx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_google_ads_docx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_keyword_master_xlsx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_marketing_plan_pptx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_measurement_timeline_docx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_paid_media_4_6_26_docx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_paid_media_4_6_26_pptx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_pptx.py` |
| `PROJECT-DOCS/build-scripts/build_signix_slide_c.py` |
| `PROJECT-DOCS/build-scripts/update_slide5_keyword_analysis.py` |

### Setup and reference
| Path |
|------|
| `PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md` |
| `PROJECT-DOCS/GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md` |
| `PROJECT-DOCS/GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md` |

### SIGNiX API demo
| Path |
|------|
| `demos/n8n-notary-lead-routing/` (entire folder) |

### Root and config
| Path |
|------|
| `README.md` |
| `.gitignore` |
| `.cursor/` (rules folder) |

---

## Part 4 — RENAME

| Current path | New path | Reason |
|---|---|---|
| `PROJECT-DOCS/06-DOCS/` | `PROJECT-DOCS/DELIVERABLES/` | Better describes what's there — marketing deliverables, not "Phase 06 document templates." All internal references in 00-INDEX.md and BRIEFING.md will be updated. |

---

## Part 5 — UPDATE after cleanup

| File | What to update |
|------|---------------|
| `PROJECT-DOCS/00-INDEX.md` | Remove all lease app phase entries; add DELIVERABLES section; update build scripts list; add ARCHIVE section with brief note |
| `PROJECT-DOCS/BRIEFING.md` | Update file paths if any references use `06-DOCS/` |
| `README.md` | Already updated — no changes needed |

---

## Summary counts

| Action | Count |
|--------|-------|
| Delete (lease app code + dist + scripts) | ~150+ files across `apps/`, `templates/`, `media/`, `scripts/`, `distribution/` |
| Delete (lease app PROJECT-DOCS) | ~35 files across phases 01–04, 07–09, 10–80 |
| Delete (stale deliverables and duplicates) | ~15 files |
| Archive → `PROJECT-DOCS/ARCHIVE/` | ~8 files |
| Rename `06-DOCS/` → `DELIVERABLES/` | 1 folder rename + link updates |
| Keep (no change) | ~65 files — all SIGNiX marketing content |

---

## What you will NOT lose

Before implementing, confirm:

- All strategy documents (`SIGNIX-MARKETING-FRAMEWORK.md`, `SIGNIX-MARKETING-PLAN-2026.md`, `SIGNIX-PAID-MEDIA-PLAN-2026.md`, etc.) — **KEPT**
- All deliverables (PDFs, DOCX, PPTX, XLSX, HTML dashboard) — **KEPT**
- All build scripts for marketing documents — **KEPT**
- All email files and source HTML — **KEPT** (duplicates removed)
- BRIEFING.md, CEO profile, design guidelines — **KEPT**
- The n8n lead routing demo — **KEPT**
- The wkhtmltopdf setup guide — **KEPT**
- ABS collateral source files and corrected PDFs — **KEPT**
- Google Ads setup guide — **KEPT**

---

## Review checklist (for Chris before go-ahead)

- [ ] Comfortable removing the entire `apps/`, `templates/`, `media/` Django app code?
- [ ] Comfortable removing the `distribution/` student setup guides?
- [ ] OK to rename `06-DOCS/` to `DELIVERABLES/`?
- [ ] Any personal build scripts (resume, job plan) you want to keep somewhere?
- [ ] Any lease app phase docs you want to keep beyond `20-APPROACH.md`?
- [ ] Confirm the `SIGNiX_SlideC_Audiences.pptx` and `SIGNIX-PAID-MEDIA-SLIDES-CEO.pptx` are still needed (they are in KEEP list)?

---

*Once you review and say "go ahead," I will implement this plan in one pass, commit the changes, and give you the push command.*

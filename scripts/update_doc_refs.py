#!/usr/bin/env python3
"""
Update all cross-references in PROJECT-DOCS .md files to use relative paths.
Run from repo root. Mapping: old filename -> path relative to PROJECT_DOCS.

IMPORTANT: Do not run this script on 00-INDEX.md — the index uses intentional
paths (relative to PROJECT-DOCS); the script would corrupt them (e.g. double
prefixes or wrong replacements inside path strings).
"""
import os
import re

PROJECT_DOCS = "PROJECT-DOCS"

# Old filename -> path relative to PROJECT_DOCS (so we can compute relpath from any file)
MAPPING = {
    # Project-level
    "PROJECT-PITCH.md": "10-PROJECT-PITCH.md",
    "APPROACH.md": "20-APPROACH.md",
    "SCOPE.md": "30-SCOPE.md",
    "REQUIREMENTS.md": "40-REQUIREMENTS.md",
    "WBS.md": "50-WBS.md",
    "LOE.md": "60-LOE.md",
    "PLAN-MASTER.md": "70-PLAN-MASTER.md",
    # General knowledge
    "KNOWLEDGE-APP-FOUNDATION.md": "GENERAL-KNOWLEDGE/KNOWLEDGE-APP-FOUNDATION.md",
    "KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md": "GENERAL-KNOWLEDGE/KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md",
    "KNOWLEDGE-FILE-ASSETS-MEDIA.md": "GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md",
    "KNOWLEDGE-HTML-TO-PDF.md": "GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md",
    "KNOWLEDGE-SIGNiX.md": "GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md",
    # 01-BASELINE
    "DESIGN-BASELINE.md": "01-BASELINE/DESIGN-BASELINE.md",
    "PLAN-BASELINE.md": "01-BASELINE/10-PLAN-BASELINE.md",
    # 02-BIZ-DOMAIN
    "DESIGN-BIZ-DOMAIN.md": "02-BIZ-DOMAIN/DESIGN-BIZ-DOMAIN.md",
    "PHASE-PLANS-BIZ-DOMAIN.md": "02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md",
    "KNOWLEDGE-LEASE-JETPACKS.md": "02-BIZ-DOMAIN/KNOWLEDGE-LEASE-JETPACKS.md",
    "PLAN-ADD-VEHICLES.md": "02-BIZ-DOMAIN/10-PLAN-ADD-VEHICLES.md",
    "PLAN-ADD-CONTACTS.md": "02-BIZ-DOMAIN/20-PLAN-ADD-CONTACTS.md",
    "PLAN-ADD-DEALS.md": "02-BIZ-DOMAIN/30-PLAN-ADD-DEALS.md",
    # 03-IMAGES
    "DESIGN-IMAGES.md": "03-IMAGES/DESIGN-IMAGES.md",
    "PLAN-ADD-IMAGES.md": "03-IMAGES/10-PLAN-ADD-IMAGES.md",
    # 04-DATA-INTERFACE
    "DESIGN-DATA-INTERFACE.md": "04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md",
    "PLAN-DATA-INTERFACE.md": "04-DATA-INTERFACE/10-PLAN-DATA-INTERFACE.md",
    # 05-SETUP
    "SETUP-WKHTMLTOPDF.md": "05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md",
    # 06-DOCS
    "DESIGN-DOCS.md": "06-DOCS/DESIGN-DOCS.md",
    "PHASE-PLANS-DOCS.md": "06-DOCS/PHASE-PLANS-DOCS.md",
    "PLAN-ADD-STATIC-DOC-TEMPLATES.md": "06-DOCS/10-PLAN-ADD-STATIC-DOC-TEMPLATES.md",
    "PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md": "06-DOCS/20-PLAN-ADD-DYNAMIC-DOC-TEMPLATES.md",
    "PLAN-ADD-DOC-SET-TEMPLATES.md": "06-DOCS/30-PLAN-ADD-DOC-SET-TEMPLATES.md",
    "PLAN-ADD-DOCUMENT-SETS.md": "06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md",
    # 07-SIGNiX-SUBMIT
    "DESIGN-SIGNiX-SUBMIT.md": "07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md",
    "PHASE-PLANS-SIGNiX-SUBMIT.md": "07-SIGNiX-SUBMIT/PHASE-PLANS-SIGNiX-SUBMIT.md",
    "PLAN-SIGNiX-CONFIG.md": "07-SIGNiX-SUBMIT/10-PLAN-SIGNiX-CONFIG.md",
    "PLAN-SIGNiX-SIGNATURE-TRANSACTION.md": "07-SIGNiX-SUBMIT/20-PLAN-SIGNiX-SIGNATURE-TRANSACTION.md",
    "PLAN-SIGNiX-SIGNER-SERVICE.md": "07-SIGNiX-SUBMIT/30-PLAN-SIGNiX-SIGNER-SERVICE.md",
    "PLAN-SIGNiX-SIGNERS-TABLE.md": "07-SIGNiX-SUBMIT/40-PLAN-SIGNiX-SIGNERS-TABLE.md",
    "PLAN-SIGNiX-BUILD-BODY.md": "07-SIGNiX-SUBMIT/50-PLAN-SIGNiX-BUILD-BODY.md",
    "PLAN-SIGNiX-SEND-AND-PERSIST.md": "07-SIGNiX-SUBMIT/60-PLAN-SIGNiX-SEND-AND-PERSIST.md",
    "PLAN-SIGNiX-SEND-FOR-SIGNATURE.md": "07-SIGNiX-SUBMIT/70-PLAN-SIGNiX-SEND-FOR-SIGNATURE.md",
    "PLAN-SIGNiX-DASHBOARD.md": "07-SIGNiX-SUBMIT/80-PLAN-SIGNiX-DASHBOARD.md",
    "PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md": "07-SIGNiX-SUBMIT/90-PLAN-SIGNiX-DEAL-VIEW-TRANSACTIONS.md",
    # 08-NGROK
    "PLAN-NGROK.md": "08-NGROK/10-PLAN-NGROK.md",
    # 09-SIGNiX-DASHBOARD-SYNC
    "DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md": "09-SIGNiX-DASHBOARD-SYNC/DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md",
    "PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md": "09-SIGNiX-DASHBOARD-SYNC/PHASE-PLANS-SIGNiX-DASHBOARD-SYNC.md",
    "PLAN-SIGNiX-SYNC-MODEL.md": "09-SIGNiX-DASHBOARD-SYNC/10-PLAN-SIGNiX-SYNC-MODEL.md",
    "PLAN-SIGNiX-PUSH-LISTENER.md": "09-SIGNiX-DASHBOARD-SYNC/20-PLAN-SIGNiX-PUSH-LISTENER.md",
    "PLAN-SIGNiX-SUBMIT-PUSH-URL.md": "09-SIGNiX-DASHBOARD-SYNC/30-PLAN-SIGNiX-SUBMIT-PUSH-URL.md",
    "PLAN-SIGNiX-DASHBOARD-SIGNERS.md": "09-SIGNiX-DASHBOARD-SYNC/40-PLAN-SIGNiX-DASHBOARD-SIGNERS.md",
    "PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md": "09-SIGNiX-DASHBOARD-SYNC/50-PLAN-SIGNiX-DOWNLOAD-ON-COMPLETE.md",
    "PLAN-SIGNiX-TRANSACTION-DETAIL.md": "09-SIGNiX-DASHBOARD-SYNC/60-PLAN-SIGNiX-TRANSACTION-DETAIL.md",
}

# Sort by length descending so longer names get replaced before shorter
ORDERED_KEYS = sorted(MAPPING.keys(), key=len, reverse=True)


def main():
    for root, _dirs, files in os.walk(PROJECT_DOCS):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            if path == os.path.join(PROJECT_DOCS, "00-INDEX.md"):
                continue  # Do not modify index; it uses intentional paths
            current_dir = os.path.relpath(root, PROJECT_DOCS)
            if current_dir == ".":
                current_dir = ""
            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()
            original = content
            for old_name in ORDERED_KEYS:
                target_path = MAPPING[old_name]
                rel = os.path.relpath(
                    os.path.join(PROJECT_DOCS, target_path),
                    os.path.join(PROJECT_DOCS, current_dir),
                )
                rel = rel.replace("\\", "/")
                pattern = r"\b" + re.escape(old_name) + r"\b"
                content = re.sub(pattern, rel, content)
            if content != original:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(content)
                print(f"Updated: {path}")


if __name__ == "__main__":
    main()

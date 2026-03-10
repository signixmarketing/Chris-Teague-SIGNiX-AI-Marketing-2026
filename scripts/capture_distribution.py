#!/usr/bin/env python3
"""
Capture current application state into distribution/ for class distribution.

Creates distribution/db.sqlite3 (SQLite backup) and distribution/media.tar.gz
(archive of media/). Commit these files and push to GitHub so students can
run the restore script after cloning.

Usage:
  python scripts/capture_distribution.py
  ./scripts/capture_distribution.py

Run from project root (where manage.py and db.sqlite3 live).
"""

import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISTRIBUTION_DIR = PROJECT_ROOT / "distribution"
DB_PATH = PROJECT_ROOT / "db.sqlite3"
MEDIA_DIR = PROJECT_ROOT / "media"


def main():
    if not PROJECT_ROOT.joinpath("manage.py").exists():
        print("Error: Run from project root (where manage.py is).", file=sys.stderr)
        sys.exit(1)

    DISTRIBUTION_DIR.mkdir(parents=True, exist_ok=True)
    dest_db = DISTRIBUTION_DIR / "db.sqlite3"
    dest_media_archive = DISTRIBUTION_DIR / "media.tar.gz"

    # 1. Database
    if not DB_PATH.exists():
        print("Warning: db.sqlite3 not found; skipping database.", file=sys.stderr)
    else:
        try:
            src = sqlite3.connect(DB_PATH)
            dest = sqlite3.connect(dest_db)
            src.backup(dest)
            src.close()
            dest.close()
            print("Captured database -> %s" % dest_db)
        except sqlite3.Error as e:
            print("Error capturing database: %s" % e, file=sys.stderr)
            sys.exit(1)

    # 2. Media archive
    if not MEDIA_DIR.exists():
        print("Note: media/ not found; skipping media archive.")
    else:
        try:
            with tarfile.open(dest_media_archive, "w:gz") as tar:
                tar.add(MEDIA_DIR, arcname="media")
            print("Captured media -> %s" % dest_media_archive)
        except (OSError, tarfile.TarError) as e:
            print("Error capturing media: %s" % e, file=sys.stderr)
            sys.exit(1)

    print("\nCapture complete: %s" % DISTRIBUTION_DIR)
    print("Next: commit and push so students can restore:")
    print("  git add distribution/ scripts/capture_distribution.py scripts/restore_distribution.py")
    print("  git commit -m 'Add distribution bundle and capture/restore scripts for class'")
    print("  git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())

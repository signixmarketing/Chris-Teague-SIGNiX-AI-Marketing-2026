#!/usr/bin/env python3
"""
Create a timestamped backup of application state: SQLite DB and media directory.
Backups are stored under backups/YYYYMMDD-HHMMSS/ (db.sqlite3 + media/).

Usage:
  python scripts/backup_app_state.py [--backup-dir DIR]
  ./scripts/backup_app_state.py

Uses SQLite backup API for a consistent DB copy even if the app is running.
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"
DB_PATH = PROJECT_ROOT / "db.sqlite3"
MEDIA_DIR = PROJECT_ROOT / "media"


def main():
    parser = argparse.ArgumentParser(
        description="Back up application state (db.sqlite3 and media/) to a timestamped directory."
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory to store backups (default: {DEFAULT_BACKUP_DIR})",
    )
    args = parser.parse_args()
    backup_root = args.backup_dir.resolve()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 1. Back up database (SQLite backup API for consistency)
    if not DB_PATH.exists():
        print(f"Warning: {DB_PATH} not found; skipping database backup.", file=sys.stderr)
    else:
        dest_db = backup_dir / "db.sqlite3"
        try:
            src = sqlite3.connect(DB_PATH)
            dest = sqlite3.connect(dest_db)
            src.backup(dest)
            src.close()
            dest.close()
        except sqlite3.Error as e:
            print(f"Error backing up database: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Backed up database -> {dest_db}")

    # 2. Back up media directory
    if not MEDIA_DIR.exists():
        print(f"Note: {MEDIA_DIR} not found; skipping media backup.")
    else:
        dest_media = backup_dir / "media"
        try:
            shutil.copytree(MEDIA_DIR, dest_media, dirs_exist_ok=False)
        except FileExistsError:
            print(f"Error: {dest_media} already exists.", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error backing up media: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Backed up media -> {dest_media}")

    print(f"Backup complete: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

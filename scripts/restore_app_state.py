#!/usr/bin/env python3
"""
List available backups and restore application state from a chosen backup.
Backups are expected under backups/YYYYMMDD-HHMMSS/ (db.sqlite3 and optionally media/).

Usage:
  python scripts/restore_app_state.py              # list backups
  python scripts/restore_app_state.py latest         # restore most recent
  python scripts/restore_app_state.py 20250219-143000
  python scripts/restore_app_state.py 1              # restore by index (1 = newest)
  python scripts/restore_app_state.py 2 --yes       # skip confirmation
"""

import argparse
import shutil
import sys
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"
DB_PATH = PROJECT_ROOT / "db.sqlite3"
MEDIA_DIR = PROJECT_ROOT / "media"


def get_backups(backup_root: Path) -> list[Path]:
    """Return backup directories sorted newest first (by name = timestamp)."""
    if not backup_root.exists():
        return []
    dirs = [p for p in backup_root.iterdir() if p.is_dir() and (p / "db.sqlite3").exists()]
    dirs.sort(key=lambda p: p.name, reverse=True)
    return dirs


def main():
    parser = argparse.ArgumentParser(
        description="List backups or restore application state from a backup."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Backup to restore: 'latest', a timestamp (e.g. 20250219-143000), or index 1, 2, ...",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory where backups are stored (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt when restoring",
    )
    args = parser.parse_args()
    backup_root = args.backup_dir.resolve()

    backups = get_backups(backup_root)

    # List only
    if args.target is None:
        if not backups:
            print("No backups found.")
            return 0
        print("Available backups (newest first):")
        for i, b in enumerate(backups, start=1):
            db = "db.sqlite3"
            media = "media" if (b / "media").exists() else "-"
            print(f"  {i}. {b.name}  [{db}, {media}]")
        return 0

    # Resolve target to a backup directory
    target = args.target.strip().lower()
    if target == "latest" or target == "1":
        chosen = backups[0] if backups else None
    elif target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(backups):
            chosen = backups[idx - 1]
        else:
            chosen = None
    else:
        chosen = backup_root / target
        if not chosen.is_dir() or not (chosen / "db.sqlite3").exists():
            chosen = None

    if chosen is None or not chosen.exists():
        print("No such backup. Run without arguments to list backups.", file=sys.stderr)
        sys.exit(1)

    chosen = chosen.resolve()

    if not args.yes:
        print(f"Restore will overwrite:")
        print(f"  {DB_PATH}")
        print(f"  {MEDIA_DIR}/")
        print(f"with content from: {chosen}")
        try:
            r = input("Proceed? [y/N]: ").strip().lower()
        except EOFError:
            r = "n"
        if r != "y" and r != "yes":
            print("Aborted.")
            sys.exit(0)

    # Restore database
    src_db = chosen / "db.sqlite3"
    if not src_db.exists():
        print(f"Error: {src_db} not found.", file=sys.stderr)
        sys.exit(1)
    try:
        shutil.copy2(src_db, DB_PATH)
        print(f"Restored database from {src_db}")
    except OSError as e:
        print(f"Error restoring database: {e}", file=sys.stderr)
        sys.exit(1)

    # Restore media
    src_media = chosen / "media"
    if src_media.exists():
        if MEDIA_DIR.exists():
            shutil.rmtree(MEDIA_DIR)
        shutil.copytree(src_media, MEDIA_DIR)
        print(f"Restored media from {src_media}")
    else:
        print("No media in backup; leaving existing media/ unchanged.")

    print("Restore complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

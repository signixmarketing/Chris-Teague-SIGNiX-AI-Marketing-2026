#!/usr/bin/env python3
"""
Verify backup integrity: SQLite integrity_check and optional media presence.
Use after backup_app_state.py to ensure a backup is restorable.

Usage:
  python scripts/verify_app_backups.py                    # verify all backups
  python scripts/verify_app_backups.py latest              # verify newest only
  python scripts/verify_app_backups.py 1                   # verify by index
  python scripts/verify_app_backups.py 20250219-143000     # verify by timestamp
  python scripts/verify_app_backups.py --backup-dir DIR    # custom backup root
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"


def get_backups(backup_root: Path) -> list[Path]:
    """Return backup directories sorted newest first (by name = timestamp)."""
    if not backup_root.exists():
        return []
    dirs = [p for p in backup_root.iterdir() if p.is_dir() and (p / "db.sqlite3").exists()]
    dirs.sort(key=lambda p: p.name, reverse=True)
    return dirs


def verify_db(db_path: Path) -> tuple[bool, str]:
    """Run SQLite integrity_check. Returns (ok, message)."""
    if not db_path.exists():
        return False, "missing"
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            result = (row and row[0] == "ok")
            return result, "ok" if result else (row[0] if row else "unknown")
        finally:
            conn.close()
    except sqlite3.Error as e:
        return False, str(e)


def verify_media(media_path: Path) -> tuple[bool, str]:
    """Check media dir exists and report stats. Returns (ok, message)."""
    if not media_path.exists():
        return True, "not present"
    if not media_path.is_dir():
        return False, "not a directory"
    try:
        files = list(media_path.rglob("*"))
        file_count = sum(1 for p in files if p.is_file())
        return True, f"{file_count} files"
    except OSError as e:
        return False, str(e)


def verify_one(backup_dir: Path, verbose: bool = True) -> bool:
    """Verify one backup. Returns True if all checks pass."""
    name = backup_dir.name
    all_ok = True

    db_path = backup_dir / "db.sqlite3"
    db_ok, db_msg = verify_db(db_path)
    if not db_ok:
        all_ok = False
    if verbose:
        status = "OK" if db_ok else "FAIL"
        print(f"  {name}: db.sqlite3 ... {status} ({db_msg})")

    media_path = backup_dir / "media"
    media_ok, media_msg = verify_media(media_path)
    if not media_ok:
        all_ok = False
    if verbose:
        status = "OK" if media_ok else "FAIL"
        print(f"  {name}: media/ ...... {status} ({media_msg})")

    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Verify backup integrity (SQLite + media)."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        help="Backup to verify: 'all', 'latest', index (1, 2, ...), or timestamp (default: all)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory where backups are stored (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only print failures; exit 0 if all pass",
    )
    args = parser.parse_args()
    backup_root = args.backup_dir.resolve()

    backups = get_backups(backup_root)
    if not backups:
        print("No backups found.", file=sys.stderr)
        sys.exit(1)

    target = args.target.strip().lower()
    if target == "all":
        to_verify = backups
    elif target == "latest" or target == "1":
        to_verify = [backups[0]]
    elif target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(backups):
            to_verify = [backups[idx - 1]]
        else:
            print(f"Invalid index: {target}. Use 1..{len(backups)}.", file=sys.stderr)
            sys.exit(1)
    else:
        candidate = backup_root / target
        if candidate.is_dir() and (candidate / "db.sqlite3").exists():
            to_verify = [candidate.resolve()]
        else:
            print(f"No such backup: {target}.", file=sys.stderr)
            sys.exit(1)

    if not args.quiet and len(to_verify) > 1:
        print(f"Verifying {len(to_verify)} backup(s):\n")

    failed = 0
    for backup_dir in to_verify:
        if not verify_one(backup_dir, verbose=not args.quiet):
            failed += 1
        if not args.quiet and len(to_verify) > 1:
            print()

    if failed:
        if args.quiet:
            print("One or more backups failed verification.", file=sys.stderr)
        sys.exit(1)
    if not args.quiet:
        print("All backups verified OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

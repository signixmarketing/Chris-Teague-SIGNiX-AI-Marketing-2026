#!/usr/bin/env python3
"""
Restore application state from distribution/ (for students after cloning).

Copies distribution/db.sqlite3 to db.sqlite3 and extracts distribution/media.tar.gz
to media/. Run from project root after: pip install -r requirements.txt, migrate.

Usage:
  python scripts/restore_distribution.py
  ./scripts/restore_distribution.py

Run from project root (where manage.py lives).
"""

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

    src_db = DISTRIBUTION_DIR / "db.sqlite3"
    media_archive = DISTRIBUTION_DIR / "media.tar.gz"

    if not src_db.exists():
        print("Error: distribution/db.sqlite3 not found. Clone the repo and ensure distribution/ is present.", file=sys.stderr)
        sys.exit(1)

    # 1. Run migrations first (in case schema evolved)
    try:
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "manage.py"), "migrate", "--noinput"],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print("Warning: migrate failed: %s" % e, file=sys.stderr)
        # Continue anyway so we can overwrite with distribution db

    # 2. Restore database
    try:
        import shutil
        shutil.copy2(src_db, DB_PATH)
        print("Restored database from distribution/db.sqlite3")
    except OSError as e:
        print("Error restoring database: %s" % e, file=sys.stderr)
        sys.exit(1)

    # 3. Restore media
    if media_archive.exists():
        if MEDIA_DIR.exists():
            import shutil
            shutil.rmtree(MEDIA_DIR)
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(media_archive, "r:gz") as tar:
                tar.extractall(path=PROJECT_ROOT)
            print("Restored media from distribution/media.tar.gz")
        except (OSError, tarfile.TarError) as e:
            print("Error extracting media: %s" % e, file=sys.stderr)
            sys.exit(1)
    else:
        print("Note: distribution/media.tar.gz not found; skipping media.")

    print("\nRestore complete.")
    print("Run the app:  python manage.py runserver")
    print("Then open http://127.0.0.1:8000/ and log in (see project docs for demo user if applicable).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

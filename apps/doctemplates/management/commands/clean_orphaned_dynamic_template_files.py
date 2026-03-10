"""
Remove orphaned HTML files from media/document_templates/dynamic/.

Keeps only files that are still referenced by a DynamicDocumentTemplate.file.
Deletes any other files in that directory (leftovers from re-uploading templates).

Usage:
  python manage.py clean_orphaned_dynamic_template_files --dry-run   # show what would be deleted
  python manage.py clean_orphaned_dynamic_template_files            # delete orphans
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.doctemplates.models import DynamicDocumentTemplate


class Command(BaseCommand):
    help = "Remove orphaned dynamic document template files from media storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only list files that would be deleted; do not delete.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        media_root = Path(settings.MEDIA_ROOT)
        dynamic_dir = media_root / "document_templates" / "dynamic"

        in_use = set()
        for t in DynamicDocumentTemplate.objects.all():
            if t.file:
                in_use.add(t.file.name)

        if not dynamic_dir.exists():
            self.stdout.write("Directory does not exist: %s" % dynamic_dir)
            return 0

        deleted = 0
        kept = 0
        for f in sorted(dynamic_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(media_root)
            rel_str = str(rel).replace("\\", "/")
            if rel_str in in_use:
                kept += 1
                if dry_run:
                    self.stdout.write("Keep: %s" % rel_str)
            else:
                if dry_run:
                    self.stdout.write(self.style.WARNING("Would delete: %s" % rel_str))
                else:
                    try:
                        f.unlink()
                        self.stdout.write("Deleted: %s" % rel_str)
                        deleted += 1
                    except OSError as e:
                        self.stderr.write(self.style.ERROR("Failed to delete %s: %s" % (f, e)))

        if dry_run:
            self.stdout.write("\nDry run: no files deleted. Run without --dry-run to delete.")
        else:
            self.stdout.write(self.style.SUCCESS("\nDeleted %s orphaned file(s). Kept %s in-use file(s)." % (deleted, kept)))
        return 0

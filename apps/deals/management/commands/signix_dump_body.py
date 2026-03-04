"""
Management command: dump SubmitDocument request XML for a deal (Plan 5 optional).

Usage:
    python manage.py signix_dump_body <deal_id>
    python manage.py signix_dump_body <deal_id> --output /path/to/submit.xml

Loads the deal's first document set, calls build_submit_document_body, and writes
the XML to stdout or to a file. Useful for debugging and validating the payload.
Exits with an error if the deal has no document set or validation fails.
"""

from django.core.management.base import BaseCommand

from apps.deals.models import Deal
from apps.deals.signix import build_submit_document_body, SignixValidationError


class Command(BaseCommand):
    help = "Dump SubmitDocument request XML for a deal (first document set)."

    def add_arguments(self, parser):
        parser.add_argument(
            "deal_id",
            type=int,
            help="ID of the deal whose first document set to use.",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default=None,
            help="Write XML to this file instead of stdout.",
        )

    def handle(self, *args, **options):
        deal_id = options["deal_id"]
        output_path = options.get("output")

        deal = Deal.objects.filter(pk=deal_id).select_related("lease_officer", "deal_type").prefetch_related(
            "document_sets__document_set_template", "document_sets__instances__versions", "contacts"
        ).first()
        if deal is None:
            self.stderr.write(self.style.ERROR(f"Deal with id {deal_id} not found."))
            return 1

        document_set = deal.document_sets.first()
        if document_set is None:
            self.stderr.write(
                self.style.ERROR(f"Deal #{deal_id} has no document set. Generate documents first.")
            )
            return 1

        try:
            body, metadata = build_submit_document_body(deal, document_set)
        except SignixValidationError as e:
            self.stderr.write(self.style.ERROR("Validation failed:"))
            for err in e.errors:
                self.stderr.write(f"  - {err}")
            return 1

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(body)
            self.stdout.write(self.style.SUCCESS(f"Wrote XML to {output_path} (transaction_id={metadata['transaction_id']})"))
        else:
            self.stdout.write(body)
        return 0

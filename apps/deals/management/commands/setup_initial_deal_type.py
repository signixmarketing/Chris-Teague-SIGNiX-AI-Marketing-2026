"""
Management command: ensure the default Deal Type exists.

Usage:
    python manage.py setup_initial_deal_type

Creates "Lease - Single Signer" if not present (idempotent).
Safe to run multiple times.
"""

from django.core.management.base import BaseCommand

from apps.deals.models import DealType


class Command(BaseCommand):
    help = "Create the default Deal Type (Lease - Single Signer) if it does not exist (idempotent)."

    def handle(self, *args, **options):
        deal_type, created = DealType.objects.get_or_create(
            name="Lease - Single Signer"
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created deal type: {deal_type.name}"
                )
            )
        else:
            self.stdout.write(
                f"Deal type '{deal_type.name}' already exists."
            )

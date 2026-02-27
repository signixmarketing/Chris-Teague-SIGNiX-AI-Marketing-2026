"""
Management command: create the initial jet pack vehicle if not present.

Usage:
    python manage.py setup_initial_vehicle

Creates the vehicle per PLAN-ADD-VEHICLES.md Section 3 (Skyward Personal Jetpack P-2024).
Safe to run multiple times (idempotent; looks up by jpin).
"""

from django.core.management.base import BaseCommand

from apps.vehicles.models import Vehicle


# Initial vehicle data per PLAN-ADD-VEHICLES.md Section 3.
INITIAL_SKU = "Skyward Personal Jetpack P-2024"
INITIAL_YEAR = "2024"
INITIAL_JPIN = "4CH8P4K7E3X6Z9R2V"


class Command(BaseCommand):
    help = "Create the initial jet pack vehicle if it does not exist (idempotent)."

    def handle(self, *args, **options):
        vehicle, created = Vehicle.objects.get_or_create(
            jpin=INITIAL_JPIN,
            defaults={
                "sku": INITIAL_SKU,
                "year": INITIAL_YEAR,
            },
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created vehicle: {vehicle.sku} (jpin={vehicle.jpin})."
                )
            )
        else:
            self.stdout.write(
                f"Vehicle with jpin '{INITIAL_JPIN}' already exists."
            )

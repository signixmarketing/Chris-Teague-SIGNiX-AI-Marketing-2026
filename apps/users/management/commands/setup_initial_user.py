"""
Management command: create or update the initial lease officer user and profile.

Usage:
    python manage.py setup_initial_user

Creates user "karl" (password "karl", is_staff=True, is_superuser=True) and a LeaseOfficerProfile
with the plan-specified data. Safe to run multiple times (idempotent).
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.users.models import LeaseOfficerProfile


# Initial user and profile data per PLAN-BASELINE.md Section 6.
INITIAL_USERNAME = "karl"
INITIAL_PASSWORD = "karl"
INITIAL_FIRST_NAME = "Karl"
INITIAL_LAST_NAME = "Matthews"
INITIAL_PHONE = "9197440153"
INITIAL_EMAIL = "kmatthews@signix.com"
INITIAL_TIMEZONE = "America/New_York"


class Command(BaseCommand):
    help = "Create or update the initial lease officer user (karl) and profile."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username=INITIAL_USERNAME,
            defaults={
                "is_staff": True,
                "is_superuser": True,  # Full admin: add, edit, and delete users.
                "first_name": INITIAL_FIRST_NAME,
                "last_name": INITIAL_LAST_NAME,
                "email": INITIAL_EMAIL,
            },
        )
        if created:
            user.set_password(INITIAL_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{INITIAL_USERNAME}'."))
        else:
            # Ensure existing karl stays a superuser so they can manage users.
            if not user.is_superuser:
                user.is_superuser = True
                user.save()
            self.stdout.write(f"User '{INITIAL_USERNAME}' already exists.")

        profile, profile_created = LeaseOfficerProfile.objects.get_or_create(
            user=user,
            defaults={
                "first_name": INITIAL_FIRST_NAME,
                "last_name": INITIAL_LAST_NAME,
                "phone_number": INITIAL_PHONE,
                "email": INITIAL_EMAIL,
                "timezone": INITIAL_TIMEZONE,
            },
        )
        if not profile_created:
            # Keep profile in sync with plan data (idempotent update).
            profile.first_name = INITIAL_FIRST_NAME
            profile.last_name = INITIAL_LAST_NAME
            profile.phone_number = INITIAL_PHONE
            profile.email = INITIAL_EMAIL
            profile.timezone = INITIAL_TIMEZONE
            profile.save()
            self.stdout.write("Updated existing lease officer profile.")
        else:
            self.stdout.write(self.style.SUCCESS("Created lease officer profile."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Initial user ready: username={INITIAL_USERNAME}, password={INITIAL_PASSWORD}"
            )
        )

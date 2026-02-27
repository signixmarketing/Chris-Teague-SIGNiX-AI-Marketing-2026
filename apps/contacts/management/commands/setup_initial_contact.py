"""
Management command: create the initial contact if not present.

Usage:
    python manage.py setup_initial_contact

Creates the contact per PLAN-ADD-CONTACTS.md Section 3 (Max Danger Fun).
Safe to run multiple times (idempotent; looks up by email).
"""

from django.core.management.base import BaseCommand

from apps.contacts.models import Contact


# Initial contact data per PLAN-ADD-CONTACTS.md Section 3.
INITIAL_FIRST_NAME = "Max"
INITIAL_MIDDLE_NAME = "Danger"
INITIAL_LAST_NAME = "Fun"
INITIAL_EMAIL = "signixkarl@gmail.com"
INITIAL_PHONE = "9197440153"


class Command(BaseCommand):
    help = "Create the initial contact if it does not exist (idempotent)."

    def handle(self, *args, **options):
        contact, created = Contact.objects.get_or_create(
            email=INITIAL_EMAIL,
            defaults={
                "first_name": INITIAL_FIRST_NAME,
                "middle_name": INITIAL_MIDDLE_NAME,
                "last_name": INITIAL_LAST_NAME,
                "phone_number": INITIAL_PHONE,
            },
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created contact: {contact} ({contact.email})."
                )
            )
        else:
            self.stdout.write(
                f"Contact with email '{INITIAL_EMAIL}' already exists."
            )

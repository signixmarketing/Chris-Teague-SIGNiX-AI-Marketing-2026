"""
Lease officer profile model.

One profile per User; holds display name, phone, and email for vehicle (jet pack)
lease origination. full_name is derived from first_name + last_name.
"""

from django.conf import settings
from django.db import models


class LeaseOfficerProfile(models.Model):
    """
    Profile for a lease officer (one-to-one with User).

    Used as the source of truth for display name, phone, and email in the
    lease origination app. full_name is computed from first_name and last_name.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lease_officer_profile",
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=30)
    email = models.EmailField()

    class Meta:
        verbose_name = "Lease officer profile"
        verbose_name_plural = "Lease officer profiles"

    def __str__(self):
        return self.full_name

    @property
    def full_name(self) -> str:
        """Display name: first_name + last_name, trimmed."""
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(parts).strip() or "(no name)"

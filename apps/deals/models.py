"""
Deal model for the lease app.

A deal (lease origination) has properties (dates, payment, deposit, insurance,
governing law), a lease officer (User), a deal type (classification for document
generation), and zero-to-many vehicles and contacts. Persistence is in the
project's SQLite database via Django ORM.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.contacts.models import Contact
from apps.vehicles.models import Vehicle


class DealType(models.Model):
    """
    Classification of a deal (e.g., lease, cash purchase). Determines which
    Document Set Template is used when generating documents.
    """

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Deal Type"
        verbose_name_plural = "Deal Types"

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        """Return the default Deal Type (Lease - Single Signer), creating if needed."""
        obj, _ = cls.objects.get_or_create(name="Lease - Single Signer")
        return obj


class Deal(models.Model):
    """
    A lease deal: dates, payment terms, and associations to a lease officer,
    vehicles, and contacts.
    """

    lease_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    deal_type = models.ForeignKey(
        DealType,
        on_delete=models.PROTECT,
        related_name="deals",
        null=True,
        blank=True,
    )
    vehicles = models.ManyToManyField(Vehicle, blank=True, related_name="deals")
    contacts = models.ManyToManyField(Contact, blank=True, related_name="deals")

    date_entered = models.DateField()
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_period = models.CharField(max_length=20, default="month")
    security_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    insurance_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    governing_law = models.CharField(max_length=100, default="Delaware")

    class Meta:
        verbose_name = "Deal"
        verbose_name_plural = "Deals"
        ordering = ["-date_entered", "-id"]

    def save(self, *args, **kwargs):
        if self.deal_type_id is None:
            self.deal_type = DealType.get_default()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Deal #{self.id} — {self.date_entered} — {self.lease_officer.get_username()}"

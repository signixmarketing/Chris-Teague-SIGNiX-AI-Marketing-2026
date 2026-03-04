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

    # Plan 4: signer order and authentication for SIGNiX (null/empty = use template order and slot defaults)
    signer_order = models.JSONField(null=True, blank=True)
    signer_authentication = models.JSONField(null=True, blank=True)

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


# Default email content for SIGNiX SubmitDocument (Design 4.4, Plan 1).
DEFAULT_SIGNIX_EMAIL_CONTENT = (
    "Your documents for the Sample Application are available online for viewing and signing."
)


class SignixConfig(models.Model):
    """
    Single-record configuration for SIGNiX Flex API: credentials, submitter info,
    and settings. Used by the transaction packager when building SubmitDocument.
    Only one row is used (singleton via get_signix_config() in apps.deals.signix).
    """

    sponsor = models.CharField(max_length=255, blank=True)
    client = models.CharField(max_length=255, blank=True)
    user_id = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    workgroup = models.CharField(max_length=255, blank=True)

    demo_only = models.BooleanField(default=True)
    delete_documents_after_days = models.PositiveIntegerField(default=60)
    default_email_content = models.TextField(default=DEFAULT_SIGNIX_EMAIL_CONTENT)

    submitter_first_name = models.CharField(max_length=150, blank=True)
    submitter_middle_name = models.CharField(max_length=150, blank=True)
    submitter_last_name = models.CharField(max_length=150, blank=True)
    submitter_email = models.EmailField(max_length=254, blank=True)
    submitter_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "SIGNiX configuration"
        verbose_name_plural = "SIGNiX configurations"

    def __str__(self):
        if self.demo_only:
            return "SIGNiX Config (Webtest)"
        return "SIGNiX Config (Production)"


class SignatureTransaction(models.Model):
    """
    One record per submission to SIGNiX. Stores DocumentSetID, transaction_id,
    status, first signer's signing URL, and timestamps. Linked to Deal and
    DocumentSet. Used by Plan 6 orchestrator and Plans 8/9 UI.
    """

    STATUS_SUBMITTED = "Submitted"
    STATUS_IN_PROGRESS = "In Progress"
    STATUS_SUSPENDED = "Suspended"
    STATUS_COMPLETE = "Complete"
    STATUS_CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, STATUS_SUBMITTED),
        (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
        (STATUS_SUSPENDED, STATUS_SUSPENDED),
        (STATUS_COMPLETE, STATUS_COMPLETE),
        (STATUS_CANCELLED, STATUS_CANCELLED),
    ]

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="signature_transactions",
    )
    document_set = models.ForeignKey(
        "documents.DocumentSet",
        on_delete=models.CASCADE,
    )
    signix_document_set_id = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=36, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED,
    )
    first_signing_url = models.URLField(max_length=512, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Signature transaction"
        verbose_name_plural = "Signature transactions"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Deal #{self.deal_id} — {self.signix_document_set_id} — {self.status}"

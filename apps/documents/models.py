"""
Document Set, Document Instance, and Document Instance Version models.

A Document Set is attached to a Deal and contains documents generated from
templates. Each Document Instance is one document (from a Static or Dynamic
template); each has one or more Document Instance Versions (e.g. draft, signed).
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class DocumentSet(models.Model):
    """
    A set of documents generated for a Deal, linked to the Document Set Template
    used to create it.
    """

    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="document_sets",
        help_text="Deal this document set belongs to",
    )
    document_set_template = models.ForeignKey(
        "doctemplates.DocumentSetTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template used to create this set; SET_NULL if template is deleted",
    )

    class Meta:
        verbose_name = "Document set"
        verbose_name_plural = "Document sets"
        ordering = ["-id"]

    def __str__(self):
        return f"Document set for Deal #{self.deal_id}"


class DocumentInstance(models.Model):
    """
    One document in a Document Set (e.g. lease agreement or safety advisory),
    created from a Static or Dynamic template.
    """

    document_set = models.ForeignKey(
        DocumentSet,
        on_delete=models.CASCADE,
        related_name="instances",
        help_text="Parent document set",
    )
    order = models.PositiveIntegerField(
        help_text="1-based order within the set",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        help_text="StaticDocumentTemplate or DynamicDocumentTemplate",
    )
    object_id = models.PositiveIntegerField(
        help_text="PK of the source template",
    )
    source_document_template = GenericForeignKey("content_type", "object_id")
    template_type = models.CharField(
        max_length=20,
        help_text="Denormalized: 'static' or 'dynamic'",
    )

    class Meta:
        verbose_name = "Document instance"
        verbose_name_plural = "Document instances"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_set", "order"],
                name="documents_docinst_unique_order_per_set",
            )
        ]

    def __str__(self):
        return f"Document instance #{self.id} (order {self.order})"


class DocumentInstanceVersion(models.Model):
    """
    One version of a document (e.g. draft v1, draft v2, signed).
    """

    document_instance = models.ForeignKey(
        DocumentInstance,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="Parent document instance",
    )
    version_number = models.PositiveIntegerField(
        help_text="Sequential version (1, 2, 3, …)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        help_text="e.g. Draft, Submitted to SIGNiX, Final",
    )
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        help_text="PDF file",
        blank=True,
    )

    class Meta:
        verbose_name = "Document instance version"
        verbose_name_plural = "Document instance versions"
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_instance", "version_number"],
                name="documents_docver_unique_version_per_instance",
            )
        ]

    def __str__(self):
        return f"Version {self.version_number} of instance #{self.document_instance_id}"

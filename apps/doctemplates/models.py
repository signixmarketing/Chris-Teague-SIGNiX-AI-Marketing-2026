"""
Document template models.

- StaticDocumentTemplate: reusable PDFs with form fields (e.g., safety advisory).
- DynamicDocumentTemplate: HTML with DTL that produce populated documents.
- DocumentSetTemplate: ordered list of Static/Dynamic templates per Deal Type.
- DocumentSetTemplateItem: one template reference in a Document Set Template.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class StaticDocumentTemplate(models.Model):
    """
    A static document template: a PDF file with configurable form field definitions.

    Used as "required documents" in document sets. tagging_data holds
    form-field definitions for PDF form fields (signature, date, text).
    """

    ref_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier (e.g., ZoomJetPackSafetyAdvisory)",
    )
    description = models.CharField(
        max_length=200,
        help_text="Human-readable description",
    )
    file = models.FileField(
        upload_to="document_templates/static",
        help_text="PDF file",
    )
    tagging_type = models.CharField(
        max_length=50,
        default="pdf_fields",
        help_text="How the document is tagged; 'pdf_fields' for PDF form fields",
    )
    tagging_data = models.JSONField(
        default=list,
        help_text="Array of form-field definitions: tag_name, field_type, member_info_number, etc.",
    )

    class Meta:
        verbose_name = "Static document template"
        verbose_name_plural = "Static document templates"

    def __str__(self):
        return self.description or self.ref_id


class DocumentSetTemplate(models.Model):
    """
    A document set template: an ordered list of Static/Dynamic templates,
    associated with one Deal Type. Used when generating documents for a Deal.
    """

    deal_type = models.ForeignKey(
        "deals.DealType",
        on_delete=models.PROTECT,
        unique=True,
        help_text="Deal Type this set applies to (one set per type)",
    )
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Display name; if blank, deal type name is used",
    )

    class Meta:
        verbose_name = "Document set template"
        verbose_name_plural = "Document set templates"
        ordering = ["deal_type__name"]

    def __str__(self):
        return self.name or str(self.deal_type)


class DocumentSetTemplateItem(models.Model):
    """
    One template (Static or Dynamic) in a Document Set Template, with order.
    """

    document_set_template = models.ForeignKey(
        DocumentSetTemplate,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent document set template",
    )
    order = models.PositiveIntegerField(
        help_text="1-based order within the set",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="StaticDocumentTemplate or DynamicDocumentTemplate",
    )
    object_id = models.PositiveIntegerField(
        help_text="PK of the template",
    )
    template = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Document set template item"
        verbose_name_plural = "Document set template items"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_set_template", "order"],
                name="doctemplates_dstitem_unique_order_per_template",
            )
        ]


class DynamicDocumentTemplate(models.Model):
    """
    A dynamic document template: an HTML file with Django Template Language.

    Produces populated documents when combined with deal data. tagging_data
    holds text-tagging field definitions for SIGNiX (signature/date placement).
    mapping maps template variables to deal data sources.
    """

    ref_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier (e.g., ZoomJetPackLease)",
    )
    description = models.CharField(
        max_length=200,
        help_text="Human-readable description",
    )
    file = models.FileField(
        upload_to="document_templates/dynamic",
        help_text="HTML template file",
    )
    tagging_type = models.CharField(
        max_length=50,
        default="text_tagging",
        help_text="How the document is tagged; 'text_tagging' for SIGNiX anchor text",
    )
    tagging_data = models.JSONField(
        default=list,
        help_text="Array of text-tagging field definitions: tag_name, field_type, anchor_text, bounding_box, etc.",
    )
    mapping = models.JSONField(
        default=dict,
        help_text="Maps template variable names to {source, transform?, ...} per DESIGN-DOCS",
    )

    class Meta:
        verbose_name = "Dynamic document template"
        verbose_name_plural = "Dynamic document templates"

    def __str__(self):
        return self.description or self.ref_id

"""
Document template models.

- StaticDocumentTemplate: reusable PDFs with form fields (e.g., safety advisory).
- DynamicDocumentTemplate: HTML with DTL that produce populated documents.
"""

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

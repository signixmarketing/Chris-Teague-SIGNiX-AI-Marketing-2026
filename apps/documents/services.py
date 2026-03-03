"""
Document generation service.

Orchestration: generate_documents_for_deal, regenerate_documents (Batch 3).
Helpers: deal_has_sufficient_data, can_generate_documents, get_cannot_generate_reason.
Static path: _copy_static_template_to_version. Dynamic path: build_document_context, render_dynamic_template_to_pdf.
"""

import logging
import os
import shutil
import subprocess

import pdfkit
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max
from django.template import Context, Template

from apps.doctemplates.models import (
    DocumentSetTemplate,
    DynamicDocumentTemplate,
    StaticDocumentTemplate,
)
from apps.doctemplates.utils import apply_transform
from apps.schema.services import get_deal_data

from .exceptions import DocumentGenerationError
from .models import DocumentInstance, DocumentInstanceVersion, DocumentSet

logger = logging.getLogger(__name__)


def check_wkhtmltopdf_available():
    """
    Return True if wkhtmltopdf is installed and on PATH, False otherwise.

    Used before PDF conversion and by Django system checks.
    """
    wkhtmltopdf_path = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf_path:
        return False
    try:
        result = subprocess.run(
            [wkhtmltopdf_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError, Exception):
        return False


def _require_wkhtmltopdf():
    """Raise DocumentGenerationError if wkhtmltopdf is not available."""
    if not check_wkhtmltopdf_available():
        raise DocumentGenerationError(
            "wkhtmltopdf is not installed or not on PATH. "
            "Install it from https://wkhtmltopdf.org/ or via your package manager "
            "(e.g. apt install wkhtmltopdf, brew install wkhtmltopdf)."
        )


def deal_has_sufficient_data(deal):
    """
    Return True if the deal has all data required for document generation.

    Requires: all Deal fields have values (no blank required fields), at least
    one vehicle, at least one contact, and lease officer set.
    """
    if not deal.lease_officer_id:
        return False
    if not deal.date_entered or not deal.lease_start_date or not deal.lease_end_date:
        return False
    if deal.payment_amount is None:
        return False
    if not deal.vehicles.exists():
        return False
    if not deal.contacts.exists():
        return False
    return True


def can_generate_documents(deal):
    """
    Return True if document generation can be triggered for this deal.

    Requires sufficient data and a Document Set Template for the deal's Deal Type.
    """
    if not deal_has_sufficient_data(deal):
        return False
    if not deal.deal_type_id:
        return False
    return DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).exists()


def _get_cannot_generate_reason(deal):
    """Return user-facing reason why generation is disabled (for template display)."""
    if not deal_has_sufficient_data(deal):
        return "Create at least one vehicle and contact and ensure all deal fields are set."
    if not deal.deal_type_id:
        return "Deal type is not set."
    if not DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).exists():
        return "No document set template configured for this deal type."
    return None


def get_cannot_generate_reason(deal):
    """
    Return the reason generation is disabled, or None if it is allowed.

    Use when can_generate_documents(deal) is False to show the user why the button is disabled.
    """
    return _get_cannot_generate_reason(deal)


def _get_value_by_path(data, path):
    """
    Resolve a dot-separated path in the deal data structure (from get_deal_data).

    "deal.payment_amount" -> data["deal"]["payment_amount"].
    "deal.vehicles" -> list. "deal.vehicles.item.sku" -> first vehicle's sku (index 0).
    """
    if not path or not isinstance(path, str):
        return None
    parts = path.strip().split(".")
    if not parts or parts[0] != "deal":
        return None
    current = data.get("deal")
    if current is None:
        return None
    i = 1
    while i < len(parts):
        key = parts[i]
        if key == "item":
            # "deal.vehicles.item.sku" -> first element of list
            if isinstance(current, list) and len(current) > 0:
                current = current[0]
                i += 1
            else:
                return None
        elif isinstance(current, dict) and key in current:
            current = current[key]
            i += 1
        else:
            return None
    return current


def _set_nested(context, path, value):
    """Set context[part0][part1][...] = value for dot-separated path."""
    parts = path.strip().split(".")
    if not parts:
        return
    d = context
    for part in parts[:-1]:
        if part not in d:
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value


def build_document_context(deal, mapping, request=None):
    """
    Build template context from deal data and mapping.

    Uses get_deal_data(deal) only; applies transforms via apply_transform.
    Image sources (source starting with "image:") are resolved via Image model;
    value is absolute URL (request.build_absolute_uri when request present, else SITE_URL + path).
    Raises DocumentGenerationError if an Image is missing.
    """
    from apps.images.models import Image

    deal_data = get_deal_data(deal)
    context = {}
    if not mapping:
        return context
    base_url = None
    if request:
        base_url = request.build_absolute_uri("/")
    else:
        base_url = getattr(settings, "SITE_URL", "") or ""

    for var, entry in mapping.items():
        source = (entry.get("source") or "").strip()
        if not source:
            continue
        transform_name = (entry.get("transform") or "").strip() or None
        if source.startswith("image:"):
            uuid_str = source[6:].strip()
            try:
                image = Image.objects.get(uuid=uuid_str)
            except Image.DoesNotExist:
                raise DocumentGenerationError(
                    f"Image with UUID {uuid_str} is referenced in the template but no longer exists. "
                    "Please update the template mapping or restore the image."
                )
            url = image.file.url if image.file else ""
            if url and request:
                value = request.build_absolute_uri(url)
            elif url and base_url:
                value = base_url.rstrip("/") + ("/" + url.lstrip("/") if url.startswith("/") else url)
            else:
                value = url
            _set_nested(context, var, value)
        else:
            value = _get_value_by_path(deal_data, source)
            value = apply_transform(value, transform_name)
            _set_nested(context, var, value)
    return context


def render_dynamic_template_to_pdf(deal, dynamic_template, request=None):
    """
    Render the dynamic HTML template with deal context and convert to PDF.

    Returns PDF content as bytes. Raises on missing file, render error, or pdfkit failure.
    """
    _require_wkhtmltopdf()
    if not dynamic_template.file:
        raise DocumentGenerationError(
            f"Dynamic template '{getattr(dynamic_template, 'ref_id', '')}' has no HTML file."
        )
    mapping = dynamic_template.mapping or {}
    context_dict = build_document_context(deal, mapping, request)
    with dynamic_template.file.open("r") as f:
        html_string = f.read()
    template = Template(html_string)
    context = Context(context_dict)
    try:
        rendered_html = template.render(context)
    except Exception as e:
        logger.exception("DTL render failed for template pk=%s: %s", dynamic_template.pk, e)
        raise DocumentGenerationError(
            f"Template render failed: {e!s}"
        ) from e
    # wkhtmltopdf 0.12.6 does not support --base-url; omit it to avoid "Unknown long argument".
    # Image URLs in context are already absolute when request is present.
    pdf_options = {"enable-local-file-access": None}
    try:
        pdf_bytes = pdfkit.from_string(
            rendered_html,
            False,
            options=pdf_options,
        )
    except Exception as e:
        logger.exception("pdfkit failed for template pk=%s: %s", dynamic_template.pk, e)
        raise DocumentGenerationError(
            f"PDF conversion failed. Ensure wkhtmltopdf is installed. {e!s}"
        ) from e
    if pdf_bytes is None:
        raise DocumentGenerationError("PDF conversion produced no output.")
    return pdf_bytes


def _copy_static_template_to_version(static_template, document_instance, version_number=1):
    """
    Create a DocumentInstanceVersion for a Static template by copying its PDF.

    Assumes static_template is a StaticDocumentTemplate with a file.
    """
    if not static_template.file:
        raise DocumentGenerationError(
            f"Static template '{getattr(static_template, 'ref_id', '')}' has no file."
        )
    version = DocumentInstanceVersion(
        document_instance=document_instance,
        version_number=version_number,
        status="Draft",
    )
    version.save()
    name = os.path.basename(static_template.file.name) or "document.pdf"
    with static_template.file.open("rb") as src:
        version.file.save(name, src, save=True)
    return version


def _save_dynamic_pdf_to_version(document_instance, pdf_bytes, version_number=1, filename="document.pdf"):
    """Create a DocumentInstanceVersion and save PDF bytes to it."""
    version = DocumentInstanceVersion(
        document_instance=document_instance,
        version_number=version_number,
        status="Draft",
    )
    version.save()
    from django.core.files.base import ContentFile

    version.file.save(filename, ContentFile(pdf_bytes), save=True)
    return version


def generate_documents_for_deal(deal, request=None):
    """
    Create a Document Set for the deal from its Deal Type's Document Set Template.

    Processes both Static and Dynamic template items. Returns the created DocumentSet on success.
    Raises DocumentGenerationError on failure (insufficient data, no template, or processing error).
    """
    if not deal_has_sufficient_data(deal):
        raise DocumentGenerationError(
            "Deal does not have sufficient data. Add at least one vehicle and one contact, and ensure all required fields are set."
        )
    if not deal.deal_type_id:
        raise DocumentGenerationError("Deal has no deal type set.")
    template = DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).first()
    if not template:
        raise DocumentGenerationError(
            "No document set template configured for this deal type."
        )
    items = list(template.items.all().select_related("content_type"))
    static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
    dynamic_ct = ContentType.objects.get_for_model(DynamicDocumentTemplate)

    try:
        with transaction.atomic():
            document_set = DocumentSet.objects.create(
                deal=deal,
                document_set_template=template,
            )
            order = 1
            for item in items:
                tmpl = item.template
                if tmpl is None:
                    logger.warning(
                        "DocumentSetTemplateItem pk=%s has missing template; skipping",
                        item.pk,
                    )
                    continue
                if isinstance(tmpl, StaticDocumentTemplate):
                    doc_instance = DocumentInstance.objects.create(
                        document_set=document_set,
                        order=order,
                        content_type=static_ct,
                        object_id=tmpl.pk,
                        template_type="static",
                    )
                    _copy_static_template_to_version(tmpl, doc_instance)
                    order += 1
                elif isinstance(tmpl, DynamicDocumentTemplate):
                    pdf_bytes = render_dynamic_template_to_pdf(deal, tmpl, request=request)
                    doc_instance = DocumentInstance.objects.create(
                        document_set=document_set,
                        order=order,
                        content_type=dynamic_ct,
                        object_id=tmpl.pk,
                        template_type="dynamic",
                    )
                    name = (tmpl.ref_id or "dynamic") + ".pdf"
                    _save_dynamic_pdf_to_version(doc_instance, pdf_bytes, version_number=1, filename=name)
                    order += 1
            logger.info(
                "Created DocumentSet pk=%s for Deal pk=%s with %s instance(s)",
                document_set.pk,
                deal.pk,
                order - 1,
            )
            return document_set
    except DocumentGenerationError:
        raise
    except Exception as e:
        logger.exception("Document generation failed for Deal pk=%s: %s", deal.pk, e)
        raise DocumentGenerationError(
            "Document generation failed. Please try again or contact support."
        ) from e


def regenerate_documents(document_set, request=None):
    """
    Add new DocumentInstanceVersions to an existing Document Set.

    For each instance, creates a new version (version_number = next) with the same
    template (static copy or dynamic re-render). Returns the same DocumentSet on success.
    Raises DocumentGenerationError on failure.
    """
    deal = document_set.deal
    if not deal_has_sufficient_data(deal):
        raise DocumentGenerationError(
            "Deal does not have sufficient data. Add at least one vehicle and one contact, and ensure all required fields are set."
        )
    static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
    dynamic_ct = ContentType.objects.get_for_model(DynamicDocumentTemplate)
    instances = list(
        document_set.instances.select_related("content_type").prefetch_related("versions")
    )
    if not instances:
        logger.info("Regenerate: no instances in DocumentSet pk=%s", document_set.pk)
        return document_set

    try:
        with transaction.atomic():
            for doc_instance in instances:
                next_version = doc_instance.versions.aggregate(
                    mx=Max("version_number")
                ).get("mx") or 0
                next_version += 1
                if doc_instance.content_type_id == static_ct.id:
                    static_t = StaticDocumentTemplate.objects.get(pk=doc_instance.object_id)
                    _copy_static_template_to_version(
                        static_t, doc_instance, version_number=next_version
                    )
                elif doc_instance.content_type_id == dynamic_ct.id:
                    dynamic_t = DynamicDocumentTemplate.objects.get(pk=doc_instance.object_id)
                    pdf_bytes = render_dynamic_template_to_pdf(deal, dynamic_t, request=request)
                    name = (dynamic_t.ref_id or "dynamic") + ".pdf"
                    _save_dynamic_pdf_to_version(
                        doc_instance, pdf_bytes,
                        version_number=next_version,
                        filename=name,
                    )
            logger.info(
                "Regenerated DocumentSet pk=%s for Deal pk=%s (%s instance(s))",
                document_set.pk, deal.pk, len(instances),
            )
            return document_set
    except DocumentGenerationError:
        raise
    except Exception as e:
        logger.exception("Regenerate failed for DocumentSet pk=%s: %s", document_set.pk, e)
        raise DocumentGenerationError(
            "Document regeneration failed. Please try again or contact support."
        ) from e


def delete_document_set(document_set):
    """
    Delete the Document Set and optionally remove PDF files from storage.

    Cascade deletes instances and versions. Collects version file paths before
    deleting so we can remove files from disk after the DB delete.
    """
    file_paths = []
    for instance in document_set.instances.prefetch_related("versions"):
        for version in instance.versions.all():
            if version.file:
                try:
                    file_paths.append(version.file.path)
                except (ValueError, OSError):
                    pass
    document_set.delete()
    for path in file_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError as e:
            logger.warning("Could not delete PDF file %s: %s", path, e)

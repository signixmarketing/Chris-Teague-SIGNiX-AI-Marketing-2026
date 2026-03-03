"""
Views for the documents app.

Deal detail Documents section is rendered by the deal detail view (apps.deals).
Batch 4: Document Instance page (version list), View PDF (inline), Download PDF (attachment),
Send for Signature stub (deals app).
"""

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import DocumentInstance, DocumentInstanceVersion


@login_required
def document_version_view(request, pk):
    """Serve the PDF for viewing inline in the browser."""
    version = get_object_or_404(
        DocumentInstanceVersion.objects.select_related("document_instance__document_set__deal"),
        pk=pk,
    )
    if not version.file:
        raise Http404("This version has no file.")
    response = FileResponse(
        version.file.open("rb"),
        content_type="application/pdf",
        as_attachment=False,
    )
    response["Content-Disposition"] = 'inline; filename="document.pdf"'
    return response


@login_required
def document_version_download(request, pk):
    """Serve the PDF as an attachment (download)."""
    version = get_object_or_404(
        DocumentInstanceVersion.objects.select_related("document_instance__document_set__deal"),
        pk=pk,
    )
    if not version.file:
        raise Http404("This version has no file.")
    filename = version.file.name.split("/")[-1] if version.file.name else "document.pdf"
    response = FileResponse(
        version.file.open("rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=filename,
    )
    return response


@login_required
def document_instance_detail(request, pk):
    """List all versions for a document instance with View and Download links."""
    instance = get_object_or_404(
        DocumentInstance.objects.select_related("document_set__deal").prefetch_related(
            "versions"
        ),
        pk=pk,
    )
    versions = instance.versions.all()
    deal = instance.document_set.deal
    return render(
        request,
        "documents/document_instance_detail.html",
        {
            "instance": instance,
            "versions": versions,
            "deal": deal,
        },
    )

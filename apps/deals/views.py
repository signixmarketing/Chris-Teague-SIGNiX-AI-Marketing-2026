"""
Views for the deals app (list, add, edit, delete).

All views require login. Lease officer defaults to request.user on create.
Delete uses GET for confirmation page and POST to perform delete.
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.documents.exceptions import DocumentGenerationError
from apps.documents.services import (
    can_generate_documents,
    delete_document_set,
    generate_documents_for_deal,
    get_cannot_generate_reason,
    regenerate_documents,
)

from .forms import DealForm
from .models import Deal, DealType


def _deal_detail_context(deal, document_set, can_generate):
    """Build context for deal detail template."""
    return {
        "deal": deal,
        "document_set": document_set,
        "can_generate": can_generate,
        "cannot_generate_reason": None if can_generate else get_cannot_generate_reason(deal),
    }


@login_required
def deal_detail(request, pk):
    """Show read-only deal summary including deal type; Edit and Delete buttons; Documents section."""
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    can_generate = can_generate_documents(deal)
    return render(
        request,
        "deals/deal_detail.html",
        _deal_detail_context(deal, document_set, can_generate),
    )


@login_required
def deal_generate_documents(request, pk):
    """POST: run document generation for the deal; redirect to deal detail or show error."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    try:
        generate_documents_for_deal(deal, request=request)
        messages.success(request, "Documents generated.")
        return redirect("deals:deal_detail", pk=pk)
    except DocumentGenerationError as e:
        messages.error(request, str(e))
        document_set = deal.document_sets.first()
        can_generate = can_generate_documents(deal)
        return render(
            request,
            "deals/deal_detail.html",
            _deal_detail_context(deal, document_set, can_generate),
        )


@login_required
def deal_regenerate_documents(request, pk):
    """POST: regenerate document set (new versions); redirect to deal detail or show error."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    if not document_set:
        messages.error(request, "No document set to regenerate.")
        return redirect("deals:deal_detail", pk=pk)
    try:
        regenerate_documents(document_set, request=request)
        messages.success(request, "Documents regenerated.")
        return redirect("deals:deal_detail", pk=pk)
    except DocumentGenerationError as e:
        messages.error(request, str(e))
        can_generate = can_generate_documents(deal)
        return render(
            request,
            "deals/deal_detail.html",
            _deal_detail_context(deal, document_set, can_generate),
        )


@login_required
def deal_delete_document_set(request, pk):
    """POST: delete the deal's document set and redirect to deal detail."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    if not document_set:
        messages.error(request, "No document set to delete.")
        return redirect("deals:deal_detail", pk=pk)
    try:
        delete_document_set(document_set)
        messages.success(request, "Document set deleted.")
    except DocumentGenerationError as e:
        messages.error(request, str(e))
    return redirect("deals:deal_detail", pk=pk)


@login_required
def deal_send_for_signature_stub(request, pk):
    """Stub: show message that SIGNiX integration is coming; redirect back to deal detail."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    get_object_or_404(Deal, pk=pk)
    messages.info(request, "SIGNiX integration will be available in a future release.")
    return redirect("deals:deal_detail", pk=pk)


@login_required
def deal_list(request):
    """List all deals (date entered, lease officer, dates, payment, vehicles/contacts count)."""
    deals = Deal.objects.all().select_related(
        "lease_officer", "deal_type"
    ).prefetch_related("vehicles", "contacts")
    return render(request, "deals/deal_list.html", {"deal_list": deals})


@login_required
def deal_add(request):
    """Show form to add a deal; on valid POST create with lease_officer=request.user."""
    if request.method == "POST":
        form = DealForm(request.POST)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.lease_officer = request.user
            deal.deal_type = DealType.get_default()
            deal.save()
            form.save_m2m()
            messages.success(request, "Deal added.")
            return redirect("deals:deal_list")
    else:
        form = DealForm()
    return render(
        request,
        "deals/deal_form.html",
        {"form": form, "lease_officer": request.user, "is_edit": False},
    )


@login_required
def deal_edit(request, pk):
    """Show form to edit a deal; on valid POST update and redirect to list."""
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == "POST":
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            form.save()
            messages.success(request, "Deal updated.")
            return redirect("deals:deal_list")
    else:
        form = DealForm(instance=deal)
    return render(
        request,
        "deals/deal_form.html",
        {"form": form, "deal": deal, "lease_officer": deal.lease_officer, "is_edit": True},
    )


@login_required
def deal_delete_confirm(request, pk):
    """GET: show confirmation page. POST: delete deal and redirect to list."""
    deal = get_object_or_404(Deal.objects.select_related("lease_officer"), pk=pk)
    if request.method == "POST":
        deal.delete()
        messages.success(request, "Deal deleted.")
        return redirect("deals:deal_list")
    return render(request, "deals/deal_confirm_delete.html", {"deal": deal})

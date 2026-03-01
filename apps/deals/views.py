"""
Views for the deals app (list, add, edit, delete).

All views require login. Lease officer defaults to request.user on create.
Delete uses GET for confirmation page and POST to perform delete.
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DealForm
from .models import Deal, DealType


@login_required
def deal_detail(request, pk):
    """Show read-only deal summary including deal type; Edit and Delete buttons."""
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts"
        ),
        pk=pk,
    )
    return render(request, "deals/deal_detail.html", {"deal": deal})


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

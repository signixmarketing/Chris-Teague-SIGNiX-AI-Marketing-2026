"""
Views for schema app.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.deals.models import Deal

from .services import get_deal_data, get_schema


@login_required
@require_GET
def schema_view(request):
    """Schema viewer page — displays the deal-centric data schema."""
    schema = get_schema()
    return render(request, "schema/schema_view.html", {"schema": schema})


@login_required
@require_GET
def debug_data_list(request):
    """Debug Data page — list of deals with View JSON button per row."""
    deals = Deal.objects.all().select_related(
        "lease_officer", "deal_type"
    ).prefetch_related("vehicles", "contacts").order_by("-date_entered")
    return render(request, "schema/debug_data_list.html", {"deal_list": deals})


@login_required
@require_GET
def deal_data_json(request, pk):
    """Return get_deal_data(deal) as JSON. 404 if deal not found."""
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts"
        ),
        pk=pk,
    )
    data = get_deal_data(deal)
    return JsonResponse(data)

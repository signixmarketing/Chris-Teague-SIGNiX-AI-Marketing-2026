"""
Views for the vehicles app (list, add, edit, delete).

All views require login. Delete uses GET for confirmation page and POST to perform delete.
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import VehicleForm
from .models import Vehicle


@login_required
def vehicle_list(request):
    """List all vehicles in a table (SKU, Year, JPIN, Actions)."""
    vehicles = Vehicle.objects.all().order_by("sku")
    return render(request, "vehicles/vehicle_list.html", {"vehicle_list": vehicles})


@login_required
def vehicle_add(request):
    """Show form to add a vehicle; on valid POST create and redirect to list."""
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle added.")
            return redirect("vehicles:vehicle_list")
    else:
        form = VehicleForm()
    return render(request, "vehicles/vehicle_form.html", {"form": form, "is_edit": False})


@login_required
def vehicle_edit(request, pk):
    """Show form to edit a vehicle; on valid POST update and redirect to list."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated.")
            return redirect("vehicles:vehicle_list")
    else:
        form = VehicleForm(instance=vehicle)
    return render(
        request,
        "vehicles/vehicle_form.html",
        {"form": form, "vehicle": vehicle, "is_edit": True},
    )


@login_required
def vehicle_delete_confirm(request, pk):
    """GET: show confirmation page. POST: delete vehicle and redirect to list."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "Vehicle deleted.")
        return redirect("vehicles:vehicle_list")
    return render(request, "vehicles/vehicle_confirm_delete.html", {"vehicle": vehicle})

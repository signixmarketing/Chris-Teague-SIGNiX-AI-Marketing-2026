"""
Django admin for vehicles.

Vehicle is registered for backup management from the admin.
"""

from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["sku", "year", "jpin"]
    list_filter = ["year"]
    search_fields = ["sku", "jpin"]
    ordering = ["sku"]

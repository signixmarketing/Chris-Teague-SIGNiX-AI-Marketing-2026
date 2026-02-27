"""
Django admin for deals.

Deal is registered for backup management from the admin.
"""

from django.contrib import admin

from .models import Deal


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date_entered",
        "lease_officer",
        "lease_start_date",
        "lease_end_date",
        "payment_amount",
        "payment_period",
        "vehicles_count",
        "contacts_count",
    ]
    list_filter = ["date_entered", "lease_officer", "governing_law"]
    search_fields = ["lease_officer__username", "governing_law"]
    filter_horizontal = ["vehicles", "contacts"]
    ordering = ["-date_entered", "-id"]
    readonly_fields = []

    def vehicles_count(self, obj):
        return obj.vehicles.count()

    vehicles_count.short_description = "Vehicles"

    def contacts_count(self, obj):
        return obj.contacts.count()

    contacts_count.short_description = "Contacts"

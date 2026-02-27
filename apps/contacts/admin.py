"""
Django admin for contacts.

Contact is registered for backup management from the admin.
"""

from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["first_name", "middle_name", "last_name", "email", "phone_number"]
    list_filter = ["last_name"]
    search_fields = ["first_name", "middle_name", "last_name", "email"]
    ordering = ["last_name", "first_name"]

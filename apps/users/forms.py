"""
Forms for the users app.

LeaseOfficerProfileEditForm: edit first_name, last_name, phone_number, email, timezone.
full_name is read-only (computed from first + last).
"""

from django import forms

from .models import LeaseOfficerProfile


class LeaseOfficerProfileEditForm(forms.ModelForm):
    """Form to update a lease officer's profile (excluding user and full_name)."""

    class Meta:
        model = LeaseOfficerProfile
        fields = ["first_name", "last_name", "phone_number", "email", "timezone"]

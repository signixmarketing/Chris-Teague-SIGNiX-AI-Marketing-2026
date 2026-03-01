"""
Forms for the deals app.

DealForm: add/edit deal (properties + vehicles + contacts).
Lease officer and deal_type are set in the view (current user and default type on create).
"""

from django import forms

from .models import Deal


class DealForm(forms.ModelForm):
    """Form to create or update a deal; vehicles and contacts are multi-select."""

    class Meta:
        model = Deal
        fields = [
            "date_entered",
            "lease_start_date",
            "lease_end_date",
            "payment_amount",
            "payment_period",
            "security_deposit",
            "insurance_amount",
            "governing_law",
            "vehicles",
            "contacts",
        ]
        widgets = {
            "date_entered": forms.DateInput(attrs={"type": "date"}),
            "lease_start_date": forms.DateInput(attrs={"type": "date"}),
            "lease_end_date": forms.DateInput(attrs={"type": "date"}),
            "vehicles": forms.CheckboxSelectMultiple,
            "contacts": forms.CheckboxSelectMultiple,
        }

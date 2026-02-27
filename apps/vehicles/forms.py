"""
Forms for the vehicles app.

VehicleForm: add/edit vehicle (sku, year, jpin).
"""

from django import forms

from .models import Vehicle


class VehicleForm(forms.ModelForm):
    """Form to create or update a vehicle (sku, year, jpin)."""

    class Meta:
        model = Vehicle
        fields = ["sku", "year", "jpin"]

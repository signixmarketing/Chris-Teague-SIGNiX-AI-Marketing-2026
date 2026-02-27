"""
Forms for the contacts app.

ContactForm: add/edit contact (first_name, middle_name, last_name, email, phone_number).
"""

from django import forms

from .models import Contact


class ContactForm(forms.ModelForm):
    """Form to create or update a contact; middle_name is optional."""

    class Meta:
        model = Contact
        fields = ["first_name", "middle_name", "last_name", "email", "phone_number"]

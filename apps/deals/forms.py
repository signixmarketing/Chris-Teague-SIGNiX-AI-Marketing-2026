"""
Forms for the deals app.

DealForm: add/edit deal (properties + vehicles + contacts).
Lease officer and deal_type are set in the view (current user and default type on create).
"""

from django import forms

from .models import Deal, SignixConfig


class SignixConfigForm(forms.ModelForm):
    """Form to edit the single SignixConfig (credentials, submitter, settings)."""

    class Meta:
        model = SignixConfig
        fields = [
            "sponsor",
            "client",
            "user_id",
            "password",
            "workgroup",
            "push_base_url",
            "demo_only",
            "delete_documents_after_days",
            "default_email_content",
            "submitter_first_name",
            "submitter_middle_name",
            "submitter_last_name",
            "submitter_email",
            "submitter_phone",
        ]
        widgets = {
            "password": forms.PasswordInput(attrs={"autocomplete": "new-password"}, render_value=True),
            "push_base_url": forms.URLInput(attrs={"placeholder": "https://your-app.example.com"}),
            "default_email_content": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != "demo_only":
                self.fields[field].widget.attrs.setdefault("class", "form-control")
            else:
                self.fields[field].widget.attrs.setdefault("class", "form-check-input")
        # Password required only when creating or when current password is empty
        if self.instance and self.instance.pk and self.instance.password:
            self.fields["password"].required = False
            self.fields["password"].help_text = "Leave blank to keep existing password."
        self.fields["push_base_url"].required = False
        self.fields["push_base_url"].help_text = (
            "Optional override. When blank, the app uses the current site URL "
            "or SIGNIX_PUSH_BASE_URL / NGROK_DOMAIN."
        )

    def clean(self):
        cleaned = super().clean()
        # Require all five credentials when saving
        for key in ("sponsor", "client", "user_id", "workgroup"):
            if not cleaned.get(key):
                self.add_error(key, "This field is required.")
        if not cleaned.get("password") and not (self.instance and self.instance.pk and self.instance.password):
            self.add_error("password", "This field is required.")
        if not cleaned.get("submitter_email"):
            self.add_error("submitter_email", "This field is required.")
        return cleaned


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

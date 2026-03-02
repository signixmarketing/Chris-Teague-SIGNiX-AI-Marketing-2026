"""
Forms for document templates.

Static: StaticDocumentTemplateForm, TaggingFieldFormSet.
Dynamic: DynamicDocumentTemplateForm, DynamicTaggingFieldFormSet.
"""

from django import forms
from django.forms import formset_factory

from .models import StaticDocumentTemplate, DynamicDocumentTemplate


def _ref_id_exists_in_static(ref_id, exclude_pk=None):
    qs = StaticDocumentTemplate.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.filter(ref_id=ref_id).exists()


def _ref_id_exists_in_dynamic(ref_id, exclude_pk=None):
    qs = DynamicDocumentTemplate.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.filter(ref_id=ref_id).exists()


class StaticDocumentTemplateForm(forms.ModelForm):
    """Form for static template metadata: ref_id, description, file."""

    class Meta:
        model = StaticDocumentTemplate
        fields = ["ref_id", "description", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # File required on add, optional on edit
        if self.instance and self.instance.pk:
            self.fields["file"].required = False

    def clean_ref_id(self):
        ref_id = self.cleaned_data.get("ref_id")
        if not ref_id:
            return ref_id
        if _ref_id_exists_in_static(ref_id, exclude_pk=getattr(self.instance, "pk", None)):
            raise forms.ValidationError("A template with this ref_id already exists.")
        if _ref_id_exists_in_dynamic(ref_id):
            raise forms.ValidationError("A template with this ref_id already exists.")
        return ref_id

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file
        # Validate PDF
        name = getattr(file, "name", "")
        content_type = getattr(file, "content_type", "")
        if not (name.lower().endswith(".pdf") or content_type == "application/pdf"):
            raise forms.ValidationError("File must be a PDF.")
        return file


FIELD_TYPE_CHOICES = [
    ("", "---------"),
    ("signature", "Signature"),
    ("date", "Date"),
    ("text", "Text"),
]

MEMBER_INFO_CHOICES = [
    ("", "---------"),
    (1, "User (lease officer)"),
    (2, "Contact"),
]


class TaggingFieldForm(forms.Form):
    """Single form field definition for tagging_data."""

    tag_name = forms.CharField(max_length=100, required=False, label="Tag name")
    field_type = forms.ChoiceField(
        choices=FIELD_TYPE_CHOICES,
        required=False,
        label="Field type",
    )
    member_info_number = forms.TypedChoiceField(
        choices=MEMBER_INFO_CHOICES,
        coerce=lambda x: int(x) if x else None,
        required=False,
        empty_value=None,
        label="Signer",
    )
    date_signed_field_name = forms.CharField(max_length=100, required=False, label="Date signed field name")
    date_signed_format = forms.CharField(max_length=20, required=False, label="Date signed format")

    def clean(self):
        cleaned = super().clean()
        field_type = cleaned.get("field_type")
        if field_type == "signature":
            if not cleaned.get("date_signed_field_name"):
                self.add_error("date_signed_field_name", "Required when field type is signature.")
            if not cleaned.get("date_signed_format"):
                self.add_error("date_signed_format", "Required when field type is signature.")
        return cleaned


TaggingFieldFormSet = formset_factory(
    TaggingFieldForm,
    extra=3,
    min_num=0,
    validate_min=True,
)


def tagging_data_to_formset_initial(tagging_data):
    """Convert tagging_data (list of dicts) to formset initial data."""
    if not tagging_data or not isinstance(tagging_data, list):
        return []
    initial = []
    for item in tagging_data:
        if not isinstance(item, dict):
            continue
        initial.append({
            "tag_name": item.get("tag_name", ""),
            "field_type": item.get("field_type", ""),
            "member_info_number": item.get("member_info_number"),
            "date_signed_field_name": item.get("date_signed_field_name", ""),
            "date_signed_format": item.get("date_signed_format", ""),
        })
    return initial


def formset_data_to_tagging_data(cleaned_data_list):
    """
    Convert formset cleaned_data to tagging_data (list of dicts).
    Skips fully empty rows.
    """
    result = []
    for row in cleaned_data_list:
        tag_name = row.get("tag_name", "").strip()
        field_type = row.get("field_type", "")
        if not tag_name and not field_type:
            continue
        item = {
            "tag_name": tag_name or "",
            "field_type": field_type or "text",
            "member_info_number": row.get("member_info_number") or 2,
        }
        if field_type == "signature":
            item["date_signed_field_name"] = (row.get("date_signed_field_name") or "").strip()
            item["date_signed_format"] = (row.get("date_signed_format") or "").strip()
        result.append(item)
    return result


# Alias for plan compatibility
tagging_data_to_formset_data = tagging_data_to_formset_initial


# --- Dynamic template forms ---


class DynamicDocumentTemplateForm(forms.ModelForm):
    """Form for dynamic template metadata: ref_id, description, file (HTML)."""

    class Meta:
        model = DynamicDocumentTemplate
        fields = ["ref_id", "description", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["file"].required = False

    def clean_ref_id(self):
        ref_id = self.cleaned_data.get("ref_id")
        if not ref_id:
            return ref_id
        if _ref_id_exists_in_static(ref_id):
            raise forms.ValidationError("A template with this ref_id already exists.")
        if _ref_id_exists_in_dynamic(ref_id, exclude_pk=getattr(self.instance, "pk", None)):
            raise forms.ValidationError("A template with this ref_id already exists.")
        return ref_id

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file
        name = getattr(file, "name", "")
        content_type = getattr(file, "content_type", "")
        ok = (
            name.lower().endswith(".html")
            or name.lower().endswith(".htm")
            or content_type in ("text/html", "application/xhtml+xml")
        )
        if not ok:
            raise forms.ValidationError("File must be HTML.")
        return file


DYNAMIC_FIELD_TYPE_CHOICES = [
    ("", "---------"),
    ("date_signed", "Date signed"),
    ("signature", "Signature"),
]

IS_REQUIRED_CHOICES = [
    ("", "---------"),
    ("yes", "Yes"),
    ("no", "No"),
]


class DynamicTaggingFieldForm(forms.Form):
    """Single text-tagging field definition for dynamic template tagging_data."""

    tag_name = forms.CharField(max_length=100, required=False, label="Tag name")
    field_type = forms.ChoiceField(
        choices=DYNAMIC_FIELD_TYPE_CHOICES,
        required=False,
        label="Field type",
    )
    is_required = forms.ChoiceField(
        choices=IS_REQUIRED_CHOICES,
        required=False,
        label="Required",
    )
    anchor_text = forms.CharField(max_length=200, required=False, label="Anchor text")
    x_offset = forms.IntegerField(required=False, label="X offset", min_value=0, initial=0)
    y_offset = forms.IntegerField(required=False, label="Y offset", min_value=0, initial=0)
    width = forms.IntegerField(required=False, label="Width", min_value=1, initial=90)
    height = forms.IntegerField(required=False, label="Height", min_value=1, initial=12)
    member_info_number = forms.TypedChoiceField(
        choices=MEMBER_INFO_CHOICES,
        coerce=lambda x: int(x) if x else None,
        required=False,
        empty_value=None,
        label="Signer",
    )
    date_signed_field_name = forms.CharField(
        max_length=100, required=False, label="Date signed field name"
    )
    date_signed_format = forms.CharField(
        max_length=20, required=False, label="Date signed format"
    )

    def clean(self):
        cleaned = super().clean()
        field_type = cleaned.get("field_type")
        if field_type == "signature":
            if not cleaned.get("date_signed_field_name"):
                self.add_error(
                    "date_signed_field_name",
                    "Required when field type is signature.",
                )
            if not cleaned.get("date_signed_format"):
                self.add_error(
                    "date_signed_format",
                    "Required when field type is signature.",
                )
        return cleaned


DynamicTaggingFieldFormSet = formset_factory(
    DynamicTaggingFieldForm,
    extra=3,
    min_num=0,
    validate_min=True,
)


def dynamic_tagging_data_to_formset_initial(tagging_data):
    """Convert tagging_data (list of dicts) to formset initial data."""
    if not tagging_data or not isinstance(tagging_data, list):
        return []
    initial = []
    for item in tagging_data:
        if not isinstance(item, dict):
            continue
        bbox = item.get("bounding_box") or {}
        initial.append({
            "tag_name": item.get("tag_name", ""),
            "field_type": item.get("field_type", ""),
            "is_required": item.get("is_required", ""),
            "anchor_text": item.get("anchor_text", ""),
            "x_offset": bbox.get("x_offset", 0),
            "y_offset": bbox.get("y_offset", 0),
            "width": bbox.get("width", 90),
            "height": bbox.get("height", 12),
            "member_info_number": item.get("member_info_number"),
            "date_signed_field_name": item.get("date_signed_field_name", ""),
            "date_signed_format": item.get("date_signed_format", ""),
        })
    return initial


def dynamic_formset_cleaned_to_tagging_data(cleaned_data_list):
    """Convert formset cleaned_data to tagging_data (list of dicts). Skips empty rows."""
    result = []
    for row in cleaned_data_list:
        tag_name = (row.get("tag_name") or "").strip()
        field_type = row.get("field_type") or ""
        if not tag_name and not field_type:
            continue
        item = {
            "tag_name": tag_name or "",
            "field_type": field_type or "date_signed",
            "is_required": row.get("is_required") or "yes",
            "anchor_text": (row.get("anchor_text") or "").strip(),
            "bounding_box": {
                "x_offset": row.get("x_offset") or 0,
                "y_offset": row.get("y_offset") or 0,
                "width": row.get("width") or 90,
                "height": row.get("height") or 12,
            },
        }
        if field_type == "signature":
            item["member_info_number"] = row.get("member_info_number") or 2
            item["date_signed_field_name"] = (
                row.get("date_signed_field_name") or ""
            ).strip()
            item["date_signed_format"] = (
                row.get("date_signed_format") or ""
            ).strip()
        result.append(item)
    return result

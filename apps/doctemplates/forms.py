"""
Forms for document templates.

Static: StaticDocumentTemplateForm, TaggingFieldFormSet.
Dynamic: DynamicDocumentTemplateForm, DynamicTaggingFieldFormSet.
Document Set: DocumentSetTemplateForm, DocumentSetTemplateItemFormSet,
  get_document_template_choices, items_to_formset_initial, formset_to_items.
"""

from django import forms
from django.forms import formset_factory

from .models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
    DynamicDocumentTemplate,
)


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


# --- Document Set Template forms ---


def get_document_template_choices():
    """
    Return combined choices for Static and Dynamic templates for doc set item dropdown.

    Value format: "static-<pk>" or "dynamic-<pk>". Label: "{ref_id} (Static)" or
    "{ref_id} (Dynamic)". Ordered by ref_id for consistency.
    """
    static = [
        (f"static-{t.pk}", f"{t.ref_id} (Static)")
        for t in StaticDocumentTemplate.objects.all().order_by("ref_id")
    ]
    dynamic = [
        (f"dynamic-{t.pk}", f"{t.ref_id} (Dynamic)")
        for t in DynamicDocumentTemplate.objects.all().order_by("ref_id")
    ]
    return static + dynamic


def items_to_formset_initial(items):
    """
    Convert DocumentSetTemplateItem queryset/list to formset initial data.

    Returns list of dicts with key "template_choice" (value "static-<pk>" or
    "dynamic-<pk>"). Items should be ordered by order field.
    """
    from django.contrib.contenttypes.models import ContentType

    if not items:
        return []
    static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
    dynamic_ct = ContentType.objects.get_for_model(DynamicDocumentTemplate)
    initial = []
    for item in items:
        if item.content_type_id == static_ct.id:
            value = f"static-{item.object_id}"
        elif item.content_type_id == dynamic_ct.id:
            value = f"dynamic-{item.object_id}"
        else:
            continue
        initial.append({"template_choice": value})
    return initial


def formset_to_items(cleaned_data_list, document_set_template):
    """
    Convert formset cleaned_data to unsaved DocumentSetTemplateItem instances.

    Skips empty rows (blank template_choice). Order is 1-based from position.
    Caller should delete existing items and bulk_create or save each.
    """
    from django.contrib.contenttypes.models import ContentType

    static_ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
    dynamic_ct = ContentType.objects.get_for_model(DynamicDocumentTemplate)
    result = []
    for order, row in enumerate(cleaned_data_list, start=1):
        raw = (row.get("template_choice") or "").strip()
        if not raw:
            continue
        if raw.startswith("static-"):
            try:
                pk = int(raw.replace("static-", "", 1))
                result.append(
                    DocumentSetTemplateItem(
                        document_set_template=document_set_template,
                        order=order,
                        content_type=static_ct,
                        object_id=pk,
                    )
                )
            except ValueError:
                continue
        elif raw.startswith("dynamic-"):
            try:
                pk = int(raw.replace("dynamic-", "", 1))
                result.append(
                    DocumentSetTemplateItem(
                        document_set_template=document_set_template,
                        order=order,
                        content_type=dynamic_ct,
                        object_id=pk,
                    )
                )
            except ValueError:
                continue
    return result


def _deal_types_without_doc_set_template():
    """Deal types that do not yet have a Document Set Template."""
    from apps.deals.models import DealType

    used_ids = DocumentSetTemplate.objects.values_list("deal_type_id", flat=True)
    return DealType.objects.exclude(id__in=used_ids)


class DocumentSetTemplateForm(forms.ModelForm):
    """Form for document set template: deal_type and name."""

    class Meta:
        model = DocumentSetTemplate
        fields = ["deal_type", "name"]

    def __init__(self, *args, **kwargs):
        self.for_add = kwargs.pop("for_add", None)
        super().__init__(*args, **kwargs)
        if self.for_add is None:
            self.for_add = not (self.instance and self.instance.pk)
        if self.for_add:
            self.fields["deal_type"].queryset = _deal_types_without_doc_set_template()
        else:
            self.fields["deal_type"].disabled = True
        self.fields["name"].required = False

    def save(self, commit=True):
        if not self.for_add and self.instance and self.instance.pk:
            # Edit: do not overwrite deal_type (disabled field is not in cleaned_data)
            self.instance.name = self.cleaned_data.get("name", "")
            if commit:
                self.instance.save()
            return self.instance
        return super().save(commit=commit)


class DocumentSetTemplateItemForm(forms.Form):
    """Single row: template choice (Static or Dynamic)."""

    template_choice = forms.ChoiceField(
        choices=[],
        required=False,
        label="Template",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template_choice"].choices = [("", "---------")] + get_document_template_choices()


class BaseDocumentSetTemplateItemFormSet(forms.BaseFormSet):
    """Validate at least one item and no duplicate template choices."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        choices = []
        for form in self.forms:
            val = form.cleaned_data.get("template_choice") if form.cleaned_data else None
            if val:
                choices.append(val)
        if len(choices) != len(set(choices)):
            raise forms.ValidationError("Duplicate templates are not allowed.")


DocumentSetTemplateItemFormSet = formset_factory(
    DocumentSetTemplateItemForm,
    formset=BaseDocumentSetTemplateItemFormSet,
    extra=2,
    min_num=1,
    validate_min=True,
)

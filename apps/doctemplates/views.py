"""
Views for document templates app.

Static: full CRUD for StaticDocumentTemplate (list, add, edit, delete).
Dynamic: full CRUD for DynamicDocumentTemplate (Batch 2).
"""

import os

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    StaticDocumentTemplateForm,
    TaggingFieldFormSet,
    formset_data_to_tagging_data,
    tagging_data_to_formset_initial,
    DynamicDocumentTemplateForm,
    DynamicTaggingFieldFormSet,
    dynamic_formset_cleaned_to_tagging_data,
    dynamic_tagging_data_to_formset_initial,
)
from .models import StaticDocumentTemplate, DynamicDocumentTemplate
from .utils import (
    augment_mapping_with_var_type,
    get_image_sources_for_mapping,
    parse_dtl_variables_with_metadata,
    parse_mapping_from_post,
    validate_mapping_complete,
)
from django.template.exceptions import TemplateSyntaxError

from apps.schema.services import get_paths_grouped_for_mapping


def _data_paths_grouped_with_images():
    """Return get_paths_grouped_for_mapping with Images optgroup appended."""
    grouped = list(get_paths_grouped_for_mapping())
    image_options = get_image_sources_for_mapping()
    if image_options:
        grouped.append(("Images", image_options))
    return grouped

FORMSET_PREFIX = "tagging"
TRANSFORM_CHOICES = [
    ("", "(none)"),
    ("date_day", "date_day"),
    ("date_month", "date_month"),
    ("date_year", "date_year"),
    ("date_month_day", "date_month_day"),
    ("count", "count"),
    ("number_to_word", "number_to_word"),
    ("plural_suffix", "plural_suffix"),
]
DYNAMIC_FORMSET_PREFIX = "dynamic_tagging"


def _build_mapping_rows(
    parsed_variables,
    existing_mapping,
    data_paths_grouped,
    list_variables=None,
    list_item_variables=None,
    data_source_variables=None,
    list_item_to_list=None,
    image_variables=None,
):
    """Build list of {var, form_key, source, transform, var_type, list_item_of} for template."""
    from .utils import _var_to_form_key

    list_vars = frozenset(list_variables or [])
    list_item_vars = frozenset(list_item_variables or [])
    data_src = frozenset(data_source_variables or [])
    image_vars = frozenset(image_variables or [])
    item_to_list = dict(list_item_to_list or {})
    rows = []
    for var in parsed_variables:
        m = existing_mapping.get(var, {})
        if var in data_src:
            var_type = "data_source"
            list_item_of = None
        elif var in list_vars:
            var_type = "list"
            list_item_of = None
        elif var in list_item_vars:
            var_type = "list_item"
            list_item_of = item_to_list.get(var)
        elif var in image_vars:
            var_type = "image"
            list_item_of = None
        else:
            var_type = "scalar"
            list_item_of = None
        rows.append({
            "var": var,
            "form_key": _var_to_form_key(var),
            "source": m.get("source", ""),
            "transform": m.get("transform", ""),
            "var_type": var_type,
            "list_item_of": list_item_of,
        })
    return rows


def _build_template_structure_summary(
    data_source_variables,
    list_variables,
    list_item_to_list,
    scalar_variables,
    image_variables=None,
):
    """Build structured summary for 'Template expects' display."""
    data_src = sorted(data_source_variables or [])
    lists_data = []
    for list_var in sorted(list_variables or []):
        items = sorted(k for k, v in (list_item_to_list or {}).items() if v == list_var)
        lists_data.append({"name": list_var, "items": items})
    scalars = sorted(scalar_variables or [])
    image_vars = sorted(image_variables or [])
    return {
        "primary_data_source": data_src,
        "lists": lists_data,
        "scalar_properties": scalars,
        "image_variables": image_vars,
    }


def _remove_file_from_disk(file_field):
    """Remove file from disk if it exists."""
    if not file_field:
        return
    path = getattr(file_field, "path", None)
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


# --- Dynamic template views ---


@login_required
def dynamic_doctemplate_list(request):
    """List all dynamic document templates."""
    templates = DynamicDocumentTemplate.objects.all().order_by("ref_id")
    return render(
        request,
        "doctemplates/dynamic_doctemplate_list.html",
        {"template_list": templates},
    )


@login_required
def dynamic_doctemplate_add(request):
    """Add a new dynamic document template."""
    data_paths_grouped = _data_paths_grouped_with_images()
    if request.method == "POST":
        form = DynamicDocumentTemplateForm(request.POST, request.FILES)
        formset = DynamicTaggingFieldFormSet(
            request.POST, prefix=DYNAMIC_FORMSET_PREFIX
        )
        parsed_variables = []
        list_variables = []
        list_item_variables = []
        data_source_variables = []
        list_item_to_list = {}
        image_variables = []
        mapping = {}
        file_for_parse = request.FILES.get("file")
        if file_for_parse:
            try:
                content = file_for_parse.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
                (
                    parsed_variables,
                    list_variables,
                    list_item_variables,
                    data_source_variables,
                    list_item_to_list,
                    image_variables,
                ) = parse_dtl_variables_with_metadata(content)
                file_for_parse.seek(0)
            except (TemplateSyntaxError, UnicodeDecodeError):
                pass
        if parsed_variables:
            mapping = parse_mapping_from_post(request.POST, parsed_variables)
        if form.is_valid() and formset.is_valid():
            unmapped = (
                validate_mapping_complete(mapping, parsed_variables)
                if parsed_variables
                else []
            )
            if unmapped:
                data_src = frozenset(data_source_variables or [])
                list_v = frozenset(list_variables or [])
                list_item_v = frozenset(list_item_variables or [])
                image_v = frozenset(image_variables or [])
                scalar_vars = [
                    v
                    for v in parsed_variables
                    if v not in data_src and v not in list_v and v not in list_item_v and v not in image_v
                ]
                for var in unmapped:
                    messages.error(
                        request,
                        f"Mapping required for variable: {var}",
                    )
                return render(
                    request,
                    "doctemplates/dynamic_doctemplate_form.html",
                    {
                        "form": form,
                        "formset": formset,
                        "template_obj": None,
                        "is_edit": False,
                        "parsed_variables": parsed_variables,
                        "template_structure": _build_template_structure_summary(
                            data_source_variables,
                            list_variables,
                            list_item_to_list,
                            scalar_vars,
                            image_variables,
                        ),
                        "mapping_rows": _build_mapping_rows(
                            parsed_variables,
                            mapping,
                            data_paths_grouped,
                            list_variables,
                            list_item_variables,
                            data_source_variables,
                            list_item_to_list,
                            image_variables,
                        ),
                        "data_paths_grouped": data_paths_grouped,
                        "transform_choices": TRANSFORM_CHOICES,
                        "existing_mapping": mapping,
                    },
                )
            augment_mapping_with_var_type(
                mapping,
                data_source_variables,
                list_variables,
                list_item_variables,
                image_variables,
            )
            instance = form.save()
            instance.tagging_data = dynamic_formset_cleaned_to_tagging_data(
                formset.cleaned_data
            )
            instance.mapping = mapping
            instance.save()
            messages.success(request, "Dynamic template added.")
            return redirect("doctemplates:dynamic_doctemplate_list")
    else:
        form = DynamicDocumentTemplateForm()
        formset = DynamicTaggingFieldFormSet(prefix=DYNAMIC_FORMSET_PREFIX)
    return render(
        request,
        "doctemplates/dynamic_doctemplate_form.html",
        {
            "form": form,
            "formset": formset,
            "template_obj": None,
            "is_edit": False,
            "parsed_variables": [],
            "mapping_rows": [],
            "data_paths_grouped": data_paths_grouped,
            "transform_choices": TRANSFORM_CHOICES,
            "existing_mapping": {},
        },
    )


@login_required
def dynamic_doctemplate_edit(request, pk):
    """Edit an existing dynamic document template."""
    template_obj = get_object_or_404(DynamicDocumentTemplate, pk=pk)
    data_paths_grouped = _data_paths_grouped_with_images()
    if request.method == "POST":
        form = DynamicDocumentTemplateForm(
            request.POST, request.FILES, instance=template_obj
        )
        formset = DynamicTaggingFieldFormSet(
            request.POST, prefix=DYNAMIC_FORMSET_PREFIX
        )
        parsed_variables = []
        list_variables = []
        list_item_variables = []
        data_source_variables = []
        list_item_to_list = {}
        image_variables = []
        mapping = {}
        file_for_parse = request.FILES.get("file")
        if file_for_parse:
            try:
                content = file_for_parse.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
                (
                    parsed_variables,
                    list_variables,
                    list_item_variables,
                    data_source_variables,
                    list_item_to_list,
                    image_variables,
                ) = parse_dtl_variables_with_metadata(content)
                file_for_parse.seek(0)
            except (TemplateSyntaxError, UnicodeDecodeError):
                pass
        elif template_obj.file:
            try:
                with template_obj.file.open("r") as f:
                    html_content = f.read()
                if html_content:
                    (
                        parsed_variables,
                        list_variables,
                        list_item_variables,
                        data_source_variables,
                        list_item_to_list,
                        image_variables,
                    ) = parse_dtl_variables_with_metadata(html_content)
            except (OSError, UnicodeDecodeError):
                pass
        if parsed_variables:
            mapping = parse_mapping_from_post(request.POST, parsed_variables)
        if form.is_valid() and formset.is_valid():
            unmapped = (
                validate_mapping_complete(mapping, parsed_variables)
                if parsed_variables
                else []
            )
            if unmapped:
                data_src = frozenset(data_source_variables or [])
                list_v = frozenset(list_variables or [])
                list_item_v = frozenset(list_item_variables or [])
                image_v = frozenset(image_variables or [])
                scalar_vars = [
                    v
                    for v in parsed_variables
                    if v not in data_src and v not in list_v and v not in list_item_v and v not in image_v
                ]
                for var in unmapped:
                    messages.error(
                        request,
                        f"Mapping required for variable: {var}",
                    )
                return render(
                    request,
                    "doctemplates/dynamic_doctemplate_form.html",
                    {
                        "form": form,
                        "formset": formset,
                        "template_obj": template_obj,
                        "is_edit": True,
                        "parsed_variables": parsed_variables,
                        "template_structure": _build_template_structure_summary(
                            data_source_variables,
                            list_variables,
                            list_item_to_list,
                            scalar_vars,
                            image_variables,
                        ),
                        "mapping_rows": _build_mapping_rows(
                            parsed_variables,
                            mapping,
                            data_paths_grouped,
                            list_variables,
                            list_item_variables,
                            data_source_variables,
                            list_item_to_list,
                            image_variables,
                        ),
                        "data_paths_grouped": data_paths_grouped,
                        "transform_choices": TRANSFORM_CHOICES,
                        "existing_mapping": mapping,
                    },
                )
            augment_mapping_with_var_type(
                mapping,
                data_source_variables,
                list_variables,
                list_item_variables,
                image_variables,
            )
            instance = form.save(commit=False)
            new_file = request.FILES.get("file")
            if not new_file and template_obj.file:
                instance.file = template_obj.file
            else:
                if template_obj.file and new_file:
                    _remove_file_from_disk(template_obj.file)
            instance.tagging_data = dynamic_formset_cleaned_to_tagging_data(
                formset.cleaned_data
            )
            instance.mapping = mapping
            instance.save()
            messages.success(request, "Dynamic template updated.")
            return redirect("doctemplates:dynamic_doctemplate_list")
    else:
        form = DynamicDocumentTemplateForm(instance=template_obj)
        formset = DynamicTaggingFieldFormSet(
            initial=dynamic_tagging_data_to_formset_initial(
                template_obj.tagging_data
            ),
            prefix=DYNAMIC_FORMSET_PREFIX,
        )

    parsed_variables = []
    list_variables = []
    list_item_variables = []
    data_source_variables = []
    list_item_to_list = {}
    image_variables = []
    if template_obj.file:
        try:
            with template_obj.file.open("r") as f:
                html_content = f.read()
            if html_content:
                (
                    parsed_variables,
                    list_variables,
                    list_item_variables,
                    data_source_variables,
                    list_item_to_list,
                    image_variables,
                ) = parse_dtl_variables_with_metadata(html_content)
        except (OSError, UnicodeDecodeError):
            pass

    data_src = frozenset(data_source_variables or [])
    list_v = frozenset(list_variables or [])
    list_item_v = frozenset(list_item_variables or [])
    image_v = frozenset(image_variables or [])
    scalar_vars = [
        v
        for v in parsed_variables
        if v not in data_src and v not in list_v and v not in list_item_v and v not in image_v
    ]
    existing_mapping = template_obj.mapping or {}

    return render(
        request,
        "doctemplates/dynamic_doctemplate_form.html",
        {
            "form": form,
            "formset": formset,
            "template_obj": template_obj,
            "is_edit": True,
            "parsed_variables": parsed_variables,
            "template_structure": _build_template_structure_summary(
                data_source_variables,
                list_variables,
                list_item_to_list,
                scalar_vars,
                image_variables,
            ),
            "mapping_rows": _build_mapping_rows(
                parsed_variables,
                existing_mapping,
                data_paths_grouped,
                list_variables,
                list_item_variables,
                data_source_variables,
                list_item_to_list,
                image_variables,
            ),
            "data_paths_grouped": data_paths_grouped,
            "transform_choices": TRANSFORM_CHOICES,
            "existing_mapping": existing_mapping,
        },
    )


@login_required
def dynamic_doctemplate_parse(request):
    """
    POST: accept an HTML file, parse DTL variables, return JSON.
    Used by "Identify Fields" on add form (Batch 4).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "No file provided"}, status=400)
    try:
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        (
            variables,
            list_variables,
            list_item_variables,
            data_source_variables,
            list_item_to_list,
            image_variables,
        ) = parse_dtl_variables_with_metadata(content)
        return JsonResponse({
            "variables": variables,
            "list_variables": list(list_variables),
            "list_item_variables": list(list_item_variables),
            "data_source_variables": list(data_source_variables),
            "list_item_to_list": list_item_to_list,
            "image_variables": list(image_variables),
        })
    except TemplateSyntaxError as e:
        return JsonResponse(
            {"error": f"Template syntax error: {e}"},
            status=400,
        )


@login_required
def dynamic_doctemplate_delete_confirm(request, pk):
    """GET: show confirmation. POST: delete template and file."""
    template_obj = get_object_or_404(DynamicDocumentTemplate, pk=pk)
    if request.method == "POST":
        _remove_file_from_disk(template_obj.file)
        template_obj.delete()
        messages.success(request, "Dynamic template deleted.")
        return redirect("doctemplates:dynamic_doctemplate_list")
    return render(
        request,
        "doctemplates/dynamic_doctemplate_confirm_delete.html",
        {"template_obj": template_obj},
    )


# --- Static template views ---


@login_required
def static_doctemplate_list(request):
    """List all static document templates."""
    templates = StaticDocumentTemplate.objects.all().order_by("ref_id")
    return render(
        request,
        "doctemplates/static_doctemplate_list.html",
        {"template_list": templates},
    )


@login_required
def static_doctemplate_add(request):
    """Add a new static document template."""
    if request.method == "POST":
        form = StaticDocumentTemplateForm(request.POST, request.FILES)
        formset = TaggingFieldFormSet(request.POST, prefix=FORMSET_PREFIX)
        if form.is_valid() and formset.is_valid():
            instance = form.save()
            instance.tagging_data = formset_data_to_tagging_data(formset.cleaned_data)
            instance.save()
            messages.success(request, "Static template added.")
            return redirect("doctemplates:static_doctemplate_list")
    else:
        form = StaticDocumentTemplateForm()
        formset = TaggingFieldFormSet(prefix=FORMSET_PREFIX)
    return render(
        request,
        "doctemplates/static_doctemplate_form.html",
        {"form": form, "formset": formset, "template_obj": None, "is_edit": False},
    )


@login_required
def static_doctemplate_edit(request, pk):
    """Edit an existing static document template."""
    template_obj = get_object_or_404(StaticDocumentTemplate, pk=pk)
    if request.method == "POST":
        form = StaticDocumentTemplateForm(
            request.POST, request.FILES, instance=template_obj
        )
        formset = TaggingFieldFormSet(request.POST, prefix=FORMSET_PREFIX)
        if form.is_valid() and formset.is_valid():
            instance = form.save(commit=False)
            if not request.FILES.get("file") and template_obj.file:
                instance.file = template_obj.file
            instance.tagging_data = formset_data_to_tagging_data(formset.cleaned_data)
            instance.save()
            messages.success(request, "Static template updated.")
            return redirect("doctemplates:static_doctemplate_list")
    else:
        form = StaticDocumentTemplateForm(instance=template_obj)
        formset = TaggingFieldFormSet(
            initial=tagging_data_to_formset_initial(template_obj.tagging_data),
            prefix=FORMSET_PREFIX,
        )
    return render(
        request,
        "doctemplates/static_doctemplate_form.html",
        {"form": form, "formset": formset, "template_obj": template_obj, "is_edit": True},
    )


@login_required
def static_doctemplate_delete_confirm(request, pk):
    """GET: show confirmation. POST: delete template and file."""
    template_obj = get_object_or_404(StaticDocumentTemplate, pk=pk)
    if request.method == "POST":
        if template_obj.file:
            path = getattr(template_obj.file, "path", None)
            if path and os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        template_obj.delete()
        messages.success(request, "Static template deleted.")
        return redirect("doctemplates:static_doctemplate_list")
    return render(
        request,
        "doctemplates/static_doctemplate_confirm_delete.html",
        {"template_obj": template_obj},
    )

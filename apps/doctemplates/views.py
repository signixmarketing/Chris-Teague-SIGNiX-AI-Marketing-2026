"""
Views for document templates app.

Static: full CRUD for StaticDocumentTemplate (list, add, edit, delete).
Dynamic: full CRUD for DynamicDocumentTemplate (Batch 2).
"""

import os

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
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
    DocumentSetTemplateForm,
    DocumentSetTemplateItemFormSet,
    formset_to_items,
    items_to_formset_initial,
)
from .models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
    DynamicDocumentTemplate,
)
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
    from django.contrib.contenttypes.models import ContentType

    template_obj = get_object_or_404(DynamicDocumentTemplate, pk=pk)
    if request.method == "POST":
        ct = ContentType.objects.get_for_model(DynamicDocumentTemplate)
        if _template_in_use_by_doc_set(ct, template_obj.pk):
            messages.error(
                request,
                "This template cannot be deleted because it is used in a Document Set Template.",
            )
            return render(
                request,
                "doctemplates/dynamic_doctemplate_confirm_delete.html",
                {"template_obj": template_obj},
            )
        _remove_file_from_disk(template_obj.file)
        template_obj.delete()
        messages.success(request, "Dynamic template deleted.")
        return redirect("doctemplates:dynamic_doctemplate_list")
    return render(
        request,
        "doctemplates/dynamic_doctemplate_confirm_delete.html",
        {"template_obj": template_obj},
    )


# --- Document Set Template views ---

DOCSET_FORMSET_PREFIX = "items"


def _can_add_doc_set_template():
    """True if at least one Deal Type has no Document Set Template."""
    from .forms import _deal_types_without_doc_set_template
    return _deal_types_without_doc_set_template().exists()


def _template_choices_exist():
    """True if at least one Static or Dynamic template exists."""
    return StaticDocumentTemplate.objects.exists() or DynamicDocumentTemplate.objects.exists()


def _template_in_use_by_doc_set(content_type, object_id):
    """True if this template is referenced by any DocumentSetTemplateItem."""
    return DocumentSetTemplateItem.objects.filter(
        content_type=content_type, object_id=object_id
    ).exists()


@login_required
def docsettemplate_list(request):
    """List all document set templates."""
    template_list = DocumentSetTemplate.objects.prefetch_related("items").all()
    can_add = _can_add_doc_set_template()
    return render(
        request,
        "doctemplates/docsettemplate_list.html",
        {"template_list": template_list, "can_add": can_add},
    )


@login_required
def docsettemplate_add(request):
    """Add a new document set template."""
    if not _template_choices_exist():
        messages.error(
            request,
            "Create at least one Static or Dynamic template first.",
        )
        return redirect("doctemplates:docsettemplate_list")
    if not _can_add_doc_set_template():
        messages.error(
            request,
            "Every deal type already has a document set template.",
        )
        return redirect("doctemplates:docsettemplate_list")

    if request.method == "POST":
        form = DocumentSetTemplateForm(request.POST, for_add=True)
        formset = DocumentSetTemplateItemFormSet(
            request.POST, prefix=DOCSET_FORMSET_PREFIX
        )
        if form.is_valid() and formset.is_valid():
            instance = form.save()
            for item in formset_to_items(formset.cleaned_data, instance):
                item.save()
            messages.success(request, "Document set template added.")
            return redirect("doctemplates:docsettemplate_list")
    else:
        form = DocumentSetTemplateForm(for_add=True)
        formset = DocumentSetTemplateItemFormSet(prefix=DOCSET_FORMSET_PREFIX)

    form_rows = [(f, None) for f in formset.forms]
    return render(
        request,
        "doctemplates/docsettemplate_form.html",
        {
            "form": form,
            "formset": formset,
            "form_rows": form_rows,
            "document_set_template": None,
            "is_edit": False,
        },
    )


@login_required
def docsettemplate_edit(request, pk):
    """Edit an existing document set template."""
    dst = get_object_or_404(
        DocumentSetTemplate.objects.prefetch_related("items"), pk=pk
    )
    items = list(dst.items.all())
    item_ids = [item.pk for item in items]

    if request.method == "POST":
        form = DocumentSetTemplateForm(
            request.POST, instance=dst, for_add=False
        )
        formset = DocumentSetTemplateItemFormSet(
            request.POST,
            initial=items_to_formset_initial(items),
            prefix=DOCSET_FORMSET_PREFIX,
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            dst.items.all().delete()
            for item in formset_to_items(formset.cleaned_data, dst):
                item.save()
            messages.success(request, "Document set template updated.")
            return redirect("doctemplates:docsettemplate_list")
    else:
        form = DocumentSetTemplateForm(instance=dst, for_add=False)
        formset = DocumentSetTemplateItemFormSet(
            initial=items_to_formset_initial(items),
            prefix=DOCSET_FORMSET_PREFIX,
        )

    form_rows = [
        (f, item_ids[i] if i < len(item_ids) else None)
        for i, f in enumerate(formset.forms)
    ]
    return render(
        request,
        "doctemplates/docsettemplate_form.html",
        {
            "form": form,
            "formset": formset,
            "form_rows": form_rows,
            "document_set_template": dst,
            "is_edit": True,
        },
    )


@login_required
def docsettemplate_delete_confirm(request, pk):
    """GET: show confirmation. POST: delete document set template and items."""
    dst = get_object_or_404(DocumentSetTemplate, pk=pk)
    if request.method == "POST":
        dst.delete()
        messages.success(request, "Document set template deleted.")
        return redirect("doctemplates:docsettemplate_list")
    return render(
        request,
        "doctemplates/docsettemplate_confirm_delete.html",
        {"document_set_template": dst},
    )


def _docset_item_move(dst, item_id, direction):
    """Move item up (-1) or down (+1). Swap order with sibling; renumber 1-based."""
    item = get_object_or_404(
        DocumentSetTemplateItem,
        document_set_template=dst,
        pk=item_id,
    )
    current_order = item.order
    if direction == -1:
        sibling = dst.items.filter(order=current_order - 1).first()
    else:
        sibling = dst.items.filter(order=current_order + 1).first()
    if not sibling:
        return
    old_sibling_order = sibling.order
    # Swap using temp to avoid unique constraint
    item.order = 0
    item.save(update_fields=["order"])
    sibling.order = current_order
    sibling.save(update_fields=["order"])
    item.order = old_sibling_order
    item.save(update_fields=["order"])
    # Renumber to 1, 2, 3, ...
    for i, it in enumerate(dst.items.order_by("order"), start=1):
        if it.order != i:
            it.order = i
            it.save(update_fields=["order"])


@login_required
def docsettemplate_item_move_up(request, pk, item_id):
    """POST only: move item up, redirect to edit."""
    if request.method != "POST":
        raise Http404
    dst = get_object_or_404(DocumentSetTemplate, pk=pk)
    _docset_item_move(dst, item_id, -1)
    return redirect("doctemplates:docsettemplate_edit", pk=pk)


@login_required
def docsettemplate_item_move_down(request, pk, item_id):
    """POST only: move item down, redirect to edit."""
    if request.method != "POST":
        raise Http404
    dst = get_object_or_404(DocumentSetTemplate, pk=pk)
    _docset_item_move(dst, item_id, +1)
    return redirect("doctemplates:docsettemplate_edit", pk=pk)


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
    from django.contrib.contenttypes.models import ContentType

    template_obj = get_object_or_404(StaticDocumentTemplate, pk=pk)
    if request.method == "POST":
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        if _template_in_use_by_doc_set(ct, template_obj.pk):
            messages.error(
                request,
                "This template cannot be deleted because it is used in a Document Set Template.",
            )
            return render(
                request,
                "doctemplates/static_doctemplate_confirm_delete.html",
                {"template_obj": template_obj},
            )
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

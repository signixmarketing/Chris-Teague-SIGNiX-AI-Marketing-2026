"""
Utilities for document templates.

DTL parsing: extract variable paths from HTML template strings for mapping UI.
Transform application: apply mapping transforms to values from get_deal_data() output.
"""

from datetime import datetime

from django.template import Template
from django.template.base import VariableNode
from django.template.defaulttags import ForNode
from django.template.exceptions import TemplateSyntaxError


# Suffixes that indicate a variable holds an image URL (case-insensitive)
IMAGE_VARIABLE_SUFFIXES = ("_image_url", "_image", "_logo_url", "_logo")


def _is_image_variable(var_name):
    """Return True if the variable name suggests it holds an image URL."""
    if not var_name or not isinstance(var_name, str):
        return False
    lower = var_name.lower()
    return any(lower.endswith(s) for s in IMAGE_VARIABLE_SUFFIXES)


def parse_dtl_variables(html_string):
    """
    Parse an HTML string as Django Template Language and extract variable paths.

    Returns a list of variable paths (e.g. ["data.payment_amount", "data.jet_pack_list",
    "item.sku"]) for use in the mapping UI. Handles:
    - Flat variables: {{ data.payment_amount }} → "data.payment_amount"
    - Filters are stripped: {{ data.x|floatformat:2 }} → "data.x"
    - Single-level loops: {% for item in data.jet_pack_list %} → "data.jet_pack_list"
    - Loop variables: {{ item.sku }} inside the loop → "item.sku"

    Scope: single-level loops and flat variables. Nested loops, {% include %},
    and custom tags are best-effort or out of scope for v1.

    Raises TemplateSyntaxError if the template has invalid DTL syntax.
    Returns empty list if html_string is None or empty.
    """
    variables, _, _, _, _, _ = parse_dtl_variables_with_metadata(html_string)
    return variables


def parse_dtl_variables_with_metadata(html_string):
    """
    Parse DTL and extract variables plus metadata for mapping UI.

    Returns (variables, list_variables, list_item_variables, data_source_variables, list_item_to_list)
    where:
    - variables: all variable paths, with inferred data-source roots (e.g. "data") prepended
    - list_variables: paths found as ForNode sequence (e.g. data.jet_pack_list)
    - list_item_variables: paths like item.sku found inside a for loop referencing the loop var
    - data_source_variables: inferred root names (e.g. "data") that are prefixes of other vars
    - list_item_to_list: dict mapping list_item_var -> list_var (e.g. {"item.sku": "data.jet_pack_list"})
    - image_variables: frozenset of variable names that suggest image URLs (e.g. lease_image_url, logo_url)
    """
    if not html_string or not isinstance(html_string, str):
        return [], frozenset(), frozenset(), frozenset(), {}, frozenset()

    result = []
    list_vars = set()
    list_item_vars = set()
    list_item_to_list = {}  # list_item_var -> list_var
    loop_var_names = set()

    def collect_from_nodelist(nodelist, loop_context=None):
        # loop_context: (loop_var_prefixes, current_list_path) or None
        if nodelist is None:
            return
        loop_prefixes = loop_context[0] if loop_context else ()
        current_list_path = loop_context[1] if loop_context and len(loop_context) > 1 else None
        for node in nodelist:
            if isinstance(node, VariableNode):
                fe = node.filter_expression
                if hasattr(fe, "var") and fe.var is not None:
                    path = str(fe.var).strip()
                    if path and path not in result:
                        result.append(path)
                    for prefix in loop_prefixes:
                        if path == prefix or path.startswith(prefix + "."):
                            list_item_vars.add(path)
                            if current_list_path:
                                list_item_to_list[path] = current_list_path
                            break
            elif isinstance(node, ForNode):
                loop_vars = []
                if hasattr(node, "loopvars"):
                    loop_vars = list(node.loopvars) if node.loopvars else []
                for lv in loop_vars:
                    loop_var_names.add(str(lv).strip())
                inner_prefixes = tuple(str(lv).strip() for lv in loop_vars if lv)
                list_path = None
                if hasattr(node, "sequence") and node.sequence is not None:
                    seq = node.sequence
                    if hasattr(seq, "var"):
                        path = str(seq.var).strip()
                        if path:
                            if path not in result:
                                result.append(path)
                            list_vars.add(path)
                            list_path = path
                    elif hasattr(seq, "token"):
                        path = str(seq.token).strip()
                        if path:
                            if path not in result:
                                result.append(path)
                            list_vars.add(path)
                            list_path = path
                inner_context = (inner_prefixes, list_path) if list_path else (inner_prefixes, current_list_path)
                if hasattr(node, "nodelist_loop"):
                    collect_from_nodelist(node.nodelist_loop, inner_context)
            else:
                for attr in getattr(node, "child_nodelists", ()):
                    child = getattr(node, attr, None)
                    if child is not None:
                        collect_from_nodelist(child, (loop_prefixes, current_list_path))

    try:
        template = Template(html_string)
        collect_from_nodelist(template.nodelist)
    except TemplateSyntaxError:
        raise

    # Infer data-source roots: first path component from dotted vars, excluding loop vars
    data_source_roots = set()
    for path in result:
        if "." in path:
            root = path.split(".", 1)[0]
            if root and root not in loop_var_names:
                data_source_roots.add(root)
    data_source_roots = frozenset(data_source_roots)

    # Prepend data source roots to variables (so they appear first in mapping table)
    roots_sorted = sorted(data_source_roots)
    for root in reversed(roots_sorted):
        if root not in result:
            result.insert(0, root)

    # Detect image variables by naming convention
    image_vars = frozenset(v for v in result if _is_image_variable(v))

    return result, frozenset(list_vars), frozenset(list_item_vars), data_source_roots, list_item_to_list, image_vars


def get_image_sources_for_mapping():
    """
    Return image options for the mapping Source dropdown.

    Returns list of (value, display) where value is image:<uuid> for downstream
    resolution. Display is the image name. Used to build the "Images" optgroup.
    """
    try:
        from apps.images.models import Image

        return [(f"image:{img.uuid}", img.name) for img in Image.objects.all().order_by("name")]
    except Exception:
        return []


def _var_to_form_key(var):
    """Convert variable name to form key (dots -> __)."""
    return var.replace(".", "__")


def _form_key_to_var(key):
    """Convert form key back to variable name."""
    return key.replace("__", ".")


def parse_mapping_from_post(post_data, parsed_variables):
    """
    Parse mapping from request.POST.

    Expects keys mapping_<var>_source and mapping_<var>_transform where var uses __ for dots.
    Returns dict {var: {source: path, transform?: x}}. Variables without source are skipped.
    Empty source means unmapped. Raises ValueError if required variables are missing.
    """
    mapping = {}
    for var in parsed_variables:
        key = _var_to_form_key(var)
        source = (post_data.get(f"mapping_{key}_source") or "").strip()
        transform = (post_data.get(f"mapping_{key}_transform") or "").strip()
        if source:
            entry = {"source": source}
            if transform:
                entry["transform"] = transform
            mapping[var] = entry
    return mapping


def augment_mapping_with_var_type(
    mapping,
    data_source_variables,
    list_variables,
    list_item_variables,
    image_variables=None,
):
    """
    Add var_type to each mapping entry for persistence.

    var_type: "data_source" | "list" | "list_item" | "image" | "scalar"
    """
    data_src = frozenset(data_source_variables) if data_source_variables is not None else frozenset()
    list_v = frozenset(list_variables) if list_variables is not None else frozenset()
    list_item = frozenset(list_item_variables) if list_item_variables is not None else frozenset()
    image_v = frozenset(image_variables) if image_variables is not None else frozenset()
    for var, entry in mapping.items():
        if var in data_src:
            entry["var_type"] = "data_source"
        elif var in list_v:
            entry["var_type"] = "list"
        elif var in list_item:
            entry["var_type"] = "list_item"
        elif var in image_v:
            entry["var_type"] = "image"
        else:
            entry["var_type"] = "scalar"


def validate_mapping_complete(mapping, parsed_variables):
    """
    Ensure all parsed variables are mapped.
    Returns list of unmapped variable names.
    """
    unmapped = []
    for var in parsed_variables:
        if var not in mapping or not (mapping[var].get("source")):
            unmapped.append(var)
    return unmapped


def mapping_to_form_initial(mapping):
    """Convert mapping dict to form initial: {var: {source, transform}}."""
    return mapping


def apply_transform(value, transform_name):
    """
    Apply a transform to a value from get_deal_data() output.

    Used by the context builder when building the template context.
    Dates from get_deal_data() are ISO strings ("YYYY-MM-DD").

    Returns the transformed value. Returns value unchanged if transform is empty
    or unknown. Returns "" for None/empty value when transform expects a value.
    """
    if not transform_name:
        return value
    if value is None or value == "":
        return "" if transform_name in ("date_day", "date_month", "date_year", "date_month_day") else value

    if transform_name == "date_day":
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.day
        except (ValueError, TypeError):
            return value

    if transform_name == "date_month":
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.month
        except (ValueError, TypeError):
            return value

    if transform_name == "date_year":
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.year
        except (ValueError, TypeError):
            return value

    if transform_name == "date_month_day":
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return f"{dt.strftime('%B')} {dt.day}"
        except (ValueError, TypeError):
            return value

    if transform_name == "count":
        if isinstance(value, list):
            return len(value)
        return value

    if transform_name == "number_to_word":
        n = value if isinstance(value, int) else (int(value) if value not in (None, "") else 0)
        return _number_to_word(n)

    if transform_name == "plural_suffix":
        n = value if isinstance(value, int) else (int(value) if value not in (None, "") else 0)
        return "" if n == 1 else "s"

    return value


def _number_to_word(n):
    """Convert 0–99 to English word. Fallback to str(n) outside range."""
    if not isinstance(n, int) or n < 0:
        return str(n) if n is not None else "zero"
    units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen",
    ]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    if n < 20:
        return units[n]
    if n < 100:
        t, u = divmod(n, 10)
        return tens[t] + (" " + units[u] if u else "")
    return str(n)

"""
Schema discovery and deal data retrieval.

Provides get_schema(), get_paths(), and get_deal_data(deal) for the
deal-centric data interface. Used by the mapping UI and context builder.
"""

from django.contrib.auth import get_user_model
from django.db.models import DateField, DecimalField, IntegerField

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealType
from apps.users.models import LeaseOfficerProfile
from apps.vehicles.models import Vehicle

User = get_user_model()

# Map Django field classes to schema types
FIELD_TYPE_MAP = {
    DateField: "date",
    DecimalField: "decimal",
    IntegerField: "integer",
}


def _schema_type_for_field(field):
    """Return schema type for a Django field."""
    for django_cls, schema_type in FIELD_TYPE_MAP.items():
        if isinstance(field, django_cls):
            return schema_type
    # CharField, TextField, EmailField, etc. -> string
    return "string"


def _build_scalar_node(path, field, model_cls):
    """Build a scalar (leaf) schema node."""
    return {
        "path": path,
        "type": _schema_type_for_field(field),
        "model": model_cls.__name__,
        "description": getattr(field, "verbose_name", None) or field.name.replace("_", " ").title(),
    }


def _collect_paths_from_nodes(nodes):
    """Recursively collect all mappable path strings from schema nodes."""
    paths = []
    for node in nodes:
        node_type = node.get("type")
        path = node.get("path")
        if node_type in ("string", "date", "decimal", "integer"):
            paths.append(path)
        elif node_type == "object" and "children" in node:
            paths.extend(_collect_paths_from_nodes(node["children"]))
        elif node_type == "list" and "children" in node:
            paths.append(path)
            paths.extend(_collect_paths_from_nodes(node["children"]))
    return paths


def get_schema():
    """
    Return the deal-centric schema as a tree.

    Structure: { "root": "deal", "description": "...", "version": "1", "nodes": [...] }
    Each node has path, type, optional model, description, children, item_path.
    """
    # Deal scalar fields (exclude relations)
    deal_scalar_fields = [
        "date_entered",
        "lease_start_date",
        "lease_end_date",
        "payment_amount",
        "payment_period",
        "security_deposit",
        "insurance_amount",
        "governing_law",
    ]

    deal_children = []

    for field_name in deal_scalar_fields:
        try:
            field = Deal._meta.get_field(field_name)
            deal_children.append(_build_scalar_node(f"deal.{field_name}", field, Deal))
        except Exception:
            pass

    # lease_officer (User) - object with username and lease_officer_profile
    lease_officer_children = [
        {"path": "deal.lease_officer.username", "type": "string", "model": "User", "description": "Username"},
        {"path": "deal.lease_officer.lease_officer_profile.first_name", "type": "string", "model": "LeaseOfficerProfile", "description": "First name"},
        {"path": "deal.lease_officer.lease_officer_profile.last_name", "type": "string", "model": "LeaseOfficerProfile", "description": "Last name"},
        {"path": "deal.lease_officer.lease_officer_profile.phone_number", "type": "string", "model": "LeaseOfficerProfile", "description": "Phone number"},
        {"path": "deal.lease_officer.lease_officer_profile.email", "type": "string", "model": "LeaseOfficerProfile", "description": "Email"},
        {"path": "deal.lease_officer.lease_officer_profile.full_name", "type": "string", "model": "LeaseOfficerProfile", "description": "Full name"},
    ]
    deal_children.append({
        "path": "deal.lease_officer",
        "type": "object",
        "model": "User",
        "description": "Lease officer",
        "children": lease_officer_children,
    })

    # deal_type (DealType) - object with name
    deal_children.append({
        "path": "deal.deal_type",
        "type": "object",
        "model": "DealType",
        "description": "Deal type",
        "children": [
            {"path": "deal.deal_type.name", "type": "string", "model": "DealType", "description": "Name"},
        ],
    })

    # vehicles - list of Vehicle
    vehicle_children = []
    for field_name in ["sku", "year", "jpin"]:
        try:
            field = Vehicle._meta.get_field(field_name)
            vehicle_children.append(_build_scalar_node(f"deal.vehicles.item.{field_name}", field, Vehicle))
        except Exception:
            pass
    deal_children.append({
        "path": "deal.vehicles",
        "type": "list",
        "model": "Vehicle",
        "item_path": "item",
        "description": "Vehicles",
        "children": vehicle_children,
    })

    # vehicles_count (derived from deal.vehicles; use transform number_to_word or plural_suffix for display variants)
    deal_children.append(
        {"path": "deal.vehicles_count", "type": "integer", "model": "Deal", "description": "Count of vehicles"},
    )

    # contacts - list of Contact (includes full_name: computed from first + middle + last)
    contact_children = []
    for field_name in ["first_name", "middle_name", "last_name", "email", "phone_number"]:
        try:
            field = Contact._meta.get_field(field_name)
            contact_children.append(_build_scalar_node(f"deal.contacts.item.{field_name}", field, Contact))
        except Exception:
            pass
    contact_children.append({
        "path": "deal.contacts.item.full_name",
        "type": "string",
        "model": "Contact",
        "description": "Full name (first + middle + last, space-separated)",
    })
    deal_children.append({
        "path": "deal.contacts",
        "type": "list",
        "model": "Contact",
        "item_path": "item",
        "description": "Contacts",
        "children": contact_children,
    })

    # contacts_count (derived from deal.contacts; use transform number_to_word or plural_suffix for display variants)
    deal_children.append(
        {"path": "deal.contacts_count", "type": "integer", "model": "Deal", "description": "Count of contacts"},
    )

    root_node = {
        "path": "deal",
        "type": "object",
        "model": "Deal",
        "description": "Deal",
        "children": deal_children,
    }

    return {
        "root": "deal",
        "description": "Deal-centric document context schema",
        "version": "1",
        "nodes": [root_node],
    }


def get_paths():
    """
    Return a flat list of mappable path strings.

    Derived from get_schema(). Includes paths like deal.payment_amount,
    deal.vehicles, deal.vehicles.item.sku, etc.
    """
    schema = get_schema()
    paths = []
    for root_node in schema.get("nodes", []):
        paths.append(root_node["path"])
        paths.extend(_collect_paths_from_nodes(root_node.get("children", [])))
    return paths


# List paths used for grouping in the mapping UI
LIST_PATHS = ["deal.vehicles", "deal.contacts"]


def get_paths_grouped_for_mapping():
    """
    Return paths grouped for the mapping UI dropdown.

    Groups: Data Source (root paths like deal), List sources, Scalar / item paths.
    Returns: [(group_label, [(path, display_label), ...]), ...]
    """
    all_paths = get_paths()
    list_group = []
    scalar_group = []
    list_labels = {"deal.vehicles": "deal.vehicles — Vehicles (list)", "deal.contacts": "deal.contacts — Contacts (list)"}
    for p in all_paths:
        if p == "deal":
            continue
        if p in LIST_PATHS:
            list_group.append((p, list_labels.get(p, f"{p} (list)")))
        else:
            scalar_group.append((p, p))
    result = []
    result.append(("Data Source", [("deal", "deal")]))
    if list_group:
        result.append(("List sources", list_group))
    if scalar_group:
        result.append(("Scalar / item paths", scalar_group))
    return result


def get_deal_data(deal):
    """
    Return the full deal-centric data structure for a given deal.

    Input: Deal instance.
    Output: Nested dict with "deal" at root. JSON-serializable.
    Vehicles and contacts ordered by id. Use null when lease_officer or
    lease_officer_profile is missing.
    """
    # Scalars
    data = {
        "date_entered": deal.date_entered.isoformat() if deal.date_entered else None,
        "lease_start_date": deal.lease_start_date.isoformat() if deal.lease_start_date else None,
        "lease_end_date": deal.lease_end_date.isoformat() if deal.lease_end_date else None,
        "payment_amount": float(deal.payment_amount) if deal.payment_amount is not None else None,
        "payment_period": deal.payment_period or "",
        "security_deposit": float(deal.security_deposit) if deal.security_deposit is not None else None,
        "insurance_amount": float(deal.insurance_amount) if deal.insurance_amount is not None else None,
        "governing_law": deal.governing_law or "",
    }

    # lease_officer
    if deal.lease_officer_id:
        user = deal.lease_officer
        profile = getattr(user, "lease_officer_profile", None)
        if profile is None:
            try:
                profile = LeaseOfficerProfile.objects.get(user=user)
            except LeaseOfficerProfile.DoesNotExist:
                profile = None

        if profile is not None:
            data["lease_officer"] = {
                "username": user.get_username(),
                "lease_officer_profile": {
                    "first_name": profile.first_name or "",
                    "last_name": profile.last_name or "",
                    "phone_number": profile.phone_number or "",
                    "email": profile.email or "",
                    "full_name": profile.full_name,
                },
            }
        else:
            data["lease_officer"] = {
                "username": user.get_username(),
                "lease_officer_profile": None,
            }
    else:
        data["lease_officer"] = None

    # deal_type
    if deal.deal_type_id:
        data["deal_type"] = {"name": deal.deal_type.name}
    else:
        data["deal_type"] = None

    # vehicles
    vehicles_qs = deal.vehicles.order_by("id")
    vehicles_list = [
        {"sku": v.sku or "", "year": str(v.year) if v.year is not None else "", "jpin": v.jpin or ""}
        for v in vehicles_qs
    ]
    data["vehicles"] = vehicles_list

    # vehicles_count (derived)
    data["vehicles_count"] = len(vehicles_list)

    # contacts (full_name computed from first + middle + last, space-separated)
    contacts_qs = deal.contacts.order_by("id")
    data["contacts"] = []
    for c in contacts_qs:
        parts = [c.first_name or "", c.middle_name or "", c.last_name or ""]
        full_name = " ".join(p for p in parts if p).strip()
        data["contacts"].append({
            "first_name": c.first_name or "",
            "middle_name": c.middle_name or "",
            "last_name": c.last_name or "",
            "full_name": full_name,
            "email": c.email or "",
            "phone_number": c.phone_number or "",
        })

    # contacts_count (derived)
    data["contacts_count"] = len(data["contacts"])

    return {"deal": data}

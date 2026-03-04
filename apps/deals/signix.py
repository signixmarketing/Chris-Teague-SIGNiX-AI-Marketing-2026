"""
SIGNiX integration: configuration loader and (in later plans) signer service,
transaction packager, etc. Plan 1 adds get_signix_config(); Plan 3 adds signer service.
"""

import base64
import logging
import uuid
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
from dataclasses import dataclass

import requests
from django.template.loader import get_template

from apps.deals.models import SignixConfig, SignatureTransaction
from apps.deals.models import DEFAULT_SIGNIX_EMAIL_CONTENT
from apps.doctemplates.models import DynamicDocumentTemplate

logger = logging.getLogger(__name__)


class SignixValidationError(Exception):
    """Raised when submit preconditions fail (Plan 5). errors is a list of user-facing messages."""

    def __init__(self, errors):
        self.errors = list(errors) if errors else []
        super().__init__("; ".join(self.errors))


class SignixApiError(Exception):
    """Raised when SIGNiX API returns an error (HTTP 4xx/5xx or StatusCode non-zero). Plan 6."""

    def __init__(self, message, http_status=None, response_text=None):
        self.message = message
        self.http_status = http_status
        self.response_text = response_text
        super().__init__(message)


@dataclass(frozen=True)
class SignerPerson:
    """Person data for a signer slot (Plan 3). Used by Signers table and transaction packager."""

    first_name: str
    middle_name: str
    last_name: str
    email: str
    phone: str


def get_signix_config() -> SignixConfig:
    """
    Return the single SignixConfig instance, creating it with defaults if none exists.
    Uses pk=1 so only one row is ever used; the UI and packager always use this record.
    """
    config, _ = SignixConfig.objects.get_or_create(
        pk=1,
        defaults={
            "demo_only": True,
            "delete_documents_after_days": 60,
            "default_email_content": DEFAULT_SIGNIX_EMAIL_CONTENT,
        },
    )
    return config


def get_signers_for_document_set_template(document_set_template) -> list:
    """
    Return an ordered list of unique signer slot numbers (e.g. [1, 2]) from the
    document set template by scanning each item's template tagging_data for
    member_info_number. Used by Signers table (Plan 4) and transaction packager (Plans 5–6).

    Returns [] if document_set_template is None, has no items, or no valid
    member_info_number values. Skips items whose template is missing or wrong type.
    """
    if document_set_template is None:
        return []
    slots = set()
    for item in document_set_template.items.all():
        template = getattr(item, "template", None)
        if template is None:
            continue
        tagging_data = getattr(template, "tagging_data", None)
        if not isinstance(tagging_data, list):
            continue
        for entry in tagging_data:
            if not isinstance(entry, dict):
                continue
            val = entry.get("member_info_number")
            if isinstance(val, int):
                slots.add(val)
    return sorted(slots)


def _user_to_signer_person(user) -> SignerPerson:
    """Build SignerPerson from User when no LeaseOfficerProfile (slot 1 fallback)."""
    full = (user.get_full_name() or "").strip()
    if full:
        parts = full.split(None, 1)
        first_name = parts[0]
        last_name = parts[1].strip() if len(parts) > 1 else ""
    else:
        first_name = user.get_username() or ""
        last_name = ""
    email = (getattr(user, "email", None) or "") or ""
    return SignerPerson(
        first_name=first_name,
        middle_name="",
        last_name=last_name,
        email=email,
        phone="",
    )


def resolve_signer_slot(deal, slot_number: int):
    """
    Return SignerPerson for the given slot, or None if the slot cannot be resolved.

    Slot 1 = lease officer (LeaseOfficerProfile if present, else User fallback).
    Slot 2 = first contact (deal.contacts.order_by("id").first()).
    Slot 3+ = None.
    """
    if slot_number == 1:
        user = getattr(deal, "lease_officer", None)
        if user is None:
            return None
        profile = getattr(user, "lease_officer_profile", None)
        if profile is not None:
            return SignerPerson(
                first_name=(getattr(profile, "first_name", None) or ""),
                middle_name="",
                last_name=(getattr(profile, "last_name", None) or ""),
                email=(getattr(profile, "email", None) or ""),
                phone=(getattr(profile, "phone_number", None) or ""),
            )
        return _user_to_signer_person(user)
    if slot_number == 2:
        contacts = getattr(deal, "contacts", None)
        if contacts is None:
            return None
        contact = contacts.order_by("id").first()
        if contact is None:
            return None
        return SignerPerson(
            first_name=(getattr(contact, "first_name", None) or ""),
            middle_name=(getattr(contact, "middle_name", None) or ""),
            last_name=(getattr(contact, "last_name", None) or ""),
            email=(getattr(contact, "email", None) or ""),
            phone=(getattr(contact, "phone_number", None) or ""),
        )
    return None


# Plan 4: auth type constants (used by Signers table and packager)
AUTH_SELECT_ONE_CLICK = "SelectOneClick"
AUTH_SMS_ONE_CLICK = "SMSOneClick"


def get_signer_order_for_deal(deal, document_set_template):
    """
    Return the effective signer order for the deal: deal.signer_order if set and
    non-empty, else the template's signer slots in numeric order (Plan 4).
    """
    order = getattr(deal, "signer_order", None)
    if order and isinstance(order, list) and len(order) > 0:
        return order
    return get_signers_for_document_set_template(document_set_template)


def get_signer_authentication_for_slot(deal, slot_number: int) -> str:
    """
    Return the SIGNiX auth type for the given slot: from deal.signer_authentication
    if present (key str(slot_number)), else default: slot 1 → SelectOneClick,
    slot 2 → SMSOneClick, slot 3+ → SelectOneClick (Plan 4).
    """
    auth_map = getattr(deal, "signer_authentication", None)
    if isinstance(auth_map, dict):
        key = str(slot_number)
        if key in auth_map and auth_map[key] in (AUTH_SELECT_ONE_CLICK, AUTH_SMS_ONE_CLICK):
            return auth_map[key]
    if slot_number == 2:
        return AUTH_SMS_ONE_CLICK
    return AUTH_SELECT_ONE_CLICK


def get_role_label_for_slot(slot_number: int) -> str:
    """Return display label for the signer slot (Plan 4). Slot 1 → Lease officer, 2 → Lessee, 3+ → Signer n."""
    if slot_number == 1:
        return "Lease officer"
    if slot_number == 2:
        return "Lessee"
    return f"Signer {slot_number}"


def validate_submit_preconditions(deal, document_set):
    """
    Validate that deal and document_set are ready for building SubmitDocument.
    Raises SignixValidationError with a list of error messages on failure (Plan 5).
    """
    errors = []
    if document_set is None:
        errors.append("Document set is required.")
        raise SignixValidationError(errors)
    if getattr(document_set, "deal_id", None) != getattr(deal, "pk", None):
        errors.append("Document set does not belong to this deal.")
    template = getattr(document_set, "document_set_template", None)
    if template is None:
        errors.append("Document set has no template.")
    else:
        order = get_signer_order_for_deal(deal, template)
        for slot in order:
            if resolve_signer_slot(deal, slot) is None:
                errors.append(f"Signer slot {slot} could not be resolved to a person.")
    instances = getattr(document_set, "instances", None)
    if instances is None:
        errors.append("Document set has no instances.")
    elif not instances.exists():
        errors.append("Document set has no instances.")
    else:
        for instance in instances.all():
            latest = instance.versions.first()
            if latest is None:
                errors.append(f"Document instance (order {instance.order}) has no version.")
            elif not latest.file:
                errors.append(f"Document instance (order {instance.order}) has no file.")
    config = get_signix_config()
    if not (getattr(config, "submitter_email", None) or "").strip():
        errors.append("SIGNiX configuration missing submitter email.")
    if errors:
        raise SignixValidationError(errors)


def _build_transaction_id() -> str:
    """Return a new TransactionID (UUID, 36 chars) for SubmitDocument (Plan 5)."""
    return str(uuid.uuid4())


def build_submit_data_dict(deal, document_set, config):
    """
    Build the data dict for SubmitDocument XML: cust_info, transaction_data, signers.
    Does not include Form; used by build_submit_document_body (Plan 5 Batch 1).
    Call validate_submit_preconditions first.
    """
    template = document_set.document_set_template
    transaction_id = _build_transaction_id()
    doc_set_description = f"Deal #{deal.pk} - {getattr(template, 'name', 'Document Set')}"
    submitter_phone = (getattr(config, "submitter_phone", None) or "").strip() or "800-555-1234"
    submitter_name_parts = [
        getattr(config, "submitter_first_name", None) or "",
        getattr(config, "submitter_middle_name", None) or "",
        getattr(config, "submitter_last_name", None) or "",
    ]
    submitter_name = " ".join(p for p in submitter_name_parts if p).strip()

    cust_info = {
        "sponsor": getattr(config, "sponsor", None) or "",
        "client": getattr(config, "client", None) or "",
        "userId": getattr(config, "user_id", None) or "",
        "password": getattr(config, "password", None) or "",
        "workgroup": getattr(config, "workgroup", None) or "",
        "demo": "true" if getattr(config, "demo_only", True) else "false",
        "del_docs_after": getattr(config, "delete_documents_after_days", 60),
        "email_content": getattr(config, "default_email_content", None) or "",
    }
    transaction_data = {
        "transactionId": transaction_id,
        "doc_set_description": doc_set_description,
        "submitter_email": getattr(config, "submitter_email", None) or "",
        "submitter_name": submitter_name,
        "submitter_phone": submitter_phone,
        "suspend_on_start": "false",
    }
    order = get_signer_order_for_deal(deal, template)
    signers = []
    for i, slot in enumerate(order, start=1):
        person = resolve_signer_slot(deal, slot)
        if person is None:
            continue
        service = get_signer_authentication_for_slot(deal, slot)
        signers.append({
            "first_name": person.first_name,
            "middle_name": person.middle_name or "",
            "last_name": person.last_name,
            "email": person.email,
            "phone": person.phone or "",
            "service": service,
            "sms_count": 1 if service == AUTH_SMS_ONE_CLICK else 0,  # schema requires SMSCount before Service
            "ssn": "910000000",
            "dob": "01/01/1990",  # Flex API DateType: MM/DD/YYYY pattern; placeholder for SelectOneClick/SMSOneClick
            "ref_id": f"Signer {i}",
        })
    return {
        "cust_info": cust_info,
        "transaction_data": transaction_data,
        "signers": signers,
        "transaction_id": transaction_id,
    }


def _build_form_xml_fragment(instance):
    """
    Build one Form XML fragment for a document instance (Plan 5 Batch 2).
    Uses source template ref_id for FileName, latest version file (base64).
    For Static templates: SignatureLine + SignField (AcroForm).
    For Dynamic (generated, text-tagged) templates: TextTagField + TextTagSignature.
    """
    template = getattr(instance, "source_document_template", None)
    if template is None:
        return ""
    latest = instance.versions.first()
    if latest is None or not latest.file:
        return ""
    ref_id = (getattr(template, "ref_id", None) or "document").strip() or "document"
    filename = f"{ref_id}.pdf"
    try:
        with latest.file.open("rb") as fh:
            raw_bytes = fh.read()
    except (OSError, ValueError):
        return ""
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    length = len(raw_bytes)

    if isinstance(template, DynamicDocumentTemplate):
        return _build_form_xml_fragment_text_tagging(
            instance, template, ref_id, filename, b64, length
        )
    return _build_form_xml_fragment_acroform(
        instance, template, ref_id, filename, b64, length
    )


def _build_form_xml_fragment_text_tagging(instance, template, ref_id, filename, b64, length):
    """Build Form XML for Dynamic (text-tagged) document: TextTagField + TextTagSignature."""
    tagging_data = getattr(template, "tagging_data", None) or []
    text_tag_fields = []
    text_tag_signatures = []
    for entry in tagging_data:
        if not isinstance(entry, dict):
            continue
        field_type = (entry.get("field_type") or "").strip().lower()
        anchor = (entry.get("anchor_text") or "").strip()
        bbox = entry.get("bounding_box") or {}
        x_off = bbox.get("x_offset", 0)
        y_off = bbox.get("y_offset", 0)
        w = bbox.get("width", 90)
        h = bbox.get("height", 12)
        required = (entry.get("is_required") or "yes").strip().lower() in ("yes", "true", "1")
        tag_name = (entry.get("tag_name") or "").strip()
        if field_type == "date_signed":
            text_tag_fields.append(
                f"<TextTagField><Type>DateSigned</Type><AnchorText>{saxutils.escape(anchor)}</AnchorText>"
                f"<AnchorXOffset>{x_off}</AnchorXOffset><AnchorYOffset>{y_off}</AnchorYOffset>"
                f"<Width>{w}</Width><Height>{h}</Height><IsRequired>{'yes' if required else 'no'}</IsRequired>"
                f"<TagName>{saxutils.escape(tag_name or 'DateField')}</TagName></TextTagField>"
            )
        elif field_type == "signature":
            member = entry.get("member_info_number")
            if not isinstance(member, int):
                continue
            date_tag = (entry.get("date_signed_field_name") or "").strip()
            date_fmt = (entry.get("date_signed_format") or "MM/dd/yy").strip()
            date_block = f"<DateSignedTagName>{saxutils.escape(date_tag)}</DateSignedTagName><DateSignedFormat>{saxutils.escape(date_fmt)}</DateSignedFormat>" if date_tag else ""
            text_tag_signatures.append(
                f"<TextTagSignature><MemberInfoNumber>{member}</MemberInfoNumber>"
                f"<AnchorText>{saxutils.escape(anchor)}</AnchorText>"
                f"<AnchorXOffset>{x_off}</AnchorXOffset><AnchorYOffset>{y_off}</AnchorYOffset>"
                f"<Width>{w}</Width><Height>{h}</Height><IsRequired>{'yes' if required else 'no'}</IsRequired>"
                f"{date_block}</TextTagSignature>"
            )
    if not text_tag_fields and not text_tag_signatures:
        text_tag_signatures = [
            "<TextTagSignature><MemberInfoNumber>1</MemberInfoNumber><AnchorText>Lessor</AnchorText>"
            "<AnchorXOffset>0</AnchorXOffset><AnchorYOffset>0</AnchorYOffset><Width>120</Width><Height>20</Height>"
            "<IsRequired>yes</IsRequired></TextTagSignature>",
            "<TextTagSignature><MemberInfoNumber>2</MemberInfoNumber><AnchorText>Lessee</AnchorText>"
            "<AnchorXOffset>0</AnchorXOffset><AnchorYOffset>0</AnchorYOffset><Width>120</Width><Height>20</Height>"
            "<IsRequired>yes</IsRequired></TextTagSignature>",
        ]
    ref_id_esc = saxutils.escape(f"Form-{instance.order}")
    desc_esc = saxutils.escape(ref_id)
    return (
        f"<Form><RefID>{ref_id_esc}</RefID><Desc>{desc_esc}</Desc>"
        f"<FileName>{saxutils.escape(filename)}</FileName><MimeType>application/pdf</MimeType>"
        + "".join(text_tag_fields) + "".join(text_tag_signatures)
        + f"<Length>{length}</Length><Data>{b64}</Data></Form>"
    )


def _build_form_xml_fragment_acroform(instance, template, ref_id, filename, b64, length):
    """Build Form XML for a Static (AcroForm) document: SignatureLine + SignField."""
    tagging_data = getattr(template, "tagging_data", None) or []
    signature_field_names = getattr(template, "signature_field_names", None) or {}
    signature_lines = []
    seen_member = set()
    for entry in tagging_data:
        if not isinstance(entry, dict):
            continue
        member = entry.get("member_info_number")
        if not isinstance(member, int):
            continue
        tag_name = (entry.get("tag_name") or entry.get("SignField") or "").strip()
        if not tag_name:
            tag_name = signature_field_names.get(str(member))
        if not tag_name and member in (1, 2):
            tag_name = "Lessor" if member == 1 else "Lessee"
        sign_field = f"<SignField>{saxutils.escape(tag_name)}</SignField>" if tag_name else ""
        date_signed_name = (entry.get("date_signed_field_name") or "").strip()
        date_signed_fmt = (entry.get("date_signed_format") or "MM/dd/yy").strip()
        date_block = ""
        if date_signed_name:
            date_block = f"<DateSignedField>{saxutils.escape(date_signed_name)}</DateSignedField><DateSignedFormat>{saxutils.escape(date_signed_fmt)}</DateSignedFormat>"
        signature_lines.append(
            f"<SignatureLine><MemberInfoNumber>{member}</MemberInfoNumber>{sign_field}{date_block}</SignatureLine>"
        )
        seen_member.add(member)
    if not signature_lines:
        signature_lines.append("<SignatureLine><MemberInfoNumber>1</MemberInfoNumber></SignatureLine>")
    ref_id_esc = saxutils.escape(f"Form-{instance.order}")
    desc_esc = saxutils.escape(ref_id)
    return (
        f"<Form>"
        f"<RefID>{ref_id_esc}</RefID>"
        f"<Desc>{desc_esc}</Desc>"
        f"<FileName>{saxutils.escape(filename)}</FileName>"
        f"<MimeType>application/pdf</MimeType>"
        + "".join(signature_lines)
        + f"<Length>{length}</Length>"
        f"<Data>{b64}</Data>"
        f"</Form>"
    )


def build_submit_document_body(deal, document_set):
    """
    Build the full SubmitDocument request XML and metadata (Plan 5).
    Returns (xml_string, metadata) with metadata["transaction_id"].
    Raises SignixValidationError if preconditions fail.
    """
    validate_submit_preconditions(deal, document_set)
    config = get_signix_config()
    data = build_submit_data_dict(deal, document_set, config)
    form_parts = []
    for instance in document_set.instances.order_by("order"):
        frag = _build_form_xml_fragment(instance)
        if frag:
            form_parts.append(frag)
    data["form"] = "".join(form_parts)
    data["submitter"] = {
        "email": data["transaction_data"]["submitter_email"],
        "name": data["transaction_data"]["submitter_name"],
        "phone": data["transaction_data"]["submitter_phone"],
    }
    template = get_template("signix/submit_document_request.xml")
    body = template.render({"data": data})
    return body, {"transaction_id": data["transaction_id"]}


# --- Plan 6: Send to SIGNiX and parse response ---

SIGNIX_ENDPOINT_WEBTEST = "https://webtest.signix.biz/sdd/b2b/sdddc_ns.jsp"
SIGNIX_ENDPOINT_PRODUCTION = "https://signix.net/sdd/b2b/sdddc_ns.jsp"


def get_signix_submit_endpoint(config) -> str:
    """Return the SubmitDocument endpoint URL (Webtest or Production) per config.demo_only (Plan 6)."""
    if getattr(config, "demo_only", True):
        return SIGNIX_ENDPOINT_WEBTEST
    return SIGNIX_ENDPOINT_PRODUCTION


@dataclass(frozen=True)
class SendSubmitDocumentResult:
    """Result of a successful send_submit_document call (Plan 6)."""

    document_set_id: str
    first_signing_url: str | None


def _find_text_in_element_tree(root, tag_local_name: str):
    """Find first element with given local tag name (namespace-agnostic); return its text or None."""
    for elem in root.iter():
        if elem.tag.split("}")[-1] == tag_local_name:
            return (elem.text or "").strip() or None
    return None


def _find_first_signing_url(root):
    """
    Extract first-signer signing URL from SubmitDocument response if present.
    Flex API element name may vary (e.g. AccessLink, SignerAccessLink); look for
    element text that looks like a URL (starts with http).
    """
    for elem in root.iter():
        text = (elem.text or "").strip()
        if text and (text.startswith("http://") or text.startswith("https://")):
            return text
    return None


def send_submit_document(body: str, endpoint_url: str, config) -> SendSubmitDocumentResult:
    """
    POST the SubmitDocument request XML to SIGNiX and parse the response (Plan 6).

    Transport per Flex API: POST application/x-www-form-urlencoded with
    method=SubmitDocument and request=<full XML>. Parses response for DocumentSetID
    and optional first-signing URL. On HTTP error or StatusCode non-zero, raises
    SignixApiError (message, http_status, response_text).
    """
    payload = {"method": "SubmitDocument", "request": body}
    try:
        resp = requests.post(
            endpoint_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )
    except requests.RequestException as e:
        raise SignixApiError(
            f"SIGNiX request failed: {e!s}",
            http_status=None,
            response_text=None,
        )
    response_text = resp.text or ""
    if resp.status_code >= 400:
        raise SignixApiError(
            f"SIGNiX returned HTTP {resp.status_code}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as e:
        raise SignixApiError(
            f"Invalid XML response from SIGNiX: {e!s}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    status_code_el = _find_text_in_element_tree(root, "StatusCode")
    status_code = 0
    if status_code_el is not None:
        try:
            status_code = int(status_code_el)
        except (TypeError, ValueError):
            pass
    if status_code != 0:
        status_desc = _find_text_in_element_tree(root, "StatusDesc") or "Unknown error"
        raise SignixApiError(
            f"SIGNiX error: {status_desc}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    doc_set_id = _find_text_in_element_tree(root, "DocumentSetID")
    if not doc_set_id:
        raise SignixApiError(
            "SIGNiX response missing DocumentSetID",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    first_signing_url = _find_first_signing_url(root)
    return SendSubmitDocumentResult(document_set_id=doc_set_id, first_signing_url=first_signing_url)


def _build_get_access_link_request_xml(document_set_id: str, config, member_info_number: int) -> str:
    """Build GetAccessLinkSigner request XML per Flex API (CustInfo + Data/DocumentSetID, MemberInfoNumber)."""
    ns = "urn:com:signix:schema:sdddc-1-1"
    doc_set_id_esc = saxutils.escape(document_set_id)
    sponsor = saxutils.escape(getattr(config, "sponsor", None) or "")
    client = saxutils.escape(getattr(config, "client", None) or "")
    user_id = saxutils.escape(getattr(config, "user_id", None) or "")
    pswd = saxutils.escape(getattr(config, "password", None) or "")
    workgroup = saxutils.escape(getattr(config, "workgroup", None) or "")
    return (
        f'<?xml version="1.0"?>'
        f'<GetAccessLinkSignerRq xmlns="{ns}">'
        f"<CustInfo>"
        f"<Sponsor>{sponsor}</Sponsor>"
        f"<Client>{client}</Client>"
        f"<UserId>{user_id}</UserId>"
        f"<Pswd>{pswd}</Pswd>"
        f"<Workgroup>{workgroup}</Workgroup>"
        f"</CustInfo>"
        f"<Data>"
        f"<DocumentSetID>{doc_set_id_esc}</DocumentSetID>"
        f"<MemberInfoNumber>{member_info_number}</MemberInfoNumber>"
        f"</Data>"
        f"</GetAccessLinkSignerRq>"
    )


def get_access_link_signer(
    document_set_id: str, config, member_info_number: int = 1
) -> str:
    """
    Call GetAccessLink for a signer (Plan 6). Returns the signing URL for the given member.
    Same endpoint and transport as SubmitDocument; method=GetAccessLinkSigner.
    Raises SignixApiError on HTTP or API error.
    """
    endpoint_url = get_signix_submit_endpoint(config)
    body = _build_get_access_link_request_xml(document_set_id, config, member_info_number)
    payload = {"method": "GetAccessLinkSigner", "request": body}
    try:
        resp = requests.post(
            endpoint_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    except requests.RequestException as e:
        raise SignixApiError(
            f"GetAccessLink failed: {e!s}",
            http_status=None,
            response_text=None,
        )
    response_text = resp.text or ""
    if resp.status_code >= 400:
        raise SignixApiError(
            f"GetAccessLink returned HTTP {resp.status_code}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as e:
        raise SignixApiError(
            f"GetAccessLink invalid XML: {e!s}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    status_code_el = _find_text_in_element_tree(root, "StatusCode")
    status_code = 0
    if status_code_el is not None:
        try:
            status_code = int(status_code_el)
        except (TypeError, ValueError):
            pass
    if status_code != 0:
        status_desc = _find_text_in_element_tree(root, "StatusDesc") or "Unknown error"
        raise SignixApiError(
            f"GetAccessLink error: {status_desc}",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    url = _find_first_signing_url(root)
    if not url:
        raise SignixApiError(
            "GetAccessLink response missing signer URL",
            http_status=resp.status_code,
            response_text=response_text[:500] if response_text else None,
        )
    return url


VERSION_STATUS_SUBMITTED_TO_SIGNIX = "Submitted to SIGNiX"


def submit_document_set_for_signature(deal, document_set):
    """
    Orchestrator: validate, build body, send to SIGNiX, GetAccessLink if needed,
    create SignatureTransaction, update version status (Plan 6).
    Returns (SignatureTransaction, first_signing_url).
    Raises SignixValidationError on validation failure; SignixApiError on API failure.
    """
    validate_submit_preconditions(deal, document_set)
    body, metadata = build_submit_document_body(deal, document_set)
    config = get_signix_config()
    endpoint_url = get_signix_submit_endpoint(config)
    logger.debug("Submitting document set to SIGNiX (deal_id=%s, document_set_id=%s).", deal.pk, document_set.pk)
    try:
        result = send_submit_document(body, endpoint_url, config)
    except SignixApiError as e:
        logger.error(
            "SIGNiX SubmitDocument failed: %s",
            e.message,
            extra={"http_status": e.http_status, "response_preview": (e.response_text or "")[:500]},
        )
        raise
    first_signing_url = result.first_signing_url
    if first_signing_url is None:
        try:
            first_signing_url = get_access_link_signer(result.document_set_id, config, member_info_number=1)
        except SignixApiError as e:
            logger.error(
                "GetAccessLink failed after SubmitDocument success: %s. Creating transaction with empty first_signing_url.",
                e.message,
                exc_info=True,
            )
            first_signing_url = ""
    transaction = SignatureTransaction.objects.create(
        deal=deal,
        document_set=document_set,
        signix_document_set_id=result.document_set_id,
        transaction_id=metadata.get("transaction_id") or "",
        status=SignatureTransaction.STATUS_SUBMITTED,
        first_signing_url=first_signing_url or "",
    )
    for instance in document_set.instances.all():
        latest = instance.versions.first()
        if latest is not None:
            latest.status = VERSION_STATUS_SUBMITTED_TO_SIGNIX
            latest.save(update_fields=["status"])
    return transaction, first_signing_url or ""

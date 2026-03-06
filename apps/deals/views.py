"""
Views for the deals app (list, add, edit, delete).

All views require login. Lease officer defaults to request.user on create.
Delete uses GET for confirmation page and POST to perform delete.
"""

import logging
import threading
import os

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from apps.documents.exceptions import DocumentGenerationError
from apps.documents.services import (
    can_generate_documents,
    delete_document_set,
    generate_documents_for_deal,
    get_cannot_generate_reason,
    regenerate_documents,
)

from .forms import DealForm, SignixConfigForm
from .models import Deal, DealType, SignixConfig, SignatureTransaction
from .signix import (
    get_signix_config,
    get_event_type_display,
    get_push_base_url,
    get_signers_display,
    get_signers_detail_for_transaction,
    get_signature_transaction_for_push,
    get_signer_order_for_deal,
    get_status_updated_display,
    get_signer_authentication_for_slot,
    get_role_label_for_slot,
    resolve_signer_slot,
    validate_submit_preconditions,
    submit_document_set_for_signature,
    apply_push_action,
    push_action_to_event_type,
    get_event_time_for_push,
    download_signed_documents_on_complete,
    SignixValidationError,
    SignixApiError,
    AUTH_SELECT_ONE_CLICK,
    AUTH_SMS_ONE_CLICK,
    VERSION_STATUS_SUBMITTED_TO_SIGNIX,
)
from .models import SignatureTransactionEvent

logger = logging.getLogger(__name__)

def _document_set_template_for_deal(deal, document_set):
    """Return the document set template for the deal: from document_set if present, else from deal_type."""
    if document_set:
        template = getattr(document_set, "document_set_template", None)
        if template is not None:
            return template
    if getattr(deal, "deal_type_id", None) and deal.deal_type_id:
        from apps.doctemplates.models import DocumentSetTemplate
        return DocumentSetTemplate.objects.filter(deal_type=deal.deal_type).first()
    return None


def _build_signers_list(deal, document_set_template):
    """Build list of signer dicts for the template: slot, order_index, role_label, person, auth."""
    if not document_set_template:
        return []
    order = get_signer_order_for_deal(deal, document_set_template)
    signers = []
    for i, slot in enumerate(order, start=1):
        person = resolve_signer_slot(deal, slot)
        auth = get_signer_authentication_for_slot(deal, slot)
        role_label = get_role_label_for_slot(slot)
        signers.append({
            "slot": slot,
            "order_index": i,
            "role_label": role_label,
            "person": person,
            "auth": auth,
        })
    return signers


def _document_label_for_instance(instance):
    """Return a readable label for a document instance in tables."""
    template = getattr(instance, "source_document_template", None)
    if template is None:
        return "—"
    return (
        getattr(template, "ref_id", None)
        or getattr(template, "description", None)
        or f"Document {getattr(instance, 'order', '')}".strip()
        or "—"
    )


def _signature_transaction_detail_context(transaction):
    """Build the detail-page context for a signature transaction."""
    instances = list(transaction.document_set.instances.all()) if transaction.document_set_id else []
    documents = []
    for instance in instances:
        documents.append(
            {
                "instance": instance,
                "label": _document_label_for_instance(instance),
                "as_sent_version": instance.versions.filter(
                    status=VERSION_STATUS_SUBMITTED_TO_SIGNIX
                ).first(),
                "signed_version": instance.versions.filter(status="Final").first(),
            }
        )

    events = [
        {
            "event": event,
            "label": get_event_type_display(event.event_type),
        }
        for event in transaction.events.order_by("occurred_at", "pk")
    ]

    template = getattr(transaction.document_set, "document_set_template", None)
    return {
        "transaction": transaction,
        "transaction_identifier": transaction.transaction_id or transaction.signix_document_set_id or "—",
        "document_set_type": getattr(template, "name", None) or "—",
        "status_updated_display": get_status_updated_display(transaction),
        "signers": get_signers_detail_for_transaction(transaction),
        "documents": documents,
        "events": events,
        "has_audit_trail": bool(transaction.audit_trail_file),
        "has_certificate": bool(transaction.certificate_of_completion_file),
    }


def _signature_transaction_pdf_response(file_field, default_filename):
    """Return an inline PDF response for a stored transaction artifact."""
    if not file_field:
        raise Http404("This file is not available.")
    filename = os.path.basename(file_field.name) if getattr(file_field, "name", "") else default_filename
    response = FileResponse(
        file_field.open("rb"),
        content_type="application/pdf",
        as_attachment=False,
    )
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def _deal_detail_context(
    deal, document_set, can_generate,
    can_send_for_signature=None,
    cannot_send_for_signature_reason=None,
    open_signing_url=None,
):
    """Build context for deal detail template. Optionally pass can_send overrides for re-render after validation error."""
    document_set_template = _document_set_template_for_deal(deal, document_set)
    signers = _build_signers_list(deal, document_set_template) if document_set_template else []
    signature_transactions = list(deal.signature_transactions.order_by("-submitted_at"))
    for transaction in signature_transactions:
        transaction.signers_display = get_signers_display(transaction)
        transaction.status_updated_display = get_status_updated_display(transaction)
    if document_set is None:
        can_send = False
        cannot_send_reason = None
    elif can_send_for_signature is not None:
        can_send = can_send_for_signature
        cannot_send_reason = cannot_send_for_signature_reason
    else:
        try:
            validate_submit_preconditions(deal, document_set)
            can_send = True
            cannot_send_reason = None
        except SignixValidationError as e:
            can_send = False
            cannot_send_reason = "; ".join(e.errors) if e.errors else "Validation failed."
    ctx = {
        "deal": deal,
        "document_set": document_set,
        "can_generate": can_generate,
        "cannot_generate_reason": None if can_generate else get_cannot_generate_reason(deal),
        "can_send_for_signature": can_send,
        "cannot_send_for_signature_reason": cannot_send_reason,
        "signers": signers,
        "auth_choices": [
            (AUTH_SELECT_ONE_CLICK, AUTH_SELECT_ONE_CLICK),
            (AUTH_SMS_ONE_CLICK, AUTH_SMS_ONE_CLICK),
        ],
        "signature_transactions": signature_transactions,
        "get_signers_display": get_signers_display,
        "get_status_updated_display": get_status_updated_display,
    }
    if open_signing_url is not None:
        ctx["open_signing_url"] = open_signing_url
    return ctx


@login_required
def deal_detail(request, pk):
    """Show read-only deal summary including deal type; Edit and Delete buttons; Documents section."""
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__document_set_template", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    can_generate = can_generate_documents(deal)
    open_signing_url = None
    if "signix_open_signing_url" in request.session:
        open_signing_url = request.session.pop("signix_open_signing_url")
    return render(
        request,
        "deals/deal_detail.html",
        _deal_detail_context(deal, document_set, can_generate, open_signing_url=open_signing_url),
    )


@login_required
def deal_generate_documents(request, pk):
    """POST: run document generation for the deal; redirect to deal detail or show error."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__document_set_template", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    try:
        generate_documents_for_deal(deal, request=request)
        messages.success(request, "Documents generated.")
        return redirect("deals:deal_detail", pk=pk)
    except DocumentGenerationError as e:
        messages.error(request, str(e))
        document_set = deal.document_sets.first()
        can_generate = can_generate_documents(deal)
        return render(
            request,
            "deals/deal_detail.html",
            _deal_detail_context(deal, document_set, can_generate),
        )


@login_required
def deal_regenerate_documents(request, pk):
    """POST: regenerate document set (new versions); redirect to deal detail or show error."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__document_set_template", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    if not document_set:
        messages.error(request, "No document set to regenerate.")
        return redirect("deals:deal_detail", pk=pk)
    try:
        regenerate_documents(document_set, request=request)
        messages.success(request, "Documents regenerated.")
        return redirect("deals:deal_detail", pk=pk)
    except DocumentGenerationError as e:
        messages.error(request, str(e))
        can_generate = can_generate_documents(deal)
        return render(
            request,
            "deals/deal_detail.html",
            _deal_detail_context(deal, document_set, can_generate),
        )


@login_required
def deal_delete_document_set(request, pk):
    """POST: delete the deal's document set and redirect to deal detail."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__document_set_template", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    if not document_set:
        messages.error(request, "No document set to delete.")
        return redirect("deals:deal_detail", pk=pk)
    try:
        delete_document_set(document_set)
        messages.success(request, "Document set deleted.")
    except DocumentGenerationError as e:
        messages.error(request, str(e))
    return redirect("deals:deal_detail", pk=pk)


@login_required
def deal_send_for_signature(request, pk):
    """POST: submit document set to SIGNiX; on success redirect to deal detail and open signing URL in new window (Option A)."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("lease_officer", "deal_type").prefetch_related(
            "vehicles", "contacts", "document_sets__document_set_template", "document_sets__instances__versions"
        ),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    if not document_set:
        messages.error(request, "No document set to send.")
        return redirect("deals:deal_detail", pk=pk)
    try:
        _tx, first_signing_url = submit_document_set_for_signature(
            deal,
            document_set,
            request=request,
        )
    except SignixValidationError as e:
        reason = "; ".join(e.errors) if e.errors else "Validation failed."
        messages.error(request, reason)
        can_generate = can_generate_documents(deal)
        context = _deal_detail_context(
            deal, document_set, can_generate,
            can_send_for_signature=False,
            cannot_send_for_signature_reason=reason,
        )
        return render(request, "deals/deal_detail.html", context)
    except SignixApiError as e:
        messages.error(
            request,
            f"SIGNiX request failed; try again or contact support. ({getattr(e, 'message', str(e))})",
        )
        return redirect("deals:deal_detail", pk=pk)
    messages.success(request, "Documents sent for signature.")
    if first_signing_url:
        request.session["signix_open_signing_url"] = first_signing_url
    else:
        messages.info(
            request,
            "Transaction created; signing link could not be retrieved. You can check the transaction or contact support.",
        )
    return redirect("deals:deal_detail", pk=pk)


@login_required
def signature_transaction_list(request):
    """List all signature transactions (Plan 8 dashboard)."""
    transactions = list(
        SignatureTransaction.objects.all()
        .order_by("-submitted_at")
        .select_related("deal", "deal__deal_type", "document_set", "document_set__document_set_template")
    )
    for transaction in transactions:
        transaction.signers_display = get_signers_display(transaction)
        transaction.status_updated_display = get_status_updated_display(transaction)
    return render(
        request,
        "deals/signature_transaction_list.html",
        {"signature_transaction_list": transactions},
    )


@login_required
def signature_transaction_detail(request, pk):
    """Show one signature transaction with signer, document, and event details."""
    transaction = get_object_or_404(
        SignatureTransaction.objects.select_related(
            "deal",
            "document_set",
            "document_set__document_set_template",
        ).prefetch_related(
            "deal__contacts",
            "events",
            "document_set__instances__versions",
        ),
        pk=pk,
    )
    return render(
        request,
        "deals/signature_transaction_detail.html",
        _signature_transaction_detail_context(transaction),
    )


@login_required
def signature_transaction_audit_trail(request, pk):
    """Serve the stored SIGNiX audit trail PDF inline."""
    transaction = get_object_or_404(
        SignatureTransaction.objects.select_related("deal"),
        pk=pk,
    )
    return _signature_transaction_pdf_response(
        transaction.audit_trail_file,
        "audit_trail.pdf",
    )


@login_required
def signature_transaction_certificate(request, pk):
    """Serve the stored SIGNiX certificate of completion PDF inline."""
    transaction = get_object_or_404(
        SignatureTransaction.objects.select_related("deal"),
        pk=pk,
    )
    return _signature_transaction_pdf_response(
        transaction.certificate_of_completion_file,
        "certificate_of_completion.pdf",
    )


@login_required
def signature_transaction_delete_all(request):
    """GET: show confirmation page. POST: delete all signature transactions and redirect to list (Plan 8)."""
    if request.method == "POST":
        count = SignatureTransaction.objects.count()
        SignatureTransaction.objects.all().delete()
        messages.success(request, f"All signature transaction records ({count}) have been removed.")
        return redirect("deals:signature_transaction_list")
    return render(request, "deals/signature_transaction_delete_all_confirm.html")


@login_required
def deal_signature_transaction_delete_all(request, pk):
    """GET: show confirmation page. POST: delete this deal's signature transactions and redirect to deal detail (Plan 9)."""
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == "POST":
        count = SignatureTransaction.objects.filter(deal_id=pk).count()
        SignatureTransaction.objects.filter(deal_id=pk).delete()
        messages.success(request, f"All signature transaction records for this deal ({count}) have been removed.")
        return redirect("deals:deal_detail", pk=pk)
    return render(request, "deals/deal_signature_transaction_delete_all_confirm.html", {"deal": deal})


@login_required
def deal_signers_update_auth(request, pk):
    """POST: save signer authentication for all slots; redirect back to deal detail."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(
        Deal.objects.select_related("deal_type").prefetch_related("document_sets__document_set_template"),
        pk=pk,
    )
    document_set = deal.document_sets.first()
    template = _document_set_template_for_deal(deal, document_set)
    if not template:
        messages.error(request, "No document set template for this deal.")
        return redirect("deals:deal_detail", pk=pk)
    order = get_signer_order_for_deal(deal, template)
    auth_map = dict(deal.signer_authentication) if isinstance(deal.signer_authentication, dict) else {}
    valid = {AUTH_SELECT_ONE_CLICK, AUTH_SMS_ONE_CLICK}
    for slot in order:
        key = f"auth_{slot}"
        value = request.POST.get(key)
        if value in valid:
            auth_map[str(slot)] = value
    deal.signer_authentication = auth_map
    deal.save(update_fields=["signer_authentication"])
    messages.success(request, "Signer settings saved.")
    return redirect("deals:deal_detail", pk=pk)


@login_required
def deal_signers_reorder(request, pk):
    """POST: move a signer up or down; redirect back to deal detail."""
    if request.method != "POST":
        return redirect("deals:deal_detail", pk=pk)
    deal = get_object_or_404(Deal.objects.select_related("deal_type").prefetch_related("document_sets__document_set_template"), pk=pk)
    document_set = deal.document_sets.first()
    template = _document_set_template_for_deal(deal, document_set)
    if not template:
        messages.error(request, "No document set template for this deal.")
        return redirect("deals:deal_detail", pk=pk)
    order = get_signer_order_for_deal(deal, template)
    action = request.POST.get("action")
    try:
        slot = int(request.POST.get("slot", 0))
    except (TypeError, ValueError):
        slot = 0
    if action == "move_up" and slot in order:
        idx = order.index(slot)
        if idx > 0:
            order = list(order)
            order[idx], order[idx - 1] = order[idx - 1], order[idx]
            deal.signer_order = order
            deal.save(update_fields=["signer_order"])
            messages.success(request, "Signer order updated.")
    elif action == "move_down" and slot in order:
        idx = order.index(slot)
        if idx < len(order) - 1:
            order = list(order)
            order[idx], order[idx + 1] = order[idx + 1], order[idx]
            deal.signer_order = order
            deal.save(update_fields=["signer_order"])
            messages.success(request, "Signer order updated.")
    return redirect("deals:deal_detail", pk=pk)


@csrf_exempt
def signix_push(request):
    """Public SIGNiX push listener: apply status updates and record an event."""
    try:
        action = (request.GET.get("action") or "").strip()
        signix_document_set_id = (request.GET.get("id") or "").strip()
        transaction_id = (request.GET.get("extid") or "").strip()
        pid = (request.GET.get("pid") or "").strip()
        refid = (request.GET.get("refid") or "").strip()
        ts = (request.GET.get("ts") or "").strip()

        if not action or not signix_document_set_id or not transaction_id:
            logger.warning(
                "Push request missing required parameter (action=%r, id=%r, extid=%r)",
                action,
                signix_document_set_id,
                transaction_id,
            )
            return HttpResponse("OK", status=200, content_type="text/plain")

        transaction = get_signature_transaction_for_push(
            signix_document_set_id=signix_document_set_id,
            transaction_id=transaction_id,
        )
        if transaction is None:
            logger.warning(
                "Push request transaction not found (id=%s, extid=%s)",
                signix_document_set_id,
                transaction_id,
            )
            return HttpResponse("OK", status=200, content_type="text/plain")

        apply_push_action(transaction, action, refid=refid, pid=pid, ts=ts)
        transaction.save(
            update_fields=[
                "status",
                "completed_at",
                "status_last_updated",
                "signers_completed_refids",
                "signers_completed_count",
            ]
        )

        SignatureTransactionEvent.objects.create(
            signature_transaction=transaction,
            event_type=push_action_to_event_type(action),
            occurred_at=get_event_time_for_push(ts),
            refid=refid,
            pid=pid,
        )

        if action == "complete":
            thread = threading.Thread(
                target=download_signed_documents_on_complete,
                args=(transaction,),
                daemon=True,
            )
            thread.start()
    except Exception:
        logger.exception("Unhandled error while processing SIGNiX push")
    return HttpResponse("OK", status=200, content_type="text/plain")


@login_required
def deal_list(request):
    """List all deals (date entered, lease officer, dates, payment, vehicles/contacts count)."""
    deals = Deal.objects.all().select_related(
        "lease_officer", "deal_type"
    ).prefetch_related("vehicles", "contacts")
    return render(request, "deals/deal_list.html", {"deal_list": deals})


@login_required
def deal_add(request):
    """Show form to add a deal; on valid POST create with lease_officer=request.user."""
    if request.method == "POST":
        form = DealForm(request.POST)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.lease_officer = request.user
            deal.deal_type = DealType.get_default()
            deal.save()
            form.save_m2m()
            messages.success(request, "Deal added.")
            return redirect("deals:deal_list")
    else:
        form = DealForm()
    return render(
        request,
        "deals/deal_form.html",
        {"form": form, "lease_officer": request.user, "is_edit": False},
    )


@login_required
def deal_edit(request, pk):
    """Show form to edit a deal; on valid POST update and redirect to list."""
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == "POST":
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            form.save()
            messages.success(request, "Deal updated.")
            return redirect("deals:deal_list")
    else:
        form = DealForm(instance=deal)
    return render(
        request,
        "deals/deal_form.html",
        {"form": form, "deal": deal, "lease_officer": deal.lease_officer, "is_edit": True},
    )


@login_required
def deal_delete_confirm(request, pk):
    """GET: show confirmation page. POST: delete deal and redirect to list."""
    deal = get_object_or_404(Deal.objects.select_related("lease_officer"), pk=pk)
    if request.method == "POST":
        deal.delete()
        messages.success(request, "Deal deleted.")
        return redirect("deals:deal_list")
    return render(request, "deals/deal_confirm_delete.html", {"deal": deal})


@login_required
@user_passes_test(lambda u: u.is_staff)
def signix_config_edit(request):
    """GET: show SIGNiX Configuration form. POST: save and redirect with success message."""
    config = get_signix_config()
    if request.method == "POST":
        form = SignixConfigForm(request.POST, instance=config)
        if form.is_valid():
            instance = form.save(commit=False)
            # Keep existing password when editing and password field left blank
            if instance.pk and not form.cleaned_data.get("password"):
                instance.password = SignixConfig.objects.get(pk=instance.pk).password
            instance.save()
            messages.success(request, "SIGNiX configuration saved.")
            return redirect("signix_config")
    else:
        form = SignixConfigForm(instance=config)
    return render(
        request,
        "deals/signix_config_form.html",
        {
            "form": form,
            "derived_push_base_url": get_push_base_url(request),
        },
    )

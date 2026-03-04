"""
Tests for Plan 7: Send for Signature view (deal_send_for_signature, deal detail context).
Plan 7 Batch 3: view tests for all branches; deal detail context with document set.
"""

from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.deals.models import Deal, DealType, SignixConfig
from apps.deals.signix import get_signix_config, SignixValidationError, SignixApiError
from apps.users.models import LeaseOfficerProfile
from apps.contacts.models import Contact
from apps.doctemplates.models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
)
from apps.documents.models import DocumentSet, DocumentInstance, DocumentInstanceVersion
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


def _make_pdf():
    return SimpleUploadedFile("doc.pdf", b"%PDF-1.4 minimal", content_type="application/pdf")


class DealSendForSignatureViewTests(TestCase):
    """Plan 7 Batch 1: deal_send_for_signature view behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="senduser",
            email="send@example.com",
            password="test",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Send",
            last_name="User",
            email="send@example.com",
            phone_number="555-0000",
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("300.00"),
        )

    def test_get_redirects_to_deal_detail(self):
        """GET send-for-signature redirects to deal detail."""
        url = reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))

    def test_post_no_document_set_redirects_with_error(self):
        """POST when deal has no document set: error message and redirect to deal detail."""
        url = reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No document set")


@patch("apps.deals.views.submit_document_set_for_signature")
class DealSendForSignatureWithDocumentSetTests(TestCase):
    """Plan 7 Batch 3: deal_send_for_signature with mocked orchestrator when deal has a document set."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="senduser2",
            email="send2@example.com",
            password="test",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Send",
            last_name="User",
            email="send2@example.com",
            phone_number="555-0000",
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("300.00"),
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Plan7 Test Template"},
        )
        self.document_set = DocumentSet.objects.create(
            deal=self.deal,
            document_set_template=self.doc_set_tpl,
        )

    def test_post_success_sets_session_then_cleared_on_deal_detail(self, mock_submit):
        """POST with valid deal/document_set (mock success): redirect, success message, session set then cleared."""
        mock_tx = MagicMock()
        mock_submit.return_value = (mock_tx, "https://sign.example.com/link")
        url = reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(self.client.session.get("signix_open_signing_url"), "https://sign.example.com/link")
        # GET deal detail clears the session key
        resp2 = self.client.get(resp["Location"])
        self.assertEqual(resp2.status_code, 200)
        self.assertIsNone(self.client.session.get("signix_open_signing_url"))
        self.assertContains(resp2, "Documents sent for signature")

    def test_post_validation_error_render_with_error_message(self, mock_submit):
        """POST with validation failure (mock SignixValidationError): re-render deal detail with error, no redirect."""
        mock_submit.side_effect = SignixValidationError(["Signer slot 2 could not be resolved to a person."])
        url = reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Signer slot 2")
        self.assertTemplateUsed(resp, "deals/deal_detail.html")

    def test_post_api_error_redirect_with_generic_message(self, mock_submit):
        """POST with SignixApiError: generic message, redirect to deal detail."""
        mock_submit.side_effect = SignixApiError("Server error")
        url = reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "SIGNiX request failed")
        self.assertContains(resp, "try again or contact support")


class DealDetailContextTests(TestCase):
    """Plan 7 Batch 1: deal detail context includes can_send_for_signature and cannot_send_for_signature_reason."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="ctxuser",
            email="ctx@example.com",
            password="test",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Ctx",
            last_name="User",
            email="ctx@example.com",
            phone_number="555-0000",
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("300.00"),
        )

    def test_deal_detail_without_document_set_has_can_send_false(self):
        """Deal with no document set: context has can_send_for_signature False (button not shown)."""
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["can_send_for_signature"])
        self.assertIsNone(resp.context["cannot_send_for_signature_reason"])


class DealDetailContextWithDocumentSetTests(TestCase):
    """Plan 7 Batch 3: deal detail context can_send_for_signature when document set exists."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="ctxuser2",
            email="ctx2@example.com",
            password="test",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Ctx",
            last_name="User",
            email="ctx2@example.com",
            phone_number="555-0000",
        )
        self.contact = Contact.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone_number="555-1111",
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("300.00"),
        )
        self.deal.contacts.add(self.contact)
        self.static_tpl = StaticDocumentTemplate.objects.create(
            ref_id="Plan7Ctx",
            description="Plan 7 context test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Plan7 Context Template"},
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=self.doc_set_tpl,
            order=1,
            content_type=ct,
            object_id=self.static_tpl.pk,
        )
        self.document_set = DocumentSet.objects.create(
            deal=self.deal,
            document_set_template=self.doc_set_tpl,
        )
        self.instance = DocumentInstance.objects.create(
            document_set=self.document_set,
            order=1,
            content_type=ct,
            object_id=self.static_tpl.pk,
            template_type="static",
        )
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance,
            version_number=1,
            status="Draft",
            file=_make_pdf(),
        )
        config = get_signix_config()
        config.submitter_email = "submitter@example.com"
        config.save()

    def test_deal_detail_with_document_set_and_valid_config_can_send_true(self):
        """When document_set exists and validation passes, can_send_for_signature is True."""
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["can_send_for_signature"])
        self.assertIsNone(resp.context["cannot_send_for_signature_reason"])

    def test_deal_detail_with_document_set_unresolved_signer_can_send_false(self):
        """When document_set exists but a signer slot cannot be resolved, can_send_for_signature is False."""
        self.deal.contacts.remove(self.contact)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["can_send_for_signature"])
        self.assertIsNotNone(resp.context["cannot_send_for_signature_reason"])
        self.assertIn("could not be resolved", resp.context["cannot_send_for_signature_reason"])

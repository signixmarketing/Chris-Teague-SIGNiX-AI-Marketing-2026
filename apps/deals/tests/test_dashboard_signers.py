"""
Tests for Plan 4: SIGNiX dashboard Signers and Status updated columns.
"""

from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.deals.models import Deal, DealType, SignatureTransaction
from apps.deals.signix import get_signers_display, get_status_updated_display
from apps.deals.views import _deal_detail_context
from apps.documents.models import DocumentSet

User = get_user_model()


class DashboardSignersBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashsigners",
            email="dashsigners@example.com",
            password="test",
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
        self.doc_set = DocumentSet.objects.create(deal=self.deal, document_set_template=None)


class GetSignersDisplayTests(TestCase):
    def test_signers_display_normal(self):
        tx = SignatureTransaction(signer_count=2, signers_completed_count=1)
        self.assertEqual(get_signers_display(tx), "1/2")

    def test_signers_display_zero_of_two(self):
        tx = SignatureTransaction(signer_count=2, signers_completed_count=0)
        self.assertEqual(get_signers_display(tx), "0/2")

    def test_signers_display_all_complete(self):
        tx = SignatureTransaction(signer_count=2, signers_completed_count=2)
        self.assertEqual(get_signers_display(tx), "2/2")

    def test_signers_display_null_signer_count(self):
        tx = SignatureTransaction(signer_count=None, signers_completed_count=1)
        self.assertEqual(get_signers_display(tx), "—")

    def test_signers_display_null_completed_count_treated_as_zero(self):
        tx = SignatureTransaction(signer_count=2, signers_completed_count=None)
        self.assertEqual(get_signers_display(tx), "0/2")

    def test_signers_display_zero_signers(self):
        tx = SignatureTransaction(signer_count=0, signers_completed_count=0)
        self.assertEqual(get_signers_display(tx), "0/0")


class GetStatusUpdatedDisplayTests(TestCase):
    def test_status_updated_display_with_value(self):
        tx = SignatureTransaction(
            status_last_updated=timezone.make_aware(datetime(2025, 3, 15, 14, 30))
        )
        self.assertEqual(get_status_updated_display(tx), "Mar 15, 2025 2:30 PM")

    def test_status_updated_display_null_returns_dash(self):
        tx = SignatureTransaction(status_last_updated=None)
        self.assertEqual(get_status_updated_display(tx), "—")

    def test_status_updated_display_fallback_to_submitted_at(self):
        tx = SignatureTransaction(
            status_last_updated=None,
            submitted_at=timezone.make_aware(datetime(2025, 3, 15, 14, 30)),
        )
        self.assertEqual(
            get_status_updated_display(tx, fallback_to_submitted_at=True),
            "Mar 15, 2025 2:30 PM",
        )

    def test_status_updated_display_null_and_no_fallback(self):
        tx = SignatureTransaction(
            status_last_updated=None,
            submitted_at=timezone.make_aware(datetime(2025, 3, 15, 14, 30)),
        )
        self.assertEqual(get_status_updated_display(tx, fallback_to_submitted_at=False), "—")


class SignatureTransactionListSignersTests(DashboardSignersBase):
    def test_list_includes_signers_and_status_updated_columns(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SIGNERS-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
            signer_count=2,
            signers_completed_count=0,
        )
        response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signers")
        self.assertContains(response, "Status updated")
        self.assertContains(response, "0/2")

    def test_list_signers_column_value(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SIGNERS-2",
            status=SignatureTransaction.STATUS_IN_PROGRESS,
            signer_count=2,
            signers_completed_count=1,
        )
        response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertContains(response, "1/2")

    def test_list_status_updated_shows_dash_when_null(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SIGNERS-3",
            status=SignatureTransaction.STATUS_SUBMITTED,
            signer_count=2,
            signers_completed_count=0,
            status_last_updated=None,
        )
        response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertContains(response, "—")

    def test_list_empty_state_colspan(self):
        response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'colspan="9"', html=False)

    def test_list_legacy_signer_count_none_shows_dash(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SIGNERS-4",
            status=SignatureTransaction.STATUS_SUBMITTED,
            signer_count=None,
        )
        response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertContains(response, "—")


class DealDetailSignersTests(DashboardSignersBase):
    def test_deal_detail_signature_table_has_signers_and_status_updated(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-DETAIL-1",
            status=SignatureTransaction.STATUS_IN_PROGRESS,
            signer_count=2,
            signers_completed_count=1,
        )
        response = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signers")
        self.assertContains(response, "Status updated")
        self.assertContains(response, "1/2")

    def test_deal_detail_signers_null_safe(self):
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-DETAIL-2",
            status=SignatureTransaction.STATUS_SUBMITTED,
            signer_count=None,
        )
        response = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "—")

    def test_deal_detail_context_includes_helper_callables(self):
        transaction = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-DETAIL-3",
            status=SignatureTransaction.STATUS_SUBMITTED,
            signer_count=2,
            signers_completed_count=0,
        )
        context = _deal_detail_context(self.deal, self.doc_set, can_generate=False)
        self.assertIn("get_signers_display", context)
        self.assertIn("get_status_updated_display", context)
        self.assertTrue(callable(context["get_signers_display"]))
        self.assertTrue(callable(context["get_status_updated_display"]))
        self.assertEqual(context["get_signers_display"](transaction), "0/2")
        self.assertEqual(context["get_status_updated_display"](transaction), "—")

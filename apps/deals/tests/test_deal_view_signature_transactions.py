"""
Tests for Plan 9: Deal View — Related signature transactions.
Batches 1–3: subsection, table, empty state, delete for this deal, re-render context.
"""

from decimal import Decimal
from datetime import date
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.deals.models import Deal, DealType, SignatureTransaction
from apps.documents.models import DocumentSet
from apps.deals.signix import SignixValidationError

User = get_user_model()


class DealDetailSignatureTransactionsTests(TestCase):
    """Plan 9 Batch 1: deal detail shows Signature transactions subsection."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="dealviewuser",
            email="dealview@example.com",
            password="test",
        )
        self.client = Client()
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

    def test_deal_detail_includes_signature_transactions_subsection(self):
        """Deal detail page contains the Signature transactions card and View all link."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Signature transactions")
        self.assertContains(resp, "View all signature transactions")
        self.assertContains(resp, reverse("deals:signature_transaction_list"))

    def test_deal_detail_empty_state_when_no_transactions(self):
        """When deal has no signature transactions, subsection shows empty state message."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No signature transactions for this deal.")

    def test_deal_detail_shows_transactions_table_when_transactions_exist(self):
        """When deal has signature transactions, table shows rows with Submitted at, DocumentSetID, Status."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-P9-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "DS-P9-1")
        self.assertContains(resp, "Submitted")
        self.assertContains(resp, "Submitted at")
        self.assertContains(resp, "SIGNiX DocumentSetID")
        self.assertContains(resp, "Open signing")

    def test_deal_detail_shows_open_signing_when_url_and_status_allow(self):
        """Open signing link appears when first_signing_url is set and status is Submitted."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-P9-2",
            status=SignatureTransaction.STATUS_SUBMITTED,
            first_signing_url="https://sign.example.com/deal-sign",
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Open signing")
        self.assertContains(resp, "https://sign.example.com/deal-sign")


class DealSignatureTransactionDeleteAllTests(TestCase):
    """Plan 9 Batch 2: deal-scoped delete all (deal_signature_transaction_delete_all)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="deldealuser",
            email="deldeal@example.com",
            password="test",
        )
        self.client = Client()
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

    def test_delete_all_get_requires_login(self):
        """Unauthenticated GET redirects to login."""
        url = reverse("deals:deal_signature_transaction_delete_all", kwargs={"pk": self.deal.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_delete_all_get_returns_200_and_confirmation_content(self):
        """Authenticated GET returns 200 and confirmation page with 'for this deal' and Cancel to deal detail."""
        self.client.force_login(self.user)
        url = reverse("deals:deal_signature_transaction_delete_all", kwargs={"pk": self.deal.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "for this deal")
        self.assertContains(resp, "Delete all")
        self.assertContains(resp, "Cancel")
        self.assertContains(resp, reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))

    def test_delete_all_post_deletes_only_this_deal_and_redirects_to_deal_detail(self):
        """POST deletes only this deal's transactions and redirects to deal detail with success message."""
        other_deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 2),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("400.00"),
        )
        other_doc_set = DocumentSet.objects.create(deal=other_deal, document_set_template=None)
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-DEAL-A",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        SignatureTransaction.objects.create(
            deal=other_deal,
            document_set=other_doc_set,
            signix_document_set_id="DS-DEAL-B",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.assertEqual(SignatureTransaction.objects.filter(deal=self.deal).count(), 1)
        self.assertEqual(SignatureTransaction.objects.filter(deal=other_deal).count(), 1)
        self.client.force_login(self.user)
        url = reverse("deals:deal_signature_transaction_delete_all", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SignatureTransaction.objects.filter(deal=self.deal).count(), 0)
        self.assertEqual(SignatureTransaction.objects.filter(deal=other_deal).count(), 1)
        self.assertContains(resp, "removed")
        self.assertContains(resp, "for this deal")

    def test_deal_detail_shows_delete_button_when_transactions_exist(self):
        """Delete Transaction History button appears when deal has signature transactions."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-X",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertContains(resp, "Delete Transaction History")
        self.assertContains(resp, reverse("deals:deal_signature_transaction_delete_all", kwargs={"pk": self.deal.pk}))

    def test_deal_detail_hides_delete_button_when_no_transactions(self):
        """Delete Transaction History button is not shown when deal has no signature transactions."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertNotContains(resp, "Delete Transaction History")


class DealViewSignatureTransactionsBatch3Tests(TestCase):
    """Plan 9 Batch 3: re-render context, delete POST requires login, open signing only when allowed."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="batch3user",
            email="b3@example.com",
            password="test",
        )
        self.client = Client()
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

    def test_delete_all_post_requires_login(self):
        """Unauthenticated POST to deal-scoped delete-all redirects to login."""
        url = reverse("deals:deal_signature_transaction_delete_all", kwargs={"pk": self.deal.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_open_signing_not_shown_when_status_complete(self):
        """Open signing link is not shown when status is Complete (same rule as Plan 8)."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-COMPLETE",
            status=SignatureTransaction.STATUS_COMPLETE,
            first_signing_url="https://sign.example.com/complete",
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "DS-COMPLETE")
        self.assertContains(resp, "Complete")
        # Signing URL should not be linked (column header "Open signing" is always present)
        self.assertNotContains(resp, "https://sign.example.com/complete")

    @patch("apps.deals.views.submit_document_set_for_signature")
    def test_render_after_validation_error_includes_signature_transactions_subsection(self, mock_submit):
        """Plan 9 Batch 3 polish: re-render after Plan 7 validation error still shows Signature transactions."""
        mock_submit.side_effect = SignixValidationError(["Validation error for test"])
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("deals:deal_send_for_signature", kwargs={"pk": self.deal.pk}),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Signature transactions")
        self.assertTemplateUsed(resp, "deals/deal_detail.html")

"""
Tests for Plan 8: Signature transactions dashboard (list, delete-all, sidebar).
Batches 1–3: list view, delete-all flow, sidebar/UI, polish (empty state, date format).
"""

from decimal import Decimal
from datetime import date, datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.deals.models import Deal, DealType, SignatureTransaction
from apps.documents.models import DocumentSet
from apps.doctemplates.models import DocumentSetTemplate
from django.contrib.auth import get_user_model

User = get_user_model()


class SignatureTransactionListViewTests(TestCase):
    """Plan 8 Batch 1: signature_transaction_list view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboarduser",
            email="dash@example.com",
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

    def test_list_requires_login(self):
        """Unauthenticated request redirects to login."""
        url = reverse("deals:signature_transaction_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_list_returns_200_with_empty_table(self):
        """Authenticated GET returns 200 and empty table."""
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Signature transactions")
        self.assertContains(resp, "No signature transactions yet")

    def test_list_shows_transaction_and_deal_link(self):
        """When transactions exist, table shows deal link and columns."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-TEST-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Deal #" + str(self.deal.pk))
        self.assertContains(resp, "DS-TEST-1")
        self.assertContains(resp, "Submitted")

    def test_list_shows_open_link_when_url_and_status_allow(self):
        """Open link appears when first_signing_url is set and status is Submitted."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-TEST-2",
            status=SignatureTransaction.STATUS_SUBMITTED,
            first_signing_url="https://sign.example.com/link",
        )
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Open link")
        self.assertContains(resp, "https://sign.example.com/link")

    def test_list_open_link_not_shown_when_status_not_submitted_or_in_progress(self):
        """Open link is not shown when status is Complete (or other non-allowed status)."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-NO-LINK",
            status=SignatureTransaction.STATUS_COMPLETE,
            first_signing_url="https://sign.example.com/complete",
        )
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "DS-NO-LINK")
        self.assertContains(resp, "Complete")
        # Column header "Open link" is always present; assert the signing URL is not linked in the table
        self.assertNotContains(resp, "https://sign.example.com/complete")

    def test_list_empty_state_shows_expected_message(self):
        """Empty list shows the planned empty-state message."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertContains(resp, "No signature transactions yet")
        self.assertContains(resp, "Send documents for signature from a Deal detail page")

    def test_list_submitted_at_date_format(self):
        """Submitted at column uses M j, Y g:i A format."""
        submitted = timezone.make_aware(datetime(2025, 3, 15, 14, 30))
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-DATE",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        SignatureTransaction.objects.filter(pk=tx.pk).update(submitted_at=submitted)
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mar 15, 2025 2:30 PM")


class SignatureTransactionDeleteAllTests(TestCase):
    """Plan 8 Batch 2: signature_transaction_delete_all view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="deluser",
            email="del@example.com",
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
        url = reverse("deals:signature_transaction_delete_all")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_delete_all_post_requires_login(self):
        """Unauthenticated POST redirects to login."""
        url = reverse("deals:signature_transaction_delete_all")
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_delete_all_get_returns_200_and_confirmation_content(self):
        """Authenticated GET returns 200 and confirmation page content."""
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_delete_all")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Delete transaction history")
        self.assertContains(resp, "remove")
        self.assertContains(resp, "signature transaction")
        self.assertContains(resp, "Delete all")
        self.assertContains(resp, "Cancel")

    def test_delete_all_post_deletes_all_and_redirects_with_message(self):
        """POST deletes all SignatureTransaction records and redirects to list with success message."""
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-A",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-B",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.assertEqual(SignatureTransaction.objects.count(), 2)
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_delete_all")
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SignatureTransaction.objects.count(), 0)
        self.assertContains(resp, "removed")
        self.assertContains(resp, "All signature transaction records")
        self.assertContains(resp, "(2)")

    def test_delete_all_post_empty_shows_zero_in_message(self):
        """POST when no records still redirects and shows success (0 removed)."""
        self.client.force_login(self.user)
        url = reverse("deals:signature_transaction_delete_all")
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "All signature transaction records")
        self.assertContains(resp, "0")


class SignatureTransactionListUITests(TestCase):
    """Plan 8 Batch 2: list page has Delete button and sidebar shows Signature transactions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="uiuser",
            email="ui@example.com",
            password="test",
        )
        self.client = Client()

    def test_list_page_contains_delete_transaction_history_button(self):
        """List page contains 'Delete Transaction History' button linking to delete-all."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Delete Transaction History")
        self.assertContains(resp, reverse("deals:signature_transaction_delete_all"))

    def test_list_page_sidebar_contains_signature_transactions_link(self):
        """Sidebar contains 'Signature transactions' link on list page."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Signature transactions")
        self.assertContains(resp, reverse("deals:signature_transaction_list"))

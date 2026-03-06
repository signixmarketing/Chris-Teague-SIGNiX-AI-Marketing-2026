"""
Tests for Plan 1 (Dashboard/Sync): SIGNiX Sync Model — SignatureTransaction
per-signer fields and Expired status, SignixConfig.push_base_url.

Run after implementing PLAN-SIGNiX-SYNC-MODEL.md:
  python manage.py test apps.deals.tests.test_sync_model
"""

from decimal import Decimal
from datetime import date

from django.test import TestCase

from apps.deals.models import Deal, DealType, SignatureTransaction, SignixConfig
from apps.deals.signix import get_signix_config
from apps.documents.models import DocumentSet
from django.contrib.auth import get_user_model

User = get_user_model()


class SignatureTransactionSyncFieldsTests(TestCase):
    """Plan 1 Batch 1: SignatureTransaction — STATUS_EXPIRED and signer_count, signers_completed_refids, signers_completed_count."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="syncuser",
            email="sync@example.com",
            password="test",
        )
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

    def test_expired_status_constant_exists(self):
        """STATUS_EXPIRED constant is defined and equals 'Expired'."""
        self.assertTrue(hasattr(SignatureTransaction, "STATUS_EXPIRED"))
        self.assertEqual(SignatureTransaction.STATUS_EXPIRED, "Expired")

    def test_status_choices_include_expired(self):
        """STATUS_CHOICES includes Expired so the field accepts it."""
        choice_values = [choice[0] for choice in SignatureTransaction.STATUS_CHOICES]
        self.assertIn(SignatureTransaction.STATUS_EXPIRED, choice_values)

    def test_create_without_sync_fields_uses_defaults(self):
        """Creating with only required fields leaves sync fields as defaults."""
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SYNC-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        self.assertIsNone(tx.signer_count)
        self.assertEqual(tx.signers_completed_refids, [])
        self.assertEqual(tx.signers_completed_count, 0)

    def test_create_with_sync_fields_persists(self):
        """signer_count, signers_completed_refids, signers_completed_count persist."""
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SYNC-2",
            status=SignatureTransaction.STATUS_IN_PROGRESS,
            signer_count=2,
            signers_completed_refids=["P01", "P02"],
            signers_completed_count=2,
        )
        tx.refresh_from_db()
        self.assertEqual(tx.signer_count, 2)
        self.assertEqual(tx.signers_completed_refids, ["P01", "P02"])
        self.assertEqual(tx.signers_completed_count, 2)

    def test_status_expired_can_be_saved(self):
        """Transaction can be saved with status Expired."""
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SYNC-3",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        tx.status = SignatureTransaction.STATUS_EXPIRED
        tx.save()
        tx.refresh_from_db()
        self.assertEqual(tx.status, SignatureTransaction.STATUS_EXPIRED)


class SignixConfigPushBaseUrlTests(TestCase):
    """Plan 1 Batch 2: SignixConfig.push_base_url."""

    def test_push_base_url_default_blank(self):
        """get_signix_config() returns config with push_base_url blank by default."""
        config = get_signix_config()
        self.assertEqual(config.push_base_url, "")

    def test_push_base_url_persists(self):
        """push_base_url can be set and persists."""
        config = get_signix_config()
        config.push_base_url = "https://test.ngrok-free.dev"
        config.save()
        config.refresh_from_db()
        self.assertEqual(config.push_base_url, "https://test.ngrok-free.dev")

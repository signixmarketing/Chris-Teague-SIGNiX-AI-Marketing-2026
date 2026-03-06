"""
Tests for Plan 1 (Dashboard/Sync): SIGNiX Sync Model.

Batch 1 tests cover SignatureTransaction per-signer/status fields and the legacy
row backfill logic. Batch 2 tests cover SignixConfig.push_base_url. Batch 3
tests cover SignatureTransactionEvent.

Run after implementing PLAN-SIGNiX-SYNC-MODEL.md:
  python manage.py test apps.deals.tests.test_sync_model
"""

from decimal import Decimal
from datetime import date, timedelta
import importlib

from django.apps import apps as django_apps
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.deals.models import (
    Deal,
    DealType,
    SignatureTransaction,
    SignatureTransactionEvent,
    SignixConfig,
)
from apps.deals.signix import get_signix_config
from apps.documents.models import DocumentSet
from django.contrib.auth import get_user_model

User = get_user_model()


class SignatureTransactionSyncFieldsTests(TestCase):
    """Plan 1 Batch 1: SignatureTransaction sync fields and Expired status."""

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
        self.assertIsNone(tx.status_last_updated)
        self.assertFalse(tx.audit_trail_file)
        self.assertFalse(tx.certificate_of_completion_file)

    def test_create_with_sync_fields_persists(self):
        """Sync fields persist when explicitly set."""
        updated = timezone.now()
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-SYNC-2",
            status=SignatureTransaction.STATUS_IN_PROGRESS,
            signer_count=2,
            signers_completed_refids=["P01", "P02"],
            signers_completed_count=2,
            status_last_updated=updated,
        )
        tx.refresh_from_db()
        self.assertEqual(tx.signer_count, 2)
        self.assertEqual(tx.signers_completed_refids, ["P01", "P02"])
        self.assertEqual(tx.signers_completed_count, 2)
        self.assertEqual(tx.status_last_updated, updated)

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


class SignatureTransactionDataMigrationTests(TestCase):
    """Plan 1 Batch 1: data migration backfills legacy rows consistently."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="migrationuser",
            email="migration@example.com",
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

    def test_backfill_sets_complete_and_signer_counts(self):
        """Legacy rows are backfilled to Complete with 2/2 signers and submitted_at timestamp."""
        submitted = timezone.now()
        tx = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-LEGACY-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )
        SignatureTransaction.objects.filter(pk=tx.pk).update(
            signer_count=None,
            signers_completed_count=0,
            signers_completed_refids=[],
            completed_at=None,
            status_last_updated=None,
            submitted_at=submitted,
            status=SignatureTransaction.STATUS_SUBMITTED,
        )

        migration = importlib.import_module(
            "apps.deals.migrations.0006_add_signature_transaction_sync_fields"
        )
        migration.backfill_signature_transaction_sync_fields(django_apps, None)

        tx.refresh_from_db()
        self.assertEqual(tx.status, SignatureTransaction.STATUS_COMPLETE)
        self.assertEqual(tx.signer_count, 2)
        self.assertEqual(tx.signers_completed_count, 2)
        self.assertEqual(tx.signers_completed_refids, [])
        self.assertEqual(tx.completed_at, submitted)
        self.assertEqual(tx.status_last_updated, submitted)


class SignixConfigPushBaseUrlTests(TestCase):
    """Plan 1 Batch 2: SignixConfig.push_base_url."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="signixstaff",
            email="staff@example.com",
            password="test",
            is_staff=True,
        )

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

    def test_signix_config_page_loads(self):
        """Existing SIGNiX config page still renders after the field is added."""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("signix_config"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SIGNiX Configuration")


class SignatureTransactionEventTests(TestCase):
    """Plan 1 Batch 3: SignatureTransactionEvent model and ordering."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="eventuser",
            email="event@example.com",
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
        self.transaction = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.doc_set,
            signix_document_set_id="DS-EVENT-1",
            status=SignatureTransaction.STATUS_SUBMITTED,
        )

    def test_create_event_and_related_name(self):
        """Transaction.events exposes created events via related_name."""
        occurred = timezone.now()
        SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="submitted",
            occurred_at=occurred,
        )
        self.assertEqual(self.transaction.events.count(), 1)
        self.assertEqual(self.transaction.events.first().event_type, "submitted")

    def test_events_ordered_by_occurred_at(self):
        """Meta ordering is ascending by occurred_at."""
        earlier = timezone.now()
        later = earlier + timedelta(minutes=5)
        SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="party_complete",
            occurred_at=later,
        )
        SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="send",
            occurred_at=earlier,
        )
        self.assertEqual(
            list(self.transaction.events.values_list("event_type", flat=True)),
            ["send", "party_complete"],
        )

    def test_event_type_submitted(self):
        """submitted is a valid persisted event_type for the initial event."""
        event = SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="submitted",
            occurred_at=timezone.now(),
        )
        self.assertEqual(event.event_type, "submitted")
        self.assertEqual(event.signature_transaction_id, self.transaction.pk)

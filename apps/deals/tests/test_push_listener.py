"""
Tests for Plan 2 (Dashboard/Sync): SIGNiX push listener helpers and view.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.deals.models import (
    Deal,
    DealType,
    SignatureTransaction,
)
from apps.deals.signix import (
    apply_push_action,
    download_signed_documents_on_complete,
    get_event_time_for_push,
    get_signature_transaction_for_push,
    push_action_to_event_type,
)
from apps.documents.models import DocumentSet

User = get_user_model()


class PushListenerBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pushuser",
            email="push@example.com",
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
        self.doc_set = DocumentSet.objects.create(
            deal=self.deal,
            document_set_template=None,
        )

    def make_transaction(self, **kwargs):
        defaults = {
            "deal": self.deal,
            "document_set": self.doc_set,
            "signix_document_set_id": "DS-PUSH-BASE",
            "transaction_id": "ext-base",
            "status": SignatureTransaction.STATUS_SUBMITTED,
        }
        defaults.update(kwargs)
        return SignatureTransaction.objects.create(**defaults)


class GetSignatureTransactionForPushTests(PushListenerBase):
    def test_lookup_by_signix_document_set_id(self):
        tx = self.make_transaction(signix_document_set_id="DS-A", transaction_id="ext-1")
        result = get_signature_transaction_for_push(signix_document_set_id="DS-A")
        self.assertEqual(result, tx)

    def test_lookup_by_transaction_id(self):
        tx = self.make_transaction(signix_document_set_id="DS-A", transaction_id="ext-1")
        result = get_signature_transaction_for_push(transaction_id="ext-1")
        self.assertEqual(result, tx)

    def test_lookup_returns_none_when_not_found(self):
        self.assertIsNone(
            get_signature_transaction_for_push(
                signix_document_set_id="missing",
                transaction_id="none",
            )
        )

    def test_lookup_returns_none_when_both_empty(self):
        self.assertIsNone(get_signature_transaction_for_push(None, None))
        self.assertIsNone(get_signature_transaction_for_push("", ""))


class ApplyPushActionTests(PushListenerBase):
    def test_complete_sets_status_and_completed_at(self):
        tx = self.make_transaction()
        apply_push_action(tx, "complete")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_COMPLETE)
        self.assertIsNotNone(tx.completed_at)
        self.assertIsNotNone(tx.status_last_updated)

    def test_complete_sets_signers_completed_count_to_signer_count(self):
        tx = self.make_transaction(signer_count=2, signers_completed_count=0)
        apply_push_action(tx, "complete")
        self.assertEqual(tx.signers_completed_count, 2)

    def test_party_complete_appends_refid_and_sets_in_progress(self):
        tx = self.make_transaction(
            signers_completed_refids=[],
            signers_completed_count=0,
        )
        apply_push_action(tx, "partyComplete", refid="P01")
        self.assertIn("P01", tx.signers_completed_refids)
        self.assertEqual(tx.signers_completed_count, 1)
        self.assertEqual(tx.status, SignatureTransaction.STATUS_IN_PROGRESS)
        self.assertIsNotNone(tx.status_last_updated)

    def test_party_complete_idempotent(self):
        tx = self.make_transaction(
            signers_completed_refids=["P01"],
            signers_completed_count=1,
        )
        apply_push_action(tx, "partyComplete", refid="P01")
        self.assertEqual(tx.signers_completed_refids, ["P01"])
        self.assertEqual(tx.signers_completed_count, 1)

    def test_terminal_not_overwritten(self):
        tx = self.make_transaction(status=SignatureTransaction.STATUS_COMPLETE)
        apply_push_action(tx, "partyComplete", refid="P02")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_COMPLETE)

    def test_expire_sets_expired_status(self):
        tx = self.make_transaction()
        apply_push_action(tx, "expire")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_EXPIRED)
        self.assertIsNotNone(tx.status_last_updated)

    def test_suspend_sets_suspended(self):
        tx = self.make_transaction()
        apply_push_action(tx, "suspend")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_SUSPENDED)
        self.assertIsNotNone(tx.status_last_updated)

    def test_cancel_sets_cancelled(self):
        tx = self.make_transaction()
        apply_push_action(tx, "cancel")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_CANCELLED)
        self.assertIsNotNone(tx.status_last_updated)


class PushActionHelperTests(TestCase):
    def test_push_action_to_event_type_send(self):
        self.assertEqual(push_action_to_event_type("Send"), "send")

    def test_push_action_to_event_type_party_complete(self):
        self.assertEqual(push_action_to_event_type("partyComplete"), "party_complete")

    def test_push_action_to_event_type_complete(self):
        self.assertEqual(push_action_to_event_type("complete"), "complete")

    def test_push_action_to_event_type_suspend_cancel_expire(self):
        self.assertEqual(push_action_to_event_type("suspend"), "suspend")
        self.assertEqual(push_action_to_event_type("cancel"), "cancel")
        self.assertEqual(push_action_to_event_type("expire"), "expire")

    def test_get_event_time_for_push_valid_ts(self):
        dt = get_event_time_for_push("2025-03-15T14:30:00")
        self.assertEqual(dt.year, 2025)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 30)
        self.assertEqual(dt.second, 0)

    def test_get_event_time_for_push_invalid_ts(self):
        dt = get_event_time_for_push("not-a-date")
        self.assertIsNotNone(dt)

    def test_get_event_time_for_push_none(self):
        dt = get_event_time_for_push(None)
        self.assertIsNotNone(dt)


class PushViewTests(PushListenerBase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_push_view_returns_200_and_ok_body(self):
        response = self.client.get("/signix/push/?action=complete&id=unknown&extid=unknown")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    @patch("apps.deals.views.threading.Thread")
    def test_push_view_updates_transaction_and_returns_200(self, mock_thread):
        tx = self.make_transaction(signix_document_set_id="DS-V1", transaction_id="ext-v1")
        response = self.client.get(
            "/signix/push/?action=complete&id=DS-V1&extid=ext-v1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        tx.refresh_from_db()
        self.assertEqual(tx.status, SignatureTransaction.STATUS_COMPLETE)
        self.assertIsNotNone(tx.completed_at)
        self.assertIsNotNone(tx.status_last_updated)
        self.assertTrue(tx.events.filter(event_type="complete").exists())
        mock_thread.assert_called_once_with(
            target=download_signed_documents_on_complete,
            args=(tx,),
            daemon=True,
        )
        mock_thread.return_value.start.assert_called_once()

    def test_push_view_creates_party_complete_event_with_refid(self):
        tx = self.make_transaction(signix_document_set_id="DS-V2", transaction_id="ext-v2")
        response = self.client.get(
            "/signix/push/?action=partyComplete&id=DS-V2&extid=ext-v2&refid=P01"
        )
        self.assertEqual(response.status_code, 200)
        tx.refresh_from_db()
        self.assertTrue(tx.events.filter(event_type="party_complete", refid="P01").exists())

    def test_push_view_unknown_id_logs_and_returns_200(self):
        with self.assertLogs("apps.deals.views", level="WARNING") as captured:
            response = self.client.get(
                "/signix/push/?action=complete&id=unknown&extid=unknown"
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("transaction not found" in msg for msg in captured.output))

    def test_push_view_csrf_exempt(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get("/signix/push/?action=complete&id=unknown&extid=unknown")
        self.assertEqual(response.status_code, 200)

    def test_push_view_expire_updates_transaction(self):
        tx = self.make_transaction(signix_document_set_id="DS-V4", transaction_id="ext-v4")
        response = self.client.get(
            "/signix/push/?action=expire&id=DS-V4&extid=ext-v4"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        tx.refresh_from_db()
        self.assertEqual(tx.status, SignatureTransaction.STATUS_EXPIRED)
        self.assertIsNotNone(tx.status_last_updated)
        self.assertTrue(tx.events.filter(event_type="expire").exists())

    @patch("apps.deals.views.threading.Thread")
    def test_push_view_complete_idempotent(self, mock_thread):
        tx = self.make_transaction(signix_document_set_id="DS-V3", transaction_id="ext-v3")
        response1 = self.client.get(
            "/signix/push/?action=complete&id=DS-V3&extid=ext-v3"
        )
        response2 = self.client.get(
            "/signix/push/?action=complete&id=DS-V3&extid=ext-v3"
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.content, b"OK")
        self.assertEqual(response2.content, b"OK")
        tx.refresh_from_db()
        self.assertEqual(tx.status, SignatureTransaction.STATUS_COMPLETE)
        self.assertIsNotNone(tx.completed_at)
        self.assertIsNotNone(tx.status_last_updated)

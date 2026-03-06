"""
Tests for Plan 6 Batch 1: signature transaction detail page and links.
"""

import tempfile
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealType, SignatureTransaction, SignatureTransactionEvent
from apps.deals.signix import (
    VERSION_STATUS_SUBMITTED_TO_SIGNIX,
    get_event_type_display,
    get_signers_detail_for_transaction,
)
from apps.doctemplates.models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
)
from apps.documents.models import DocumentInstance, DocumentInstanceVersion, DocumentSet
from apps.users.models import LeaseOfficerProfile

User = get_user_model()


def _make_pdf(name="doc.pdf", content=b"%PDF-1.4 minimal"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class SignatureTransactionDetailBase(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        override = self.settings(MEDIA_ROOT=self.tempdir.name)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(self.tempdir.cleanup)

        self.client = Client()
        self.user = User.objects.create_user(
            username="detailuser",
            email="detailuser@example.com",
            password="test",
            first_name="Detail",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Detail",
            last_name="Officer",
            email="detailuser@example.com",
            phone_number="555-7777",
        )
        self.contact = Contact.objects.create(
            first_name="Alice",
            middle_name="",
            last_name="Signer",
            email="alice@example.com",
            phone_number="555-1111",
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
        self.deal.contacts.add(self.contact)

        self.doc_set_template = DocumentSetTemplate.objects.create(
            deal_type=self.deal_type,
            name="Detail Template",
        )
        self.static_tpl_1 = StaticDocumentTemplate.objects.create(
            ref_id="DetailDocOne",
            description="Detail document one",
            file=_make_pdf("detail-one.pdf"),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.static_tpl_2 = StaticDocumentTemplate.objects.create(
            ref_id="DetailDocTwo",
            description="Detail document two",
            file=_make_pdf("detail-two.pdf"),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=self.doc_set_template,
            order=1,
            content_type=ct,
            object_id=self.static_tpl_1.pk,
        )
        DocumentSetTemplateItem.objects.create(
            document_set_template=self.doc_set_template,
            order=2,
            content_type=ct,
            object_id=self.static_tpl_2.pk,
        )

        self.document_set = DocumentSet.objects.create(
            deal=self.deal,
            document_set_template=self.doc_set_template,
        )
        self.instance_1 = DocumentInstance.objects.create(
            document_set=self.document_set,
            order=1,
            content_type=ct,
            object_id=self.static_tpl_1.pk,
            template_type="static",
        )
        self.instance_2 = DocumentInstance.objects.create(
            document_set=self.document_set,
            order=2,
            content_type=ct,
            object_id=self.static_tpl_2.pk,
            template_type="static",
        )
        self.as_sent_version_1 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance_1,
            version_number=1,
            status=VERSION_STATUS_SUBMITTED_TO_SIGNIX,
            file=_make_pdf("submitted-one.pdf"),
        )
        self.final_version_1 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance_1,
            version_number=2,
            status="Final",
            file=_make_pdf("final-one.pdf"),
        )
        self.as_sent_version_2 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance_2,
            version_number=1,
            status=VERSION_STATUS_SUBMITTED_TO_SIGNIX,
            file=_make_pdf("submitted-two.pdf"),
        )

        self.transaction = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.document_set,
            signix_document_set_id="DS-DETAIL-1",
            transaction_id="TX-DETAIL-1",
            status=SignatureTransaction.STATUS_COMPLETE,
            signer_count=2,
            signers_completed_refids=["detailuser@example.com", "alice@example.com"],
            signers_completed_count=2,
            status_last_updated=timezone.make_aware(datetime(2025, 3, 15, 14, 45)),
        )
        SignatureTransaction.objects.filter(pk=self.transaction.pk).update(
            submitted_at=timezone.make_aware(datetime(2025, 3, 15, 14, 30))
        )
        self.transaction.refresh_from_db()

        SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="submitted",
            occurred_at=self.transaction.submitted_at,
        )
        self.party_complete_one = SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="party_complete",
            occurred_at=timezone.make_aware(datetime(2025, 3, 15, 14, 35)),
            refid="detailuser@example.com",
        )
        self.party_complete_two = SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="party_complete",
            occurred_at=timezone.make_aware(datetime(2025, 3, 15, 14, 40)),
            refid="alice@example.com",
        )
        SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="complete",
            occurred_at=timezone.make_aware(datetime(2025, 3, 15, 14, 45)),
        )

    def _set_audit_trail_file(self):
        self.transaction.audit_trail_file.save(
            "audit-trail.pdf",
            _make_pdf("audit-trail.pdf", b"%PDF-1.4 audit trail"),
            save=True,
        )
        self.transaction.refresh_from_db()

    def _set_certificate_file(self):
        self.transaction.certificate_of_completion_file.save(
            "certificate.pdf",
            _make_pdf("certificate.pdf", b"%PDF-1.4 certificate"),
            save=True,
        )
        self.transaction.refresh_from_db()


class SignatureTransactionDetailHelperTests(SignatureTransactionDetailBase):
    def test_get_event_type_display_returns_human_labels(self):
        self.assertEqual(get_event_type_display("submitted"), "Transaction submitted")
        self.assertEqual(get_event_type_display("party_complete"), "Signer completed")
        self.assertEqual(get_event_type_display("complete"), "Transaction completed")

    def test_get_signers_detail_matches_party_complete_events(self):
        signers = get_signers_detail_for_transaction(self.transaction)

        self.assertEqual(len(signers), 2)
        self.assertEqual(signers[0]["name"], "Detail Officer")
        self.assertEqual(signers[0]["email"], "detailuser@example.com")
        self.assertEqual(signers[0]["authentication"], "SelectOneClick")
        self.assertTrue(signers[0]["signed"])
        self.assertEqual(signers[0]["signed_at"], self.party_complete_one.occurred_at)

        self.assertEqual(signers[1]["name"], "Alice Signer")
        self.assertEqual(signers[1]["email"], "alice@example.com")
        self.assertEqual(signers[1]["authentication"], "SMSOneClick")
        self.assertTrue(signers[1]["signed"])
        self.assertEqual(signers[1]["signed_at"], self.party_complete_two.occurred_at)

    def test_get_signers_detail_falls_back_to_event_order_when_ids_do_not_match(self):
        self.transaction.events.filter(event_type="party_complete").delete()
        first_event = SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="party_complete",
            occurred_at=timezone.make_aware(datetime(2025, 3, 15, 14, 35)),
            refid="opaque-one",
        )
        second_event = SignatureTransactionEvent.objects.create(
            signature_transaction=self.transaction,
            event_type="party_complete",
            occurred_at=timezone.make_aware(datetime(2025, 3, 15, 14, 40)),
            refid="opaque-two",
        )

        signers = get_signers_detail_for_transaction(self.transaction)

        self.assertEqual(signers[0]["signed_at"], first_event.occurred_at)
        self.assertEqual(signers[1]["signed_at"], second_event.occurred_at)


class SignatureTransactionDetailViewTests(SignatureTransactionDetailBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_signature_transaction_detail_returns_200_for_valid_pk(self):
        response = self.client.get(
            reverse("deals:signature_transaction_detail", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "deals/signature_transaction_detail.html")
        self.assertContains(response, "TX-DETAIL-1")
        self.assertContains(response, "DS-DETAIL-1")
        self.assertContains(response, "Detail Template")
        self.assertContains(response, "Complete")
        self.assertContains(response, "Mar 15, 2025 2:45 PM")
        self.assertContains(response, "Signers")
        self.assertContains(response, "Documents")
        self.assertContains(response, "Events")
        self.assertContains(response, "Artifacts")
        self.assertContains(response, "Not available")
        self.assertContains(
            response,
            reverse("deals:deal_detail", kwargs={"pk": self.deal.pk}),
        )
        self.assertContains(
            response,
            reverse("documents:document_version_view", args=[self.as_sent_version_1.pk]),
        )
        self.assertContains(
            response,
            reverse("documents:document_version_view", args=[self.final_version_1.pk]),
        )
        self.assertContains(response, "Pending")

        signers = response.context["signers"]
        self.assertEqual(len(signers), 2)
        self.assertTrue(signers[0]["signed"])
        self.assertEqual(signers[0]["signed_at"], self.party_complete_one.occurred_at)

        documents = response.context["documents"]
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0]["as_sent_version"].pk, self.as_sent_version_1.pk)
        self.assertEqual(documents[0]["signed_version"].pk, self.final_version_1.pk)
        self.assertEqual(documents[1]["as_sent_version"].pk, self.as_sent_version_2.pk)
        self.assertIsNone(documents[1]["signed_version"])

        event_labels = [item["label"] for item in response.context["events"]]
        self.assertEqual(
            event_labels,
            [
                "Transaction submitted",
                "Signer completed",
                "Signer completed",
                "Transaction completed",
            ],
        )

    def test_signature_transaction_detail_returns_404_for_invalid_pk(self):
        response = self.client.get(reverse("deals:signature_transaction_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_list_and_deal_view_contain_link_to_detail(self):
        detail_url = reverse("deals:signature_transaction_detail", args=[self.transaction.pk])

        list_response = self.client.get(reverse("deals:signature_transaction_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "View")
        self.assertContains(list_response, detail_url)

        deal_response = self.client.get(
            reverse("deals:deal_detail", kwargs={"pk": self.deal.pk})
        )
        self.assertEqual(deal_response.status_code, 200)
        self.assertContains(deal_response, "View")
        self.assertContains(deal_response, detail_url)

    def test_signature_transaction_detail_shows_artifact_links_when_files_exist(self):
        self._set_audit_trail_file()
        self._set_certificate_file()

        response = self.client.get(
            reverse("deals:signature_transaction_detail", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("deals:signature_transaction_audit_trail", args=[self.transaction.pk]),
        )
        self.assertContains(response, "View audit trail")
        self.assertContains(
            response,
            reverse("deals:signature_transaction_certificate", args=[self.transaction.pk]),
        )
        self.assertContains(response, "View certificate")


class SignatureTransactionArtifactViewTests(SignatureTransactionDetailBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_signature_transaction_audit_trail_returns_404_when_file_empty(self):
        response = self.client.get(
            reverse("deals:signature_transaction_audit_trail", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_signature_transaction_audit_trail_returns_pdf_when_file_set(self):
        self._set_audit_trail_file()

        response = self.client.get(
            reverse("deals:signature_transaction_audit_trail", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline;", response["Content-Disposition"])
        self.assertIn("audit-trail.pdf", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 audit trail")

    def test_signature_transaction_certificate_returns_404_when_file_empty(self):
        response = self.client.get(
            reverse("deals:signature_transaction_certificate", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_signature_transaction_certificate_returns_pdf_when_file_set(self):
        self._set_certificate_file()

        response = self.client.get(
            reverse("deals:signature_transaction_certificate", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline;", response["Content-Disposition"])
        self.assertIn("certificate.pdf", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 certificate")

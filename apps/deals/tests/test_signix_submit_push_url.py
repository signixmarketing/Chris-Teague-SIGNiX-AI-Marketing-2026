"""
Tests for Plan 3 (Dashboard/Sync): SubmitDocument push URL and signer_count.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import ANY, patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealType, SignatureTransaction
from apps.deals.signix import (
    SendSubmitDocumentResult,
    VERSION_STATUS_SUBMITTED_TO_SIGNIX,
    build_submit_document_body,
    get_push_base_url,
    get_signix_config,
    submit_document_set_for_signature,
)
from apps.doctemplates.models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
)
from apps.documents.models import DocumentInstance, DocumentInstanceVersion, DocumentSet
from apps.users.models import LeaseOfficerProfile

User = get_user_model()


def _make_pdf():
    return SimpleUploadedFile("doc.pdf", b"%PDF-1.4 minimal", content_type="application/pdf")


class SubmitPushUrlBase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = User.objects.create_user(
            username="pushurluser",
            email="pushurl@example.com",
            password="test",
            first_name="Push",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Push",
            last_name="Officer",
            email="pushurl@example.com",
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
        self.static_tpl = StaticDocumentTemplate.objects.create(
            ref_id="PushUrlTest",
            description="Push URL test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Push URL Template"},
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
        self.version = DocumentInstanceVersion.objects.create(
            document_instance=self.instance,
            version_number=1,
            status="Draft",
            file=_make_pdf(),
        )
        self.config = get_signix_config()
        self.config.submitter_email = "submitter@example.com"
        self.config.push_base_url = ""
        self.config.save()


class GetPushBaseUrlTests(SubmitPushUrlBase):
    def test_get_push_base_url_uses_config_when_set(self):
        self.config.push_base_url = "https://config.example.com"
        self.config.save(update_fields=["push_base_url"])
        self.assertEqual(get_push_base_url(None), "https://config.example.com")

    def test_get_push_base_url_uses_request_when_config_blank(self):
        request = self.factory.get("/", secure=True)
        self.assertEqual(get_push_base_url(request), "https://testserver")

    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        ALLOWED_HOSTS=["proxy.example.com", "testserver", "localhost", "127.0.0.1"],
    )
    def test_get_push_base_url_uses_forwarded_https_scheme(self):
        request = self.factory.get(
            "/",
            secure=False,
            HTTP_HOST="proxy.example.com",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(get_push_base_url(request), "https://proxy.example.com")

    @override_settings(SIGNIX_PUSH_BASE_URL="", NGROK_DOMAIN="")
    def test_get_push_base_url_returns_empty_when_nothing_set(self):
        self.config.push_base_url = ""
        self.config.save(update_fields=["push_base_url"])
        self.assertEqual(get_push_base_url(None), "")

    def test_get_push_base_url_strips_trailing_slash(self):
        self.config.push_base_url = "https://config.example.com/"
        self.config.save(update_fields=["push_base_url"])
        self.assertEqual(get_push_base_url(None), "https://config.example.com")

    @override_settings(SIGNIX_PUSH_BASE_URL="", NGROK_DOMAIN="my-app.ngrok-free.dev")
    def test_get_push_base_url_uses_ngrok_setting_with_https(self):
        self.config.push_base_url = ""
        self.config.save(update_fields=["push_base_url"])
        self.assertEqual(get_push_base_url(None), "https://my-app.ngrok-free.dev")


class BuildSubmitDocumentBodyPushUrlTests(SubmitPushUrlBase):
    def test_build_body_includes_client_preferences_when_push_base_url_set(self):
        body, _ = build_submit_document_body(
            self.deal,
            self.document_set,
            push_base_url="https://push.example.com",
        )
        self.assertIn("UseClientNotifyVersion2", body)
        self.assertIn("TransactionClientNotifyURL", body)
        self.assertIn("https://push.example.com/signix/push", body)

    def test_build_body_omits_client_preferences_when_push_base_url_empty(self):
        body, _ = build_submit_document_body(
            self.deal,
            self.document_set,
            push_base_url="",
        )
        self.assertNotIn("UseClientNotifyVersion2", body)
        self.assertNotIn("TransactionClientNotifyURL", body)

    def test_build_body_uses_get_push_base_url_when_push_base_url_none(self):
        self.config.push_base_url = "https://fallback.example.com"
        self.config.save(update_fields=["push_base_url"])
        body, _ = build_submit_document_body(
            self.deal,
            self.document_set,
            push_base_url=None,
        )
        self.assertIn("https://fallback.example.com/signix/push", body)


class SubmitDocumentSetForSignaturePushUrlTests(SubmitPushUrlBase):
    @patch("apps.deals.signix.send_submit_document")
    def test_submit_sets_signer_count_and_submitted_event(self, mock_send_submit_document):
        mock_send_submit_document.return_value = SendSubmitDocumentResult(
            document_set_id="DS-PUSH-1",
            first_signing_url="https://sign.example.com/first",
        )
        request = self.factory.get("/", secure=True)

        transaction, first_url = submit_document_set_for_signature(
            self.deal,
            self.document_set,
            request=request,
        )

        self.assertEqual(first_url, "https://sign.example.com/first")
        self.assertEqual(transaction.signer_count, 2)
        submitted_event = transaction.events.get(event_type="submitted")
        self.assertEqual(submitted_event.occurred_at, transaction.submitted_at)
        sent_body = mock_send_submit_document.call_args.args[0]
        self.assertIn("https://testserver/signix/push", sent_body)

    @patch("apps.deals.signix.send_submit_document")
    def test_submit_marks_document_versions_submitted_to_signix(self, mock_send_submit_document):
        mock_send_submit_document.return_value = SendSubmitDocumentResult(
            document_set_id="DS-PUSH-2",
            first_signing_url="https://sign.example.com/first",
        )

        submit_document_set_for_signature(self.deal, self.document_set)

        self.version.refresh_from_db()
        self.assertEqual(self.version.status, VERSION_STATUS_SUBMITTED_TO_SIGNIX)

    @patch("apps.deals.signix.send_submit_document")
    def test_submit_uses_request_derived_push_url_in_body(self, mock_send_submit_document):
        mock_send_submit_document.return_value = SendSubmitDocumentResult(
            document_set_id="DS-PUSH-3",
            first_signing_url="https://sign.example.com/first",
        )
        request = self.factory.get("/", secure=False, HTTP_HOST="testserver")

        submit_document_set_for_signature(self.deal, self.document_set, request=request)

        sent_body = mock_send_submit_document.call_args.args[0]
        self.assertIn("http://testserver/signix/push", sent_body)
        mock_send_submit_document.assert_called_once_with(ANY, ANY, ANY)


class SignixConfigViewPushUrlTests(SubmitPushUrlBase):
    def setUp(self):
        super().setUp()
        self.staff_user = User.objects.create_user(
            username="pushurlstaff",
            email="pushurlstaff@example.com",
            password="test",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)
        self.config.sponsor = "sponsor"
        self.config.client = "client"
        self.config.user_id = "user-id"
        self.config.password = "secret"
        self.config.workgroup = "workgroup"
        self.config.save()

    def test_config_view_renders_with_derived_push_url(self):
        response = self.client.get(reverse("signix_config"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Push base URL")
        self.assertContains(response, "When blank, app will use:")
        self.assertContains(response, "http://testserver/signix/push")

    def test_config_view_saves_push_base_url_override(self):
        response = self.client.post(
            reverse("signix_config"),
            {
                "sponsor": "sponsor",
                "client": "client",
                "user_id": "user-id",
                "password": "",
                "workgroup": "workgroup",
                "push_base_url": "https://override.example.com",
                "demo_only": "on",
                "delete_documents_after_days": 60,
                "default_email_content": self.config.default_email_content,
                "submitter_first_name": "",
                "submitter_middle_name": "",
                "submitter_last_name": "",
                "submitter_email": "submitter@example.com",
                "submitter_phone": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.config.refresh_from_db()
        self.assertEqual(self.config.push_base_url, "https://override.example.com")
        self.assertEqual(get_push_base_url(None), "https://override.example.com")
        self.assertContains(response, "SIGNiX configuration saved.")

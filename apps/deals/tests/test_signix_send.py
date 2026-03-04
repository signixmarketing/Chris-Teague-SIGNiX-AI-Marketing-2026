"""
Tests for Plan 6 Batch 1: send_submit_document and response parsing (mocked HTTP).
Plan 6 Batch 2: submit_document_set_for_signature integration tests.
"""

from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date

import requests
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.deals.models import SignixConfig, SignatureTransaction, Deal, DealType
from apps.deals.signix import (
    SignixApiError,
    SignixValidationError,
    SendSubmitDocumentResult,
    send_submit_document,
    get_signix_submit_endpoint,
    get_signix_config,
    submit_document_set_for_signature,
    VERSION_STATUS_SUBMITTED_TO_SIGNIX,
    SIGNIX_ENDPOINT_WEBTEST,
    SIGNIX_ENDPOINT_PRODUCTION,
)
from apps.contacts.models import Contact
from apps.users.models import LeaseOfficerProfile
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


def _success_response_xml(document_set_id="DOC-123", first_signing_url=None):
    url_frag = f"<SignerAccessLink>{first_signing_url}</SignerAccessLink>" if first_signing_url else ""
    return f"""<?xml version="1.0"?>
<SubmitDocumentRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status>
        <StatusCode>0</StatusCode>
        <StatusDesc>Success</StatusDesc>
    </Status>
    <DocumentSetID>{document_set_id}</DocumentSetID>
    {url_frag}
</SubmitDocumentRs>"""


def _error_response_xml(code=1, desc="Invalid request"):
    return f"""<?xml version="1.0"?>
<SubmitDocumentRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status>
        <StatusCode>{code}</StatusCode>
        <StatusDesc>{desc}</StatusDesc>
    </Status>
</SubmitDocumentRs>"""


class GetSignixSubmitEndpointTests(TestCase):
    """Plan 6 Batch 1: endpoint URL from config.demo_only."""

    def test_demo_only_true_returns_webtest(self):
        config = SignixConfig(demo_only=True)
        self.assertEqual(get_signix_submit_endpoint(config), SIGNIX_ENDPOINT_WEBTEST)

    def test_demo_only_false_returns_production(self):
        config = SignixConfig(demo_only=False)
        self.assertEqual(get_signix_submit_endpoint(config), SIGNIX_ENDPOINT_PRODUCTION)

    def test_config_without_demo_only_defaults_to_webtest(self):
        class NoDemoConfig:
            pass
        config = NoDemoConfig()
        self.assertEqual(get_signix_submit_endpoint(config), SIGNIX_ENDPOINT_WEBTEST)


class SendSubmitDocumentTests(TestCase):
    """Plan 6 Batch 1: send_submit_document with mocked requests."""

    def setUp(self):
        self.config = SignixConfig(demo_only=True)
        self.endpoint = SIGNIX_ENDPOINT_WEBTEST
        self.body = "<SubmitDocumentRq xmlns='urn:com:signix:schema:sdddc-1-1'><Data/></SubmitDocumentRq>"

    @patch("apps.deals.signix.requests.post")
    def test_success_returns_result_with_document_set_id(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = _success_response_xml(document_set_id="DS-456")
        result = send_submit_document(self.body, self.endpoint, self.config)
        self.assertIsInstance(result, SendSubmitDocumentResult)
        self.assertEqual(result.document_set_id, "DS-456")
        self.assertIsNone(result.first_signing_url)
        mock_post.assert_called_once()
        call_kw = mock_post.call_args[1]
        self.assertEqual(call_kw["data"]["method"], "SubmitDocument")
        self.assertEqual(call_kw["data"]["request"], self.body)

    @patch("apps.deals.signix.requests.post")
    def test_success_with_first_signing_url_in_response(self, mock_post):
        mock_post.return_value.status_code = 200
        url = "https://webtest.signix.biz/sign/abc123"
        mock_post.return_value.text = _success_response_xml(
            document_set_id="DS-789", first_signing_url=url
        )
        result = send_submit_document(self.body, self.endpoint, self.config)
        self.assertEqual(result.document_set_id, "DS-789")
        self.assertEqual(result.first_signing_url, url)

    @patch("apps.deals.signix.requests.post")
    def test_http_500_raises_signix_api_error(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"
        with self.assertRaises(SignixApiError) as ctx:
            send_submit_document(self.body, self.endpoint, self.config)
        self.assertIn("500", ctx.exception.message)
        self.assertEqual(ctx.exception.http_status, 500)
        self.assertIsNotNone(ctx.exception.response_text)

    @patch("apps.deals.signix.requests.post")
    def test_status_code_non_zero_raises_signix_api_error(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = _error_response_xml(code=1, desc="Invalid CustInfo")
        with self.assertRaises(SignixApiError) as ctx:
            send_submit_document(self.body, self.endpoint, self.config)
        self.assertIn("Invalid CustInfo", ctx.exception.message)
        self.assertEqual(ctx.exception.http_status, 200)

    @patch("apps.deals.signix.requests.post")
    def test_missing_document_set_id_raises_signix_api_error(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = """<?xml version="1.0"?>
<SubmitDocumentRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status><StatusCode>0</StatusCode><StatusDesc>OK</StatusDesc></Status>
</SubmitDocumentRs>"""
        with self.assertRaises(SignixApiError) as ctx:
            send_submit_document(self.body, self.endpoint, self.config)
        self.assertIn("DocumentSetID", ctx.exception.message)

    @patch("apps.deals.signix.requests.post")
    def test_request_exception_raises_signix_api_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertRaises(SignixApiError) as ctx:
            send_submit_document(self.body, self.endpoint, self.config)
        self.assertIn("SIGNiX request failed", ctx.exception.message)
        self.assertIsNone(ctx.exception.http_status)


def _get_access_link_response_xml(signer_url):
    """GetAccessLinkSigner success response with signer URL."""
    return f"""<?xml version="1.0"?>
<GetAccessLinkSignerRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status><StatusCode>0</StatusCode><StatusDesc>OK</StatusDesc></Status>
    <SignerAccessLink>{signer_url}</SignerAccessLink>
</GetAccessLinkSignerRs>"""


class SubmitDocumentSetForSignatureTests(TestCase):
    """Plan 6 Batch 2: submit_document_set_for_signature with mocked HTTP."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="orchuser",
            email="orch@example.com",
            password="test",
            first_name="Orch",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Orch",
            last_name="Officer",
            email="orch@example.com",
            phone_number="555-0000",
        )
        self.contact = Contact.objects.create(
            first_name="Bob",
            middle_name="",
            last_name="Signer",
            email="bob@example.com",
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
            ref_id="OrchTest",
            description="Orch test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Orch Test Template"},
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
        config = get_signix_config()
        config.submitter_email = "orch@example.com"
        config.save()

    @patch("apps.deals.signix.requests.post")
    def test_success_creates_transaction_and_updates_versions(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = _success_response_xml(
            document_set_id="DS-ORCH-1",
            first_signing_url="https://webtest.signix.biz/sign/xyz",
        )
        tx, first_url = submit_document_set_for_signature(self.deal, self.document_set)
        self.assertIsNotNone(tx.pk)
        self.assertEqual(tx.deal_id, self.deal.pk)
        self.assertEqual(tx.document_set_id, self.document_set.pk)
        self.assertEqual(tx.signix_document_set_id, "DS-ORCH-1")
        self.assertEqual(tx.status, SignatureTransaction.STATUS_SUBMITTED)
        self.assertEqual(tx.first_signing_url, "https://webtest.signix.biz/sign/xyz")
        self.assertEqual(first_url, "https://webtest.signix.biz/sign/xyz")
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, VERSION_STATUS_SUBMITTED_TO_SIGNIX)

    @patch("apps.deals.signix.requests.post")
    def test_success_calls_get_access_link_when_no_url_in_submit_response(self, mock_post):
        submit_resp = MagicMock()
        submit_resp.status_code = 200
        submit_resp.text = _success_response_xml(document_set_id="DS-ORCH-2", first_signing_url=None)
        gal_resp = MagicMock()
        gal_resp.status_code = 200
        gal_resp.text = _get_access_link_response_xml("https://webtest.signix.biz/sign/getlink")
        mock_post.side_effect = [submit_resp, gal_resp]
        tx, first_url = submit_document_set_for_signature(self.deal, self.document_set)
        self.assertEqual(tx.signix_document_set_id, "DS-ORCH-2")
        self.assertEqual(tx.first_signing_url, "https://webtest.signix.biz/sign/getlink")
        self.assertEqual(first_url, "https://webtest.signix.biz/sign/getlink")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_post.call_args_list[0][1]["data"]["method"], "SubmitDocument")
        self.assertEqual(mock_post.call_args_list[1][1]["data"]["method"], "GetAccessLinkSigner")

    @patch("apps.deals.signix.requests.post")
    def test_submit_failure_creates_no_transaction_no_version_update(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Server Error"
        with self.assertRaises(SignixApiError):
            submit_document_set_for_signature(self.deal, self.document_set)
        self.assertEqual(SignatureTransaction.objects.filter(deal=self.deal).count(), 0)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "Draft")

    @patch("apps.deals.signix.requests.post")
    def test_submit_4xx_creates_no_transaction_no_version_update(self, mock_post):
        """Plan 6 Batch 3: SubmitDocument 4xx raises SignixApiError, no transaction, no version update."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        with self.assertRaises(SignixApiError):
            submit_document_set_for_signature(self.deal, self.document_set)
        self.assertEqual(SignatureTransaction.objects.filter(deal=self.deal).count(), 0)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "Draft")

    def test_validation_failure_raises_no_http_call(self):
        other_deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 2),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("350.00"),
        )
        with self.assertRaises(SignixValidationError):
            submit_document_set_for_signature(other_deal, self.document_set)
        self.assertEqual(SignatureTransaction.objects.filter(deal=other_deal).count(), 0)

    @patch("apps.deals.signix.requests.post")
    def test_validation_failure_makes_no_http_call(self, mock_post):
        """Plan 6 Batch 3: wrong deal raises SignixValidationError and requests.post is never called."""
        other_deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 2),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("350.00"),
        )
        with self.assertRaises(SignixValidationError):
            submit_document_set_for_signature(other_deal, self.document_set)
        mock_post.assert_not_called()

    @patch("apps.deals.signix.requests.post")
    def test_get_access_link_failure_after_submit_success_still_creates_transaction(self, mock_post):
        submit_resp = MagicMock()
        submit_resp.status_code = 200
        submit_resp.text = _success_response_xml(document_set_id="DS-ORCH-3", first_signing_url=None)
        gal_resp = MagicMock()
        gal_resp.status_code = 500
        gal_resp.text = "GetAccessLink error"
        mock_post.side_effect = [submit_resp, gal_resp]
        tx, first_url = submit_document_set_for_signature(self.deal, self.document_set)
        self.assertEqual(tx.signix_document_set_id, "DS-ORCH-3")
        self.assertEqual(tx.first_signing_url, "")
        self.assertEqual(first_url, "")
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, VERSION_STATUS_SUBMITTED_TO_SIGNIX)

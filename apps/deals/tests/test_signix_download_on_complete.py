"""
Tests for Plan 5: DownloadDocument helpers and download-on-complete flow.
"""

import tempfile
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealType, SignatureTransaction, SignixConfig
from apps.deals.signix import (
    DownloadDocumentResult,
    DownloadedDocument,
    SIGNIX_ENDPOINT_WEBTEST,
    SignixApiError,
    _build_download_document_request_xml,
    download_document,
    download_signed_documents_on_complete,
    get_signix_config,
    parse_download_document_response,
)
from apps.doctemplates.models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
)
from apps.documents.models import DocumentInstance, DocumentInstanceVersion, DocumentSet
from apps.users.models import LeaseOfficerProfile

User = get_user_model()


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _download_response_xml(include_certificate: bool = True, extra_document: bool = False) -> str:
    certificate_block = ""
    if include_certificate:
        certificate_block = f"""
    <CertificateOfCompletion>
        <MimeType>application/pdf</MimeType>
        <Data>{_b64(b'certificate-pdf')}</Data>
    </CertificateOfCompletion>"""
    extra_doc_block = ""
    if extra_document:
        extra_doc_block = f"""
    <Document>
        <RefID>Form-3</RefID>
        <FileName>signed-3.pdf</FileName>
        <MimeType>application/pdf</MimeType>
        <Data>{_b64(b'signed-doc-3')}</Data>
    </Document>"""
    return f"""<?xml version="1.0"?>
<DownloadDocumentRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status>
        <StatusCode>0</StatusCode>
        <StatusDesc>Success</StatusDesc>
    </Status>
    <Data>
        <DocumentSetID>DS-DOWNLOAD-1</DocumentSetID>
    </Data>
    <Documents>
        <Document>
            <RefID>Form-1</RefID>
            <FileName>signed-1.pdf</FileName>
            <MimeType>application/pdf</MimeType>
            <Data>{_b64(b'signed-doc-1')}</Data>
        </Document>
        <Document>
            <RefID>Form-2</RefID>
            <FileName>signed-2.pdf</FileName>
            <MimeType>application/pdf</MimeType>
            <Data>{_b64(b'signed-doc-2')}</Data>
        </Document>{extra_doc_block}
    </Documents>
    <AuditTrail>
        <MimeType>application/pdf</MimeType>
        <Data>{_b64(b'audit-trail-pdf')}</Data>
    </AuditTrail>{certificate_block}
</DownloadDocumentRs>"""


def _live_style_download_response_xml(include_certificate: bool = True) -> str:
    certificate_block = ""
    if include_certificate:
        certificate_block = f"""
    <CertificateOfCompletion>
        <FileName>certificate.pdf</FileName>
        <MimeType>application/pdf</MimeType>
        <Length>15</Length>
        <Data>{_b64(b'certificate-pdf')}</Data>
    </CertificateOfCompletion>"""
    return f"""<?xml version="1.0"?>
<DownloadDocumentRs xmlns="urn:com:signix:schema:sdddc-1-1">
    <Status>
        <StatusCode>0</StatusCode>
        <StatusDesc>Success</StatusDesc>
    </Status>
    <Data>
        <TransactionID>TX-123</TransactionID>
        <Form>
            <RefID>Form-1</RefID>
            <Desc>Signed One</Desc>
            <FileName>signed-1.pdf</FileName>
            <MimeType>application/pdf</MimeType>
            <Length>12</Length>
            <Data>{_b64(b'signed-doc-1')}</Data>
        </Form>
        <Form>
            <RefID>Form-2</RefID>
            <Desc>Signed Two</Desc>
            <FileName>signed-2.pdf</FileName>
            <MimeType>application/pdf</MimeType>
            <Length>12</Length>
            <Data>{_b64(b'signed-doc-2')}</Data>
        </Form>
    </Data>
    <AuditReport>
        <FileName>audit.pdf</FileName>
        <MimeType>application/pdf</MimeType>
        <Length>15</Length>
        <Data>{_b64(b'audit-trail-pdf')}</Data>
    </AuditReport>{certificate_block}
</DownloadDocumentRs>"""


class BuildDownloadDocumentRequestXmlTests(TestCase):
    def test_build_request_includes_expected_elements(self):
        config = SignixConfig(
            sponsor="sponsor",
            client="client",
            user_id="user",
            password="secret",
            workgroup="wg",
        )
        body = _build_download_document_request_xml("DS-123", config)
        self.assertIn("DownloadDocumentRq", body)
        self.assertIn("<DocumentSetID>DS-123</DocumentSetID>", body)
        self.assertIn("<IncludeAuditData>true</IncludeAuditData>", body)
        self.assertIn("<AuditDataFormat>pdf</AuditDataFormat>", body)
        self.assertIn("<UseConfirmDownload>true</UseConfirmDownload>", body)
        self.assertIn("<IncludeCertificateOfCompletion>true</IncludeCertificateOfCompletion>", body)
        self.assertLess(body.index("<IncludeAuditData>true</IncludeAuditData>"), body.index("<AuditDataFormat>pdf</AuditDataFormat>"))
        self.assertLess(body.index("<AuditDataFormat>pdf</AuditDataFormat>"), body.index("<UseConfirmDownload>true</UseConfirmDownload>"))


class ParseDownloadDocumentResponseTests(TestCase):
    def test_parse_download_document_response_extracts_documents_and_audit_trail(self):
        result = parse_download_document_response(_download_response_xml(include_certificate=True))
        self.assertIsInstance(result, DownloadDocumentResult)
        self.assertEqual(len(result.documents), 2)
        self.assertEqual(result.documents[0].content, b"signed-doc-1")
        self.assertEqual(result.documents[1].content, b"signed-doc-2")
        self.assertEqual(result.audit_trail_bytes, b"audit-trail-pdf")
        self.assertEqual(result.certificate_bytes, b"certificate-pdf")

    def test_parse_download_document_response_certificate_optional_when_absent(self):
        result = parse_download_document_response(_download_response_xml(include_certificate=False))
        self.assertEqual(len(result.documents), 2)
        self.assertEqual(result.audit_trail_bytes, b"audit-trail-pdf")
        self.assertIsNone(result.certificate_bytes)

    def test_parse_download_document_response_document_count_mismatch(self):
        result = parse_download_document_response(
            _download_response_xml(include_certificate=False, extra_document=True)
        )
        self.assertEqual(len(result.documents), 3)

    def test_parse_download_document_response_handles_live_form_and_audit_report_tags(self):
        result = parse_download_document_response(
            _live_style_download_response_xml(include_certificate=True)
        )
        self.assertEqual(len(result.documents), 2)
        self.assertEqual(result.documents[0].ref_id, "Form-1")
        self.assertEqual(result.documents[1].content, b"signed-doc-2")
        self.assertEqual(result.audit_trail_bytes, b"audit-trail-pdf")
        self.assertEqual(result.certificate_bytes, b"certificate-pdf")


class DownloadDocumentClientTests(TestCase):
    def setUp(self):
        self.config = SignixConfig(
            demo_only=True,
            sponsor="sponsor",
            client="client",
            user_id="user",
            password="secret",
            workgroup="wg",
        )

    @patch("apps.deals.signix.requests.post")
    def test_download_document_posts_expected_method_and_parses_result(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = _download_response_xml(include_certificate=True)

        result = download_document("DS-123", self.config)

        self.assertEqual(len(result.documents), 2)
        self.assertEqual(result.audit_trail_bytes, b"audit-trail-pdf")
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args[0][0], SIGNIX_ENDPOINT_WEBTEST)
        self.assertEqual(mock_post.call_args[1]["data"]["method"], "DownloadDocument")
        self.assertIn("<DocumentSetID>DS-123</DocumentSetID>", mock_post.call_args[1]["data"]["request"])

    @patch("apps.deals.signix.requests.post")
    def test_download_document_http_500_raises_signix_api_error(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Server error"
        with self.assertRaises(SignixApiError) as ctx:
            download_document("DS-123", self.config)
        self.assertIn("HTTP 500", ctx.exception.message)

    @patch("apps.deals.signix.requests.post")
    def test_download_document_request_exception_raises_signix_api_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("boom")
        with self.assertRaises(SignixApiError) as ctx:
            download_document("DS-123", self.config)
        self.assertIn("DownloadDocument failed", ctx.exception.message)


def _make_pdf():
    return SimpleUploadedFile("doc.pdf", b"%PDF-1.4 minimal", content_type="application/pdf")


class DownloadSignedDocumentsOnCompleteTests(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        override = self.settings(MEDIA_ROOT=self.tempdir.name)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(self.tempdir.cleanup)

        self.user = User.objects.create_user(
            username="downloaduser",
            email="download@example.com",
            password="test",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Download",
            last_name="User",
            email="download@example.com",
            phone_number="555-0000",
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
            ref_id="DownloadTest",
            description="Download test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Download Template"},
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
        self.instance1 = DocumentInstance.objects.create(
            document_set=self.document_set,
            order=1,
            content_type=ct,
            object_id=self.static_tpl.pk,
            template_type="static",
        )
        self.instance2 = DocumentInstance.objects.create(
            document_set=self.document_set,
            order=2,
            content_type=ct,
            object_id=self.static_tpl.pk,
            template_type="static",
        )
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance1,
            version_number=1,
            status="Submitted to SIGNiX",
            file=_make_pdf(),
        )
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance2,
            version_number=1,
            status="Submitted to SIGNiX",
            file=_make_pdf(),
        )
        self.config = get_signix_config()
        self.config.sponsor = "sponsor"
        self.config.client = "client"
        self.config.user_id = "user"
        self.config.password = "secret"
        self.config.workgroup = "wg"
        self.config.save()
        self.transaction = SignatureTransaction.objects.create(
            deal=self.deal,
            document_set=self.document_set,
            signix_document_set_id="DS-DOWNLOAD-INT",
            status=SignatureTransaction.STATUS_COMPLETE,
        )
        self.download_result = DownloadDocumentResult(
            documents=[
                DownloadedDocument(content=b"signed-doc-1", filename="signed-1.pdf", ref_id="Form-1"),
                DownloadedDocument(content=b"signed-doc-2", filename="signed-2.pdf", ref_id="Form-2"),
            ],
            audit_trail_bytes=b"audit-trail-pdf",
            certificate_bytes=b"certificate-pdf",
        )

    @patch("apps.deals.signix.download_document")
    def test_download_signed_documents_on_complete_skips_when_already_processed(self, mock_download_document):
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance1,
            version_number=2,
            status="Final",
            file=_make_pdf(),
        )
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance2,
            version_number=2,
            status="Final",
            file=_make_pdf(),
        )

        download_signed_documents_on_complete(self.transaction)

        mock_download_document.assert_not_called()

    @patch("apps.deals.signix.confirm_download")
    @patch("apps.deals.signix.download_document")
    def test_download_signed_documents_on_complete_does_not_skip_when_only_older_final_versions_exist(
        self,
        mock_download_document,
        mock_confirm_download,
    ):
        old_final1 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance1,
            version_number=2,
            status="Final",
            file=_make_pdf(),
        )
        old_final2 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance2,
            version_number=2,
            status="Final",
            file=_make_pdf(),
        )
        current_submitted1 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance1,
            version_number=3,
            status="Submitted to SIGNiX",
            file=_make_pdf(),
        )
        current_submitted2 = DocumentInstanceVersion.objects.create(
            document_instance=self.instance2,
            version_number=3,
            status="Submitted to SIGNiX",
            file=_make_pdf(),
        )
        self.transaction.submitted_at = max(
            current_submitted1.created_at,
            current_submitted2.created_at,
        ) + timezone.timedelta(seconds=1)
        self.transaction.save(update_fields=["submitted_at"])
        mock_download_document.return_value = self.download_result

        download_signed_documents_on_complete(self.transaction)

        self.assertEqual(self.instance1.versions.first().version_number, 4)
        self.assertEqual(self.instance1.versions.first().status, "Final")
        self.assertEqual(self.instance2.versions.first().version_number, 4)
        self.assertEqual(self.instance2.versions.first().status, "Final")
        self.assertNotEqual(self.instance1.versions.first().pk, old_final1.pk)
        self.assertNotEqual(self.instance2.versions.first().pk, old_final2.pk)
        mock_download_document.assert_called_once()
        mock_confirm_download.assert_called_once()

    @patch("apps.deals.signix.confirm_download")
    @patch("apps.deals.signix.download_document")
    def test_download_signed_documents_on_complete_creates_versions_and_stores_audit_certificate(
        self,
        mock_download_document,
        mock_confirm_download,
    ):
        mock_download_document.return_value = self.download_result

        download_signed_documents_on_complete(self.transaction)

        latest1 = self.instance1.versions.first()
        latest2 = self.instance2.versions.first()
        self.assertEqual(latest1.status, "Final")
        self.assertEqual(latest1.version_number, 2)
        self.assertEqual(latest2.status, "Final")
        self.assertEqual(latest2.version_number, 2)
        latest1.file.open("rb")
        self.assertEqual(latest1.file.read(), b"signed-doc-1")
        latest1.file.close()
        self.transaction.refresh_from_db()
        self.assertTrue(self.transaction.audit_trail_file)
        self.assertTrue(self.transaction.certificate_of_completion_file)
        self.assertEqual(mock_confirm_download.call_count, 1)

    @patch("apps.deals.signix.confirm_download")
    @patch("apps.deals.signix.download_document")
    def test_download_signed_documents_on_complete_calls_confirm_download(
        self,
        mock_download_document,
        mock_confirm_download,
    ):
        mock_download_document.return_value = self.download_result

        download_signed_documents_on_complete(self.transaction)

        mock_confirm_download.assert_called_once_with("DS-DOWNLOAD-INT", self.config)

    @patch("apps.deals.signix.confirm_download")
    @patch("apps.deals.signix.download_document")
    def test_audit_trail_failure_does_not_fail_flow(self, mock_download_document, mock_confirm_download):
        mock_download_document.return_value = DownloadDocumentResult(
            documents=self.download_result.documents,
            audit_trail_bytes=None,
            certificate_bytes=None,
        )

        download_signed_documents_on_complete(self.transaction)

        self.instance1.refresh_from_db()
        self.instance2.refresh_from_db()
        self.assertEqual(self.instance1.versions.first().status, "Final")
        self.assertEqual(self.instance2.versions.first().status, "Final")
        self.transaction.refresh_from_db()
        self.assertFalse(self.transaction.audit_trail_file)
        self.assertFalse(self.transaction.certificate_of_completion_file)
        mock_confirm_download.assert_called_once()

"""
Tests for Plan 5: build SubmitDocument body — validation and data dict (Batch 1).
"""

from decimal import Decimal
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.deals.signix import (
    SignixValidationError,
    validate_submit_preconditions,
    build_submit_data_dict,
    build_submit_document_body,
    _build_transaction_id,
    get_signix_config,
    get_signer_authentication_for_slot,
    AUTH_SELECT_ONE_CLICK,
    AUTH_SMS_ONE_CLICK,
)
from apps.deals.models import Deal, DealType, SignixConfig
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


class ValidateSubmitPreconditionsTests(TestCase):
    """Plan 5 Batch 1: validate_submit_preconditions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="builduser",
            email="build@example.com",
            password="test",
            first_name="Build",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Build",
            last_name="Officer",
            email="build@example.com",
            phone_number="555-0000",
        )
        self.contact = Contact.objects.create(
            first_name="Jane",
            middle_name="",
            last_name="Doe",
            email="jane@example.com",
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
        # Document set template with slots 1, 2
        self.static_tpl = StaticDocumentTemplate.objects.create(
            ref_id="BuildTest",
            description="Build test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Build Test Template"},
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
        self.config.save()

    def test_valid_passes(self):
        validate_submit_preconditions(self.deal, self.document_set)

    def test_none_document_set_raises(self):
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(self.deal, None)
        self.assertTrue(any("Document set is required" in e for e in cm.exception.errors))

    def test_wrong_deal_raises(self):
        other_deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("100.00"),
        )
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(other_deal, self.document_set)
        self.assertTrue(any("does not belong" in e for e in cm.exception.errors))

    def test_no_instances_raises(self):
        self.instance.delete()
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(self.deal, self.document_set)
        self.assertTrue(any("no instances" in e.lower() for e in cm.exception.errors))

    def test_instance_without_file_raises(self):
        self.version.file = None
        self.version.save(update_fields=["file"])
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(self.deal, self.document_set)
        self.assertTrue(any("no file" in e.lower() for e in cm.exception.errors))

    def test_unresolved_signer_raises(self):
        self.deal.contacts.clear()
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(self.deal, self.document_set)
        self.assertTrue(any("slot" in e.lower() and "resolved" in e.lower() for e in cm.exception.errors))

    def test_no_submitter_email_raises(self):
        self.config.submitter_email = ""
        self.config.save()
        with self.assertRaises(SignixValidationError) as cm:
            validate_submit_preconditions(self.deal, self.document_set)
        self.assertTrue(any("submitter" in e.lower() for e in cm.exception.errors))


class BuildSubmitDataDictTests(TestCase):
    """Plan 5 Batch 1: build_submit_data_dict and _build_transaction_id."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="dictuser",
            email="dict@example.com",
            password="test",
            first_name="Dict",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Dict",
            last_name="Officer",
            email="dict@example.com",
            phone_number="555-2222",
        )
        self.contact = Contact.objects.create(
            first_name="Bob",
            middle_name="M",
            last_name="Contact",
            email="bob@example.com",
            phone_number="555-3333",
        )
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("200.00"),
        )
        self.deal.contacts.add(self.contact)
        self.static_tpl = StaticDocumentTemplate.objects.create(
            ref_id="DictTest",
            description="Dict test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Dict Test Template"},
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
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance,
            version_number=1,
            status="Draft",
            file=_make_pdf(),
        )
        self.config = get_signix_config()
        self.config.submitter_email = "submit@example.com"
        self.config.save()

    def test_build_transaction_id_is_uuid_36_chars(self):
        tid = _build_transaction_id()
        self.assertEqual(len(tid), 36)
        self.assertRegex(tid, r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    def test_build_submit_data_dict_structure(self):
        validate_submit_preconditions(self.deal, self.document_set)
        data = build_submit_data_dict(self.deal, self.document_set, self.config)
        self.assertIn("cust_info", data)
        self.assertIn("transaction_data", data)
        self.assertIn("signers", data)
        self.assertIn("transaction_id", data)
        self.assertEqual(data["transaction_id"], data["transaction_data"]["transactionId"])

    def test_cust_info_populated(self):
        validate_submit_preconditions(self.deal, self.document_set)
        data = build_submit_data_dict(self.deal, self.document_set, self.config)
        ci = data["cust_info"]
        self.assertIn("sponsor", ci)
        self.assertIn("demo", ci)
        self.assertIn(ci["demo"], ("true", "false"))
        self.assertIn("del_docs_after", ci)

    def test_transaction_data_populated(self):
        validate_submit_preconditions(self.deal, self.document_set)
        data = build_submit_data_dict(self.deal, self.document_set, self.config)
        td = data["transaction_data"]
        self.assertIn("Deal #", td["doc_set_description"])
        self.assertEqual(td["submitter_email"], "submit@example.com")
        self.assertEqual(td["suspend_on_start"], "false")

    def test_signers_populated(self):
        validate_submit_preconditions(self.deal, self.document_set)
        data = build_submit_data_dict(self.deal, self.document_set, self.config)
        signers = data["signers"]
        self.assertEqual(len(signers), 2)
        for s in signers:
            self.assertIn("first_name", s)
            self.assertIn("email", s)
            self.assertIn("service", s)
            self.assertEqual(s["ssn"], "910000000")
            self.assertEqual(s["dob"], "01/01/1990")
        self.assertEqual(signers[0]["first_name"], "Dict")
        self.assertEqual(signers[0]["email"], "dict@example.com")
        self.assertEqual(signers[1]["first_name"], "Bob")
        self.assertEqual(signers[1]["email"], "bob@example.com")

    def test_submitter_phone_default_when_blank(self):
        self.config.submitter_phone = ""
        self.config.save()
        validate_submit_preconditions(self.deal, self.document_set)
        data = build_submit_data_dict(self.deal, self.document_set, self.config)
        self.assertEqual(data["transaction_data"]["submitter_phone"], "800-555-1234")


class BuildSubmitDocumentBodyTests(TestCase):
    """Plan 5 Batch 2: build_submit_document_body returns XML and metadata."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="bodyuser",
            email="body@example.com",
            password="test",
            first_name="Body",
            last_name="User",
        )
        LeaseOfficerProfile.objects.create(
            user=self.user,
            first_name="Body",
            last_name="Officer",
            email="body@example.com",
            phone_number="555-4444",
        )
        self.contact = Contact.objects.create(
            first_name="Alice",
            middle_name="",
            last_name="Signer",
            email="alice@example.com",
            phone_number="555-5555",
        )
        self.deal_type = DealType.get_default()
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("250.00"),
        )
        self.deal.contacts.add(self.contact)
        self.static_tpl = StaticDocumentTemplate.objects.create(
            ref_id="BodyTest",
            description="Body test",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        self.doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=self.deal_type,
            defaults={"name": "Body Test Template"},
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
        DocumentInstanceVersion.objects.create(
            document_instance=self.instance,
            version_number=1,
            status="Draft",
            file=_make_pdf(),
        )
        config = get_signix_config()
        config.submitter_email = "body@example.com"
        config.save()

    def test_returns_tuple_str_dict(self):
        body, metadata = build_submit_document_body(self.deal, self.document_set)
        self.assertIsInstance(body, str)
        self.assertIsInstance(metadata, dict)
        self.assertIn("transaction_id", metadata)

    def test_xml_contains_submit_document_rq_and_cust_info(self):
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("SubmitDocumentRq", body)
        self.assertIn("CustInfo", body)
        self.assertIn("TransactionID", body)
        self.assertIn("MemberInfo", body)

    def test_member_info_count_matches_signers(self):
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertEqual(body.count("<MemberInfo>"), 2)

    def test_member_info_includes_mobile_number(self):
        """MobileNumber is required for SharedSecret/SMS services (e.g. MemberInfo 2)."""
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("<MobileNumber>", body)
        self.assertIn("</MobileNumber>", body)

    def test_form_in_xml(self):
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("<Form>", body)
        self.assertIn("</Form>", body)
        self.assertIn("Length", body)
        self.assertIn("Data", body)

    def test_static_form_includes_date_signed_field_when_configured(self):
        """When static template tagging_data has date_signed_field_name, SubmitDocument includes DateSignedField and DateSignedFormat."""
        self.static_tpl.tagging_data = [
            {
                "member_info_number": 1,
                "tag_name": "SignatureField",
                "date_signed_field_name": "DateField",
                "date_signed_format": "MM/dd/yy",
            },
            {"member_info_number": 2},
        ]
        self.static_tpl.save()
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("<DateSignedField>DateField</DateSignedField>", body)
        self.assertIn("<DateSignedFormat>MM/dd/yy</DateSignedFormat>", body)

    def test_metadata_transaction_id_in_xml(self):
        body, metadata = build_submit_document_body(self.deal, self.document_set)
        tid = metadata["transaction_id"]
        self.assertIn(tid, body)
        self.assertEqual(len(tid), 36)

    def test_xml_contains_doc_set_description_and_submitter(self):
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("DocSetDescription", body)
        self.assertIn("Deal #", body)
        self.assertIn("SubmitterEmail", body)
        self.assertIn("body@example.com", body)
        self.assertIn("SubmitterName", body)
        self.assertIn("Body", body)

    def test_signer_order_reflected_in_member_info_order(self):
        """With signer_order [2, 1], first MemberInfo is slot 2 (Alice), second is slot 1 (Body)."""
        self.deal.signer_order = [2, 1]
        self.deal.save()
        body, _ = build_submit_document_body(self.deal, self.document_set)
        # First <MemberInfo> should contain Alice (slot 2), second should contain Body
        first_member = body.find("<MemberInfo>")
        second_member = body.find("<MemberInfo>", first_member + 1)
        self.assertGreater(second_member, first_member)
        segment_before_second = body[first_member:second_member]
        self.assertIn("Alice", segment_before_second)
        self.assertIn("Signer", segment_before_second)
        segment_after_second = body[second_member:]
        self.assertIn("Body", segment_after_second)

    def test_service_element_contains_auth_value(self):
        """Service element in XML contains SelectOneClick or SMSOneClick."""
        body, _ = build_submit_document_body(self.deal, self.document_set)
        self.assertIn("<Service>", body)
        self.assertTrue(
            AUTH_SELECT_ONE_CLICK in body or AUTH_SMS_ONE_CLICK in body,
            "XML should contain at least one auth type in Service element",
        )

"""
Tests for apps.deals.signix (Plan 3 signer service).
"""

from decimal import Decimal
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.deals.signix import (
    get_signers_for_document_set_template,
    resolve_signer_slot,
    SignerPerson,
    get_signer_order_for_deal,
    get_signer_authentication_for_slot,
    get_role_label_for_slot,
    AUTH_SELECT_ONE_CLICK,
    AUTH_SMS_ONE_CLICK,
)
from apps.deals.models import Deal, DealType
from apps.contacts.models import Contact
from apps.users.models import LeaseOfficerProfile
from apps.doctemplates.models import (
    DocumentSetTemplate,
    DocumentSetTemplateItem,
    StaticDocumentTemplate,
    DynamicDocumentTemplate,
)
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


def _make_pdf():
    return SimpleUploadedFile("doc.pdf", b"%PDF-1.4 minimal", content_type="application/pdf")


def _make_html():
    return SimpleUploadedFile("doc.html", b"<html></html>", content_type="text/html")


class GetSignersForDocumentSetTemplateTests(TestCase):
    """Batch 1: get_signers_for_document_set_template."""

    def test_none_returns_empty_list(self):
        self.assertEqual(get_signers_for_document_set_template(None), [])

    def test_template_with_no_items_returns_empty_list(self):
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixEmpty")
        template, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "Empty Set"}
        )
        self.assertEqual(get_signers_for_document_set_template(template), [])

    def test_one_static_template_with_tagging_data_returns_sorted_slots(self):
        static = StaticDocumentTemplate.objects.create(
            ref_id="TestStatic",
            description="Test",
            file=_make_pdf(),
            tagging_data=[
                {"member_info_number": 1},
                {"member_info_number": 2},
            ],
        )
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixOne")
        doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "One Template"}
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=doc_set_tpl,
            order=1,
            content_type=ct,
            object_id=static.pk,
        )
        result = get_signers_for_document_set_template(doc_set_tpl)
        self.assertEqual(result, [1, 2])

    def test_two_templates_both_with_slots_returns_unique_sorted(self):
        static = StaticDocumentTemplate.objects.create(
            ref_id="StaticA",
            description="A",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        dynamic = DynamicDocumentTemplate.objects.create(
            ref_id="DynamicB",
            description="B",
            file=_make_html(),
            tagging_data=[{"member_info_number": 2}, {"member_info_number": 1}],
        )
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixTwo")
        doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "Two Templates"}
        )
        ct_static = ContentType.objects.get_for_model(StaticDocumentTemplate)
        ct_dynamic = ContentType.objects.get_for_model(DynamicDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=doc_set_tpl, order=1, content_type=ct_static, object_id=static.pk
        )
        DocumentSetTemplateItem.objects.create(
            document_set_template=doc_set_tpl, order=2, content_type=ct_dynamic, object_id=dynamic.pk
        )
        result = get_signers_for_document_set_template(doc_set_tpl)
        self.assertEqual(result, [1, 2])

    def test_tagging_data_non_int_or_missing_ignored(self):
        static = StaticDocumentTemplate.objects.create(
            ref_id="Mixed",
            description="Mixed",
            file=_make_pdf(),
            tagging_data=[
                {"member_info_number": 1},
                {"member_info_number": "two"},  # not int, ignored
                {"other_key": 2},  # no member_info_number, ignored
                {"member_info_number": 2},
                {"member_info_number": None},  # ignored
            ],
        )
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixMixed")
        doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "Mixed"}
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=doc_set_tpl, order=1, content_type=ct, object_id=static.pk
        )
        result = get_signers_for_document_set_template(doc_set_tpl)
        self.assertEqual(result, [1, 2])

    def test_empty_tagging_data_returns_empty_list(self):
        static = StaticDocumentTemplate.objects.create(
            ref_id="NoSlots",
            description="No slots",
            file=_make_pdf(),
            tagging_data=[],
        )
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixNoSlots")
        doc_set_tpl, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "No Slots"}
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=doc_set_tpl, order=1, content_type=ct, object_id=static.pk
        )
        self.assertEqual(get_signers_for_document_set_template(doc_set_tpl), [])


class ResolveSignerSlotTests(TestCase):
    """Batch 2: resolve_signer_slot and SignerPerson."""

    def setUp(self):
        self.user_with_profile = User.objects.create_user(
            username="officer1",
            email="officer1@example.com",
            password="test",
            first_name="Django",
            last_name="Officer",
        )
        self.profile = LeaseOfficerProfile.objects.create(
            user=self.user_with_profile,
            first_name="Lease",
            last_name="Officer",
            email="lease@example.com",
            phone_number="555-0100",
        )
        self.user_no_profile = User.objects.create_user(
            username="officer2",
            email="officer2@example.com",
            password="test",
            first_name="Plain",
            last_name="User",
        )
        self.deal_type = DealType.get_default()
        self.deal_with_officer_and_contact = Deal.objects.create(
            lease_officer=self.user_with_profile,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("500.00"),
        )
        self.contact = Contact.objects.create(
            first_name="Jane",
            middle_name="M",
            last_name="Contact",
            email="jane@example.com",
            phone_number="555-0200",
        )
        self.deal_with_officer_and_contact.contacts.add(self.contact)

    def test_slot1_with_lease_officer_profile_returns_profile_data(self):
        person = resolve_signer_slot(self.deal_with_officer_and_contact, 1)
        self.assertIsInstance(person, SignerPerson)
        self.assertEqual(person.first_name, "Lease")
        self.assertEqual(person.middle_name, "")
        self.assertEqual(person.last_name, "Officer")
        self.assertEqual(person.email, "lease@example.com")
        self.assertEqual(person.phone, "555-0100")

    def test_slot1_without_profile_uses_user_fallback(self):
        deal = Deal.objects.create(
            lease_officer=self.user_no_profile,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("400.00"),
        )
        person = resolve_signer_slot(deal, 1)
        self.assertIsInstance(person, SignerPerson)
        self.assertEqual(person.first_name, "Plain")
        self.assertEqual(person.middle_name, "")
        self.assertEqual(person.last_name, "User")
        self.assertEqual(person.email, "officer2@example.com")
        self.assertEqual(person.phone, "")

    def test_slot1_user_with_blank_full_name_uses_username(self):
        user_blank = User.objects.create_user(
            username="blankuser",
            email="blank@example.com",
            password="test",
            first_name="",
            last_name="",
        )
        deal = Deal.objects.create(
            lease_officer=user_blank,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("100.00"),
        )
        person = resolve_signer_slot(deal, 1)
        self.assertIsInstance(person, SignerPerson)
        self.assertEqual(person.first_name, "blankuser")
        self.assertEqual(person.last_name, "")
        self.assertEqual(person.email, "blank@example.com")

    def test_slot2_with_contact_returns_contact_data(self):
        person = resolve_signer_slot(self.deal_with_officer_and_contact, 2)
        self.assertIsInstance(person, SignerPerson)
        self.assertEqual(person.first_name, "Jane")
        self.assertEqual(person.middle_name, "M")
        self.assertEqual(person.last_name, "Contact")
        self.assertEqual(person.email, "jane@example.com")
        self.assertEqual(person.phone, "555-0200")

    def test_slot2_no_contacts_returns_none(self):
        deal = Deal.objects.create(
            lease_officer=self.user_with_profile,
            deal_type=self.deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("300.00"),
        )
        self.assertIsNone(resolve_signer_slot(deal, 2))

    def test_slot1_no_lease_officer_returns_none(self):
        self.deal_with_officer_and_contact.lease_officer = None
        self.assertIsNone(resolve_signer_slot(self.deal_with_officer_and_contact, 1))

    def test_slot3_returns_none(self):
        self.assertIsNone(resolve_signer_slot(self.deal_with_officer_and_contact, 3))


class SignerOrderAndAuthHelpersTests(TestCase):
    """Plan 4 Batch 1: get_signer_order_for_deal, get_signer_authentication_for_slot, get_role_label_for_slot."""

    def setUp(self):
        """Template with slots [1, 2] for order tests."""
        static = StaticDocumentTemplate.objects.create(
            ref_id="Plan4Static",
            description="Plan 4",
            file=_make_pdf(),
            tagging_data=[{"member_info_number": 1}, {"member_info_number": 2}],
        )
        deal_type, _ = DealType.objects.get_or_create(name="TestSignixPlan4")
        self.template, _ = DocumentSetTemplate.objects.get_or_create(
            deal_type=deal_type, defaults={"name": "Plan 4 Template"}
        )
        ct = ContentType.objects.get_for_model(StaticDocumentTemplate)
        DocumentSetTemplateItem.objects.create(
            document_set_template=self.template, order=1, content_type=ct, object_id=static.pk
        )
        self.user = User.objects.create_user(
            username="plan4user", email="p4@example.com", password="test"
        )
        self.deal = Deal.objects.create(
            lease_officer=self.user,
            deal_type=deal_type,
            date_entered=date(2025, 1, 1),
            lease_start_date=date(2025, 2, 1),
            lease_end_date=date(2026, 1, 31),
            payment_amount=Decimal("200.00"),
        )

    def test_get_signer_order_empty_uses_template_order(self):
        self.assertIsNone(self.deal.signer_order)
        self.assertEqual(get_signer_order_for_deal(self.deal, self.template), [1, 2])

    def test_get_signer_order_set_returns_deal_order(self):
        self.deal.signer_order = [2, 1]
        self.deal.save()
        self.assertEqual(get_signer_order_for_deal(self.deal, self.template), [2, 1])

    def test_get_signer_order_empty_list_uses_template_order(self):
        self.deal.signer_order = []
        self.deal.save()
        self.assertEqual(get_signer_order_for_deal(self.deal, self.template), [1, 2])

    def test_get_signer_authentication_defaults(self):
        self.assertIsNone(self.deal.signer_authentication)
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 1), AUTH_SELECT_ONE_CLICK
        )
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 2), AUTH_SMS_ONE_CLICK
        )
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 3), AUTH_SELECT_ONE_CLICK
        )

    def test_get_signer_authentication_from_deal(self):
        self.deal.signer_authentication = {"2": AUTH_SELECT_ONE_CLICK}
        self.deal.save()
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 1), AUTH_SELECT_ONE_CLICK
        )
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 2), AUTH_SELECT_ONE_CLICK
        )

    def test_get_signer_authentication_invalid_value_uses_default(self):
        self.deal.signer_authentication = {"1": "InvalidAuth"}
        self.deal.save()
        self.assertEqual(
            get_signer_authentication_for_slot(self.deal, 1), AUTH_SELECT_ONE_CLICK
        )

    def test_get_role_label_for_slot(self):
        self.assertEqual(get_role_label_for_slot(1), "Lease officer")
        self.assertEqual(get_role_label_for_slot(2), "Lessee")
        self.assertEqual(get_role_label_for_slot(3), "Signer 3")

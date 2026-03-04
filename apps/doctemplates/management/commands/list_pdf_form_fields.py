"""
List AcroForm field names in a PDF (for configuring signature_field_names).

Usage:
    python manage.py list_pdf_form_fields <path_to.pdf>
    python manage.py list_pdf_form_fields --template <StaticDocumentTemplate.ref_id>

Use the output to set signature_field_names on your Static document template
(e.g. {"1": "LessorSignature", "2": "LesseeSignature"}) when SIGNiX reports
"Could not find form field(s): Lessor Lessee".
"""

from django.core.management.base import BaseCommand


def get_pdf_fields(path: str) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf is required. Install with: pip install pypdf")
    reader = PdfReader(path)
    fields = reader.get_fields()
    if fields is None:
        return []
    return sorted(fields.keys())


class Command(BaseCommand):
    help = "List PDF AcroForm field names (for SIGNiX signature_field_names)."

    def add_arguments(self, parser):
        parser.add_argument(
            "pdf_path",
            nargs="?",
            type=str,
            help="Path to a PDF file.",
        )
        parser.add_argument(
            "--template",
            "-t",
            type=str,
            help="StaticDocumentTemplate ref_id: use that template's PDF file.",
        )

    def handle(self, *args, **options):
        pdf_path = options.get("pdf_path")
        template_ref = options.get("template")

        if template_ref:
            from apps.doctemplates.models import StaticDocumentTemplate

            t = StaticDocumentTemplate.objects.filter(ref_id=template_ref).first()
            if t is None or not t.file:
                self.stderr.write(self.style.ERROR(f"Template '{template_ref}' not found or has no file."))
                return 1
            pdf_path = t.file.path
            self.stdout.write(f"Using template file: {pdf_path}\n")

        if not pdf_path:
            self.stderr.write(self.style.ERROR("Provide pdf_path or --template <ref_id>."))
            return 1

        try:
            names = get_pdf_fields(pdf_path)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {pdf_path}"))
            return 1
        except RuntimeError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return 1

        if not names:
            self.stdout.write("No AcroForm fields found in this PDF.")
            return 0

        self.stdout.write("AcroForm field names (use these in signature_field_names):")
        for name in names:
            self.stdout.write(f"  {name}")
        self.stdout.write("\nExample signature_field_names (edit in Admin → Static document templates):")
        self.stdout.write('  {"1": "%s", "2": "%s"}' % (names[0], names[1] if len(names) > 1 else names[0]))
        return 0

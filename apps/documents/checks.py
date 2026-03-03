"""
Django system checks for the documents app.

Registers a check for wkhtmltopdf availability so `manage.py check` can report it.
"""

from django.core.checks import Warning, register

from .services import check_wkhtmltopdf_available


@register()
def check_wkhtmltopdf(app_configs, **kwargs):
    """
    Warn if wkhtmltopdf is not installed.

    Dynamic document generation requires wkhtmltopdf on PATH.
    """
    errors = []
    if not check_wkhtmltopdf_available():
        errors.append(
            Warning(
                "wkhtmltopdf is not installed or not on PATH. Dynamic document "
                "generation (HTML to PDF) will fail. Install from "
                "https://wkhtmltopdf.org/ or via your package manager "
                "(e.g. apt install wkhtmltopdf, brew install wkhtmltopdf).",
                id="documents.W001",
            )
        )
    return errors

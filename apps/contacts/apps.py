from django.apps import AppConfig


class ContactsConfig(AppConfig):
    """AppConfig for the contacts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts"
    verbose_name = "Contacts"

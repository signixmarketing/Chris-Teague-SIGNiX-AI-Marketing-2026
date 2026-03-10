from django.apps import AppConfig


class DealsConfig(AppConfig):
    """AppConfig for the deals app (lease origination)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.deals"
    verbose_name = "Deals"

    def ready(self):
        import apps.deals.signals  # noqa: F401

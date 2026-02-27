from django.apps import AppConfig


class VehiclesConfig(AppConfig):
    """AppConfig for the vehicles app (jet pack / vehicle catalog)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vehicles"
    verbose_name = "Vehicles"

from django.apps import AppConfig


class ImagesConfig(AppConfig):
    """AppConfig for the images app (uploaded images for document templates)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.images"
    verbose_name = "Images"

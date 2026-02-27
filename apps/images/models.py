"""
Image model for the lease app.

Stores user-uploaded images (e.g. for document templates). Files are stored under
MEDIA_ROOT/images/ with a stable path (by uuid) so the URL does not change when
the user uploads a replacement.
"""

import os
import uuid

from django.db import models


def image_upload_to(instance, filename):
    """Store under images/<uuid>.<ext> so the URL is stable when the file is replaced."""
    ext = os.path.splitext(filename)[1].lower() or ".png"
    return f"images/{instance.uuid}{ext}"


class Image(models.Model):
    """
    A user-uploaded image for use in document templates (e.g. lease logo).

    The relative URL (image.file.url) can be copied into templates. The path
    includes a UUID so replacing the file does not change the URL.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    file = models.ImageField(upload_to=image_upload_to)

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def __str__(self):
        return self.name

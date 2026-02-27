"""
Django admin for images.

Image is registered for backup management from the admin.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["name", "url_display", "image_preview", "uuid"]
    list_filter = []
    search_fields = ["name"]
    readonly_fields = ["uuid", "url_display", "image_preview"]

    def url_display(self, obj):
        if obj.file:
            return obj.file.url
        return "—"

    url_display.short_description = "URL"

    def image_preview(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="max-height: 60px; max-width: 80px; object-fit: contain;">',
                obj.file.url,
            )
        return "—"

    image_preview.short_description = "Preview"

from django.contrib import admin

from .models import DocumentSetTemplate, DocumentSetTemplateItem, StaticDocumentTemplate


@admin.register(StaticDocumentTemplate)
class StaticDocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("ref_id", "description")
    list_filter = ("tagging_type",)
    search_fields = ("ref_id", "description")
    fields = (
        "ref_id",
        "description",
        "file",
        "tagging_type",
        "tagging_data",
        "signature_field_names",
    )


class DocumentSetTemplateItemInline(admin.TabularInline):
    model = DocumentSetTemplateItem
    extra = 0
    fields = ("order", "content_type", "object_id")
    readonly_fields = ("content_type", "object_id")
    ordering = ("order",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DocumentSetTemplate)
class DocumentSetTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "deal_type")
    inlines = [DocumentSetTemplateItemInline]

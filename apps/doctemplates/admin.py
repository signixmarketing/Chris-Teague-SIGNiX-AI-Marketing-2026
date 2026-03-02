from django.contrib import admin

from .models import DocumentSetTemplate, DocumentSetTemplateItem


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

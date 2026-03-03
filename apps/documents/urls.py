"""
URL routing for documents app.

Deal-scoped actions (generate, regenerate, delete) live in apps.deals.
Document Instance and version viewing (Batch 4).
"""

from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("versions/<int:pk>/view/", views.document_version_view, name="document_version_view"),
    path("versions/<int:pk>/download/", views.document_version_download, name="document_version_download"),
    path("instances/<int:pk>/", views.document_instance_detail, name="document_instance_detail"),
]

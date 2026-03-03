"""
URL routing for deals (list, add, edit, delete).
"""

from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.deal_list, name="deal_list"),
    path("add/", views.deal_add, name="deal_add"),
    path("<int:pk>/", views.deal_detail, name="deal_detail"),
    path("<int:pk>/edit/", views.deal_edit, name="deal_edit"),
    path("<int:pk>/delete/", views.deal_delete_confirm, name="deal_delete_confirm"),
    path("<int:pk>/documents/generate/", views.deal_generate_documents, name="deal_generate_documents"),
    path("<int:pk>/documents/regenerate/", views.deal_regenerate_documents, name="deal_regenerate_documents"),
    path("<int:pk>/documents/delete/", views.deal_delete_document_set, name="deal_delete_document_set"),
    path("<int:pk>/documents/send-for-signature/", views.deal_send_for_signature_stub, name="deal_send_for_signature_stub"),
]

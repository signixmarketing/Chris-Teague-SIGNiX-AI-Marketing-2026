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
    path("<int:pk>/documents/send-for-signature/", views.deal_send_for_signature, name="deal_send_for_signature"),
    path("<int:pk>/signatures/delete-all/", views.deal_signature_transaction_delete_all, name="deal_signature_transaction_delete_all"),
    path("signatures/delete-all/", views.signature_transaction_delete_all, name="signature_transaction_delete_all"),
    path("signatures/", views.signature_transaction_list, name="signature_transaction_list"),
    path("signatures/<int:pk>/", views.signature_transaction_detail, name="signature_transaction_detail"),
    path("signatures/<int:pk>/audit-trail/", views.signature_transaction_audit_trail, name="signature_transaction_audit_trail"),
    path("signatures/<int:pk>/certificate/", views.signature_transaction_certificate, name="signature_transaction_certificate"),
    path("<int:pk>/signers/update-auth/", views.deal_signers_update_auth, name="deal_signers_update_auth"),
    path("<int:pk>/signers/reorder/", views.deal_signers_reorder, name="deal_signers_reorder"),
]

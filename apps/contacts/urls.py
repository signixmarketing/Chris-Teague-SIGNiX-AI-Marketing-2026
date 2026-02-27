"""
URL routing for contacts (list, add, edit, delete).
"""

from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.contact_list, name="contact_list"),
    path("add/", views.contact_add, name="contact_add"),
    path("<int:pk>/edit/", views.contact_edit, name="contact_edit"),
    path("<int:pk>/delete/", views.contact_delete_confirm, name="contact_delete_confirm"),
]

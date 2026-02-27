"""
URL routing for deals (list, add, edit, delete).
"""

from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.deal_list, name="deal_list"),
    path("add/", views.deal_add, name="deal_add"),
    path("<int:pk>/edit/", views.deal_edit, name="deal_edit"),
    path("<int:pk>/delete/", views.deal_delete_confirm, name="deal_delete_confirm"),
]

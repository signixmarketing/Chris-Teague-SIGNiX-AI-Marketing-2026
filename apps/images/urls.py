"""
URL routing for images (list, add, edit, delete).
"""

from django.urls import path

from . import views

app_name = "images"

urlpatterns = [
    path("", views.image_list, name="image_list"),
    path("add/", views.image_add, name="image_add"),
    path("<int:pk>/edit/", views.image_edit, name="image_edit"),
    path("<int:pk>/delete/", views.image_delete_confirm, name="image_delete_confirm"),
]

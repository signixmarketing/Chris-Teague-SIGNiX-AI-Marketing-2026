"""
URL routing for vehicles (list, add, edit, delete).
"""

from django.urls import path

from . import views

app_name = "vehicles"

urlpatterns = [
    path("", views.vehicle_list, name="vehicle_list"),
    path("add/", views.vehicle_add, name="vehicle_add"),
    path("<int:pk>/edit/", views.vehicle_edit, name="vehicle_edit"),
    path("<int:pk>/delete/", views.vehicle_delete_confirm, name="vehicle_delete_confirm"),
]

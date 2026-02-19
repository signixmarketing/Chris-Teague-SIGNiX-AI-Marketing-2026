"""
URL routing for profile and app-level routes.

Profile is at /profile/ and /profile/edit/. Root redirect is in config.urls.
"""

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]

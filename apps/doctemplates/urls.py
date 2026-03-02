from django.urls import path

from . import views

app_name = "doctemplates"

urlpatterns = [
    path("static/", views.static_doctemplate_list, name="static_doctemplate_list"),
    path(
        "dynamic/",
        views.dynamic_doctemplate_list,
        name="dynamic_doctemplate_list",
    ),
    path(
        "dynamic/parse/",
        views.dynamic_doctemplate_parse,
        name="dynamic_doctemplate_parse",
    ),
    path(
        "dynamic/add/",
        views.dynamic_doctemplate_add,
        name="dynamic_doctemplate_add",
    ),
    path(
        "dynamic/<int:pk>/edit/",
        views.dynamic_doctemplate_edit,
        name="dynamic_doctemplate_edit",
    ),
    path(
        "dynamic/<int:pk>/delete/",
        views.dynamic_doctemplate_delete_confirm,
        name="dynamic_doctemplate_delete_confirm",
    ),
    path("static/add/", views.static_doctemplate_add, name="static_doctemplate_add"),
    path(
        "static/<int:pk>/edit/",
        views.static_doctemplate_edit,
        name="static_doctemplate_edit",
    ),
    path(
        "static/<int:pk>/delete/",
        views.static_doctemplate_delete_confirm,
        name="static_doctemplate_delete_confirm",
    ),
]

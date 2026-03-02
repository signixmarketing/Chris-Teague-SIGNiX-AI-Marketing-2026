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
        "doc-set-templates/",
        views.docsettemplate_list,
        name="docsettemplate_list",
    ),
    path(
        "doc-set-templates/add/",
        views.docsettemplate_add,
        name="docsettemplate_add",
    ),
    path(
        "doc-set-templates/<int:pk>/edit/",
        views.docsettemplate_edit,
        name="docsettemplate_edit",
    ),
    path(
        "doc-set-templates/<int:pk>/delete/",
        views.docsettemplate_delete_confirm,
        name="docsettemplate_delete_confirm",
    ),
    path(
        "doc-set-templates/<int:pk>/items/<int:item_id>/move-up/",
        views.docsettemplate_item_move_up,
        name="docsettemplate_item_move_up",
    ),
    path(
        "doc-set-templates/<int:pk>/items/<int:item_id>/move-down/",
        views.docsettemplate_item_move_down,
        name="docsettemplate_item_move_down",
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

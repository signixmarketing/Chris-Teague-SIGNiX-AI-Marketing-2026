from django.urls import path

from . import views

app_name = "schema"

urlpatterns = [
    path("", views.schema_view, name="schema_view"),
    path("debug/", views.debug_data_list, name="debug_data_list"),
    path("deal/<int:pk>/data/", views.deal_data_json, name="deal_data_json"),
]

"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from apps.users import views as users_views
from apps.deals.views import signix_config_edit

urlpatterns = [
    path("", users_views.root_redirect, name="root"),
    path("health/", users_views.health, name="health"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.users.urls")),
    path("vehicles/", include("apps.vehicles.urls")),
    path("contacts/", include("apps.contacts.urls")),
    path("deals/", include("apps.deals.urls")),
    path("documents/", include("apps.documents.urls")),
    path("schema/", include("apps.schema.urls")),
    path("images/", include("apps.images.urls")),
    path("document-templates/", include("apps.doctemplates.urls")),
    path("signix/config/", signix_config_edit, name="signix_config"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

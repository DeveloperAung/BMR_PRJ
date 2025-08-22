from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path("auth/", include('authentication.api.routers')),
    path("users/", include('users.api.routers')),
    path("memberships/", include('memberships.api.routers')),

    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

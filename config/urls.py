from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .middleware import health_response


def health(request):
    """Chequeo de salud (normalmente lo responde HealthCheckMiddleware antes de llegar acá)."""
    return health_response()


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    # API
    path("api/auth/", include("accounts.urls")),
    path("api/", include("projects.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Frontend básico
    path("", include("web.urls")),
]

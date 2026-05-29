from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import ensure_csrf_cookie

schema_view = get_schema_view(
    openapi.Info(
        title="Authentication API",
        default_version='v1',
        description="Django Authentication System API",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('django-auth-system/index.html', TemplateView.as_view(template_name='index.html')),
    path('admin/', admin.site.urls),

    path(
    'swagger/',
    ensure_csrf_cookie(
        schema_view.with_ui('swagger', cache_timeout=0)
    ),
    name='schema-swagger-ui'
),

    path('api/', include('authentication.urls')),
]
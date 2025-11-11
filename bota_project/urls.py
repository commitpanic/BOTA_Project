"""
URL configuration for bota_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from .api_router import router
from frontend.health import health_check
from frontend.static_debug import static_files_debug

urlpatterns = [
    # Health check (for monitoring)
    path('health/', health_check, name='health_check'),
    
    # Static files debug (for troubleshooting)
    path('static-debug/', static_files_debug, name='static_debug'),
    
    # Language switcher (not translated)
    path('i18n/setlang/', set_language, name='set_language'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints (not translated for consistency)
    path('api/', include(router.urls)),
    
    # JWT Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Frontend URLs with i18n
urlpatterns += i18n_patterns(
    path('', include('frontend.urls')),
    path('planned-activations/', include('planned_activations.urls')),
)

# Serve static and media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

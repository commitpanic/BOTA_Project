"""
Public API router configuration.
Only includes read-only public endpoints for documentation.
"""
from rest_framework.routers import DefaultRouter
from rest_framework import permissions

# Import only public viewsets
from diplomas.views import DiplomaViewSet, DiplomaTypeViewSet
from accounts.views import UserStatisticsViewSet
from activations.views import ActivationLogViewSet
from cluster.views import ClusterViewSet, SpotViewSet
from bunkers.views import BunkerViewSet

# Create public router
public_router = DefaultRouter()

# Public endpoints (read-only where appropriate)
public_router.register(r'awards', DiplomaViewSet, basename='public-diploma')
public_router.register(r'award-types', DiplomaTypeViewSet, basename='public-diplomatype')
public_router.register(r'stats', UserStatisticsViewSet, basename='public-statistics')
public_router.register(r'activation-stats', ActivationLogViewSet, basename='public-activationlog')
public_router.register(r'clusters', ClusterViewSet, basename='public-cluster')
public_router.register(r'spots', SpotViewSet, basename='public-spot')
public_router.register(r'bunkers', BunkerViewSet, basename='public-bunker')

urlpatterns = public_router.urls

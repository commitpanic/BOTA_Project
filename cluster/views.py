"""
API views for cluster app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import Cluster, ClusterMember, ClusterAlert
from .serializers import (
    ClusterSerializer, ClusterListSerializer,
    ClusterMemberSerializer, ClusterAlertSerializer
)


@extend_schema_view(
    list=extend_schema(description="List clusters", tags=["cluster"]),
    retrieve=extend_schema(description="Retrieve cluster details", tags=["cluster"]),
    create=extend_schema(description="Create new cluster", tags=["cluster"]),
    update=extend_schema(description="Update cluster", tags=["cluster"]),
    destroy=extend_schema(description="Delete cluster", tags=["cluster"]),
)
class ClusterViewSet(viewsets.ModelViewSet):
    """ViewSet for Cluster model"""
    queryset = Cluster.objects.prefetch_related('members', 'alerts')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'is_active']
    search_fields = ['name_en', 'name_pl', 'region']
    
    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == 'list':
            return ClusterListSerializer
        return ClusterSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(description="List cluster members", tags=["cluster"]),
    retrieve=extend_schema(description="Retrieve member details", tags=["cluster"]),
    create=extend_schema(description="Add bunker to cluster", tags=["cluster"]),
    update=extend_schema(description="Update cluster member", tags=["cluster"]),
    destroy=extend_schema(description="Remove bunker from cluster", tags=["cluster"]),
)
class ClusterMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for ClusterMember model"""
    queryset = ClusterMember.objects.select_related('cluster', 'bunker')
    serializer_class = ClusterMemberSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cluster', 'bunker']
    
    def perform_create(self, serializer):
        """Set added_by to current user"""
        serializer.save(added_by=self.request.user)


@extend_schema_view(
    list=extend_schema(description="List cluster alerts", tags=["cluster"]),
    retrieve=extend_schema(description="Retrieve alert details", tags=["cluster"]),
    create=extend_schema(description="Create new alert", tags=["cluster"]),
    update=extend_schema(description="Update alert", tags=["cluster"]),
    destroy=extend_schema(description="Delete alert", tags=["cluster"]),
)
class ClusterAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for ClusterAlert model"""
    queryset = ClusterAlert.objects.select_related('cluster')
    serializer_class = ClusterAlertSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cluster', 'alert_type', 'is_active']
    
    def get_queryset(self):
        """Filter to show only active alerts for non-staff users"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

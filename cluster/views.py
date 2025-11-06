"""
API views for cluster app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import Cluster, ClusterMember, ClusterAlert, Spot
from .serializers import (
    ClusterSerializer, ClusterListSerializer,
    ClusterMemberSerializer, ClusterAlertSerializer, SpotSerializer
)
from django.utils import timezone


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


@extend_schema_view(
    list=extend_schema(description="List active spots", tags=["cluster", "spotting"]),
    retrieve=extend_schema(description="Retrieve spot details", tags=["cluster", "spotting"]),
    create=extend_schema(description="Post a new spot (or refresh existing)", tags=["cluster", "spotting"]),
    destroy=extend_schema(description="Delete your own spot", tags=["cluster", "spotting"]),
)
class SpotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Spot model (real-time spotting system).
    Public read access, authenticated write access.
    """
    serializer_class = SpotSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activator_callsign', 'band', 'is_active']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']  # No PUT/PATCH
    
    def get_queryset(self):
        """Return only active, non-expired spots by default"""
        queryset = Spot.objects.select_related('spotter', 'bunker').filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-updated_at')
        
        # Optional filter by spotter callsign
        spotter = self.request.query_params.get('spotter', None)
        if spotter:
            queryset = queryset.filter(spotter__callsign__iexact=spotter)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set spotter to current user and initialize last_respot_time"""
        serializer.save(spotter=self.request.user, last_respot_time=timezone.now())
    
    def perform_destroy(self, instance):
        """Only allow users to delete their own spots"""
        if instance.spotter != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own spots")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only currently active spots (not expired)"""
        spots = self.get_queryset()
        serializer = self.get_serializer(spots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def respot(self, request, pk=None):
        """
        Re-spot an existing spot with optional new spotter callsign and comment.
        This updates the spot, resets the expiration time, and increments respot_count.
        Also creates a SpotHistory record to track who respotted and when.
        """
        from .models import SpotHistory
        
        original_spot = self.get_object()
        
        # Get new spotter callsign and comment from request
        new_spotter_callsign = request.data.get('spotter_callsign', request.user.callsign)
        new_comment = request.data.get('comment', original_spot.comment or '')
        
        # Create history record for this respot
        SpotHistory.objects.create(
            spot=original_spot,
            respotter=request.user,
            comment=new_comment
        )
        
        # Update the spot
        original_spot.spotter = request.user
        original_spot.comment = new_comment
        original_spot.respot_count += 1
        original_spot.last_respot_time = timezone.now()  # Track respot time
        original_spot.refresh_expiration()  # Extends by 30 minutes
        original_spot.save()  # Save changes to database
        
        serializer = self.get_serializer(original_spot)
        return Response({
            'message': 'Spot re-posted successfully',
            'respot_count': original_spot.respot_count,
            'spot': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get respot history for a specific spot.
        Returns list of respots with respotter callsign and timestamp.
        """
        from .models import SpotHistory
        
        spot = self.get_object()
        history = SpotHistory.objects.filter(spot=spot).select_related('respotter').order_by('-respotted_at')
        
        history_data = [
            {
                'respotter': h.respotter.callsign,
                'respotted_at': h.respotted_at,
                'comment': h.comment or ''
            }
            for h in history
        ]
        
        return Response({
            'spot_id': spot.id,
            'activator': spot.activator_callsign,
            'total_respots': spot.respot_count,
            'history': history_data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def cleanup_expired(self, request):
        """Mark expired spots as inactive (admin only)"""
        count = Spot.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).update(is_active=False)
        return Response({'message': f'Marked {count} spots as inactive'})

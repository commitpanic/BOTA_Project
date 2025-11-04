"""
API views for bunkers app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import BunkerCategory, Bunker, BunkerPhoto, BunkerResource, BunkerInspection
from .serializers import (
    BunkerCategorySerializer, BunkerSerializer, BunkerListSerializer,
    BunkerPhotoSerializer, BunkerResourceSerializer, BunkerInspectionSerializer
)


@extend_schema_view(
    list=extend_schema(description="List bunker categories", tags=["bunkers"]),
    retrieve=extend_schema(description="Retrieve category details", tags=["bunkers"]),
    create=extend_schema(description="Create new category", tags=["bunkers"]),
    update=extend_schema(description="Update category", tags=["bunkers"]),
    destroy=extend_schema(description="Delete category", tags=["bunkers"]),
)
class BunkerCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for BunkerCategory model"""
    queryset = BunkerCategory.objects.all()
    serializer_class = BunkerCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema_view(
    list=extend_schema(description="List bunkers", tags=["bunkers"]),
    retrieve=extend_schema(description="Retrieve bunker details", tags=["bunkers"]),
    create=extend_schema(description="Create new bunker", tags=["bunkers"]),
    update=extend_schema(description="Update bunker", tags=["bunkers"]),
    destroy=extend_schema(description="Delete bunker", tags=["bunkers"]),
)
class BunkerViewSet(viewsets.ModelViewSet):
    """ViewSet for Bunker model"""
    queryset = Bunker.objects.select_related('category', 'created_by', 'verified_by').prefetch_related('photos', 'resources')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_verified']
    search_fields = ['reference_number', 'name_en', 'name_pl']
    
    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == 'list':
            return BunkerListSerializer
        return BunkerSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(description="List bunker photos", tags=["bunkers"]),
    retrieve=extend_schema(description="Retrieve photo details", tags=["bunkers"]),
    create=extend_schema(description="Upload bunker photo", tags=["bunkers"]),
    update=extend_schema(description="Update photo", tags=["bunkers"]),
    destroy=extend_schema(description="Delete photo", tags=["bunkers"]),
)
class BunkerPhotoViewSet(viewsets.ModelViewSet):
    """ViewSet for BunkerPhoto model"""
    queryset = BunkerPhoto.objects.select_related('bunker', 'uploaded_by', 'approved_by')
    serializer_class = BunkerPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bunker']
    
    def perform_create(self, serializer):
        """Set uploaded_by to current user"""
        serializer.save(uploaded_by=self.request.user)
    
    @extend_schema(description="Approve photo", tags=["bunkers"])
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a bunker photo"""
        from django.utils import timezone
        photo = self.get_object()
        photo.is_approved = True
        photo.approved_by = request.user
        photo.approval_date = timezone.now()
        photo.save()
        return Response({'status': 'photo approved'})


@extend_schema_view(
    list=extend_schema(description="List bunker resources", tags=["bunkers"]),
    retrieve=extend_schema(description="Retrieve resource details", tags=["bunkers"]),
    create=extend_schema(description="Add bunker resource", tags=["bunkers"]),
    update=extend_schema(description="Update resource", tags=["bunkers"]),
    destroy=extend_schema(description="Delete resource", tags=["bunkers"]),
)
class BunkerResourceViewSet(viewsets.ModelViewSet):
    """ViewSet for BunkerResource model"""
    queryset = BunkerResource.objects.select_related('bunker', 'added_by')
    serializer_class = BunkerResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bunker', 'resource_type']
    
    def perform_create(self, serializer):
        """Set added_by to current user"""
        serializer.save(added_by=self.request.user)


@extend_schema_view(
    list=extend_schema(description="List bunker inspections", tags=["bunkers"]),
    retrieve=extend_schema(description="Retrieve inspection details", tags=["bunkers"]),
    create=extend_schema(description="Log bunker inspection", tags=["bunkers"]),
    update=extend_schema(description="Update inspection", tags=["bunkers"]),
)
class BunkerInspectionViewSet(viewsets.ModelViewSet):
    """ViewSet for BunkerInspection model"""
    queryset = BunkerInspection.objects.select_related('bunker', 'user')
    serializer_class = BunkerInspectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bunker', 'verified']
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)

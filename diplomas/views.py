"""
API views for diplomas app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification
from .serializers import (
    DiplomaTypeSerializer, DiplomaSerializer, DiplomaListSerializer,
    DiplomaProgressSerializer, DiplomaVerificationSerializer,
    DiplomaVerifySerializer, DiplomaProgressUpdateSerializer
)


@extend_schema_view(
    list=extend_schema(description="List diploma types", tags=["diplomas"]),
    retrieve=extend_schema(description="Retrieve diploma type details", tags=["diplomas"]),
    create=extend_schema(description="Create new diploma type", tags=["diplomas"]),
    update=extend_schema(description="Update diploma type", tags=["diplomas"]),
    destroy=extend_schema(description="Delete diploma type", tags=["diplomas"]),
)
class DiplomaTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for DiplomaType model"""
    queryset = DiplomaType.objects.all()
    serializer_class = DiplomaTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name_en', 'name_pl']
    
    def get_queryset(self):
        """Filter to show only active types for non-staff users"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


@extend_schema_view(
    list=extend_schema(description="List issued diplomas", tags=["diplomas"]),
    retrieve=extend_schema(description="Retrieve diploma details", tags=["diplomas"]),
    create=extend_schema(description="Issue new diploma", tags=["diplomas"]),
    update=extend_schema(description="Update diploma", tags=["diplomas"]),
    destroy=extend_schema(description="Revoke diploma", tags=["diplomas"]),
)
class DiplomaViewSet(viewsets.ModelViewSet):
    """ViewSet for Diploma model"""
    queryset = Diploma.objects.select_related('diploma_type', 'user', 'issued_by')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'diploma_type']
    search_fields = ['diploma_number']
    
    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == 'list':
            return DiplomaListSerializer
        return DiplomaSerializer
    
    def perform_create(self, serializer):
        """Set issued_by to current user"""
        serializer.save(issued_by=self.request.user)
    
    @extend_schema(
        description="Verify a diploma by number or code",
        request=DiplomaVerifySerializer,
        responses={200: DiplomaSerializer},
        tags=["diplomas"]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def verify(self, request):
        """Verify a diploma"""
        serializer = DiplomaVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        diploma = None
        if serializer.validated_data.get('diploma_number'):
            try:
                diploma = Diploma.objects.get(
                    diploma_number=serializer.validated_data['diploma_number']
                )
            except Diploma.DoesNotExist:
                pass
        
        if not diploma and serializer.validated_data.get('verification_code'):
            try:
                diploma = Diploma.objects.get(
                    verification_code=serializer.validated_data['verification_code']
                )
            except Diploma.DoesNotExist:
                pass
        
        if not diploma:
            return Response(
                {'error': 'Diploma not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log verification
        DiplomaVerification.objects.create(
            diploma=diploma,
            verified_by_ip=request.META.get('REMOTE_ADDR'),
            verified_by_user=request.user if request.user.is_authenticated else None,
            verification_method='number' if serializer.validated_data.get('diploma_number') else 'code'
        )
        
        return Response(DiplomaSerializer(diploma).data)


@extend_schema_view(
    list=extend_schema(description="List diploma progress", tags=["diplomas"]),
    retrieve=extend_schema(description="Retrieve progress details", tags=["diplomas"]),
    create=extend_schema(description="Create progress tracker", tags=["diplomas"]),
    update=extend_schema(description="Update progress", tags=["diplomas"]),
    destroy=extend_schema(description="Delete progress tracker", tags=["diplomas"]),
)
class DiplomaProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for DiplomaProgress model"""
    queryset = DiplomaProgress.objects.select_related('user', 'diploma_type')
    serializer_class = DiplomaProgressSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'diploma_type', 'is_eligible']
    
    def get_queryset(self):
        """Filter progress based on user permissions"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Non-staff can only see their own progress
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    @extend_schema(
        description="Update progress values",
        request=DiplomaProgressUpdateSerializer,
        responses={200: DiplomaProgressSerializer},
        tags=["diplomas"]
    )
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update progress values"""
        progress = self.get_object()
        serializer = DiplomaProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update progress fields directly
        updates = serializer.validated_data['progress_updates']
        for field, value in updates.items():
            if hasattr(progress, field):
                setattr(progress, field, value)
        
        progress.calculate_progress()
        progress.save()
        
        return Response(DiplomaProgressSerializer(progress).data)


@extend_schema_view(
    list=extend_schema(description="List diploma verifications", tags=["diplomas"]),
    retrieve=extend_schema(description="Retrieve verification details", tags=["diplomas"]),
)
class DiplomaVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DiplomaVerification model (read-only)"""
    queryset = DiplomaVerification.objects.select_related('diploma', 'verified_by_user')
    serializer_class = DiplomaVerificationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['diploma', 'verification_method']

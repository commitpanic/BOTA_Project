"""
API views for activations app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiRequest
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models

from .models import ActivationKey, ActivationLog, License
from .serializers import (
    ActivationKeySerializer, ActivationLogSerializer,
    LicenseSerializer, ActivationKeyUsageSerializer
)
from .log_import_service import LogImportService


@extend_schema_view(
    list=extend_schema(description="List activation keys", tags=["activations"]),
    retrieve=extend_schema(description="Retrieve key details", tags=["activations"]),
    create=extend_schema(description="Create new activation key", tags=["activations"]),
    update=extend_schema(description="Update activation key", tags=["activations"]),
    destroy=extend_schema(description="Delete activation key", tags=["activations"]),
)
class ActivationKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for ActivationKey model"""
    queryset = ActivationKey.objects.select_related('bunker', 'assigned_to')
    serializer_class = ActivationKeySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bunker', 'is_active']
    
    def get_queryset(self):
        """Filter keys based on user permissions"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Non-staff can only see their assigned keys or unassigned active keys
            queryset = queryset.filter(
                models.Q(assigned_to=self.request.user) | 
                models.Q(assigned_to__isnull=True, is_active=True)
            )
        return queryset
    
    def perform_create(self, serializer):
        """Generate key and set created_by"""
        key = ActivationKey.generate_key()
        serializer.save(key=key, created_by=self.request.user)
    
    @extend_schema(
        description="Use an activation key to log activation",
        request=ActivationKeyUsageSerializer,
        responses={200: ActivationLogSerializer},
        tags=["activations"]
    )
    @action(detail=False, methods=['post'])
    def use_key(self, request):
        """Use an activation key"""
        serializer = ActivationKeyUsageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        key_value = serializer.validated_data['key']
        try:
            key = ActivationKey.objects.get(key=key_value)
        except ActivationKey.DoesNotExist:
            return Response(
                {'error': 'Invalid activation key'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if key can be used
        if not key.can_be_used_by(request.user):
            return Response(
                {'error': 'You cannot use this key'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create activation log
        activation_log = ActivationLog.objects.create(
            user=request.user,
            bunker=key.bunker,
            activation_key=key,
            activation_date=timezone.now(),
            is_b2b=serializer.validated_data.get('is_b2b', False),
            notes=serializer.validated_data.get('notes', '')
        )
        
        # Increment key usage
        key.use_key()
        
        return Response(
            ActivationLogSerializer(activation_log).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(description="List activation logs", tags=["activations"]),
    retrieve=extend_schema(description="Retrieve log details", tags=["activations"]),
    create=extend_schema(description="Create activation log", tags=["activations"]),
    update=extend_schema(description="Update activation log", tags=["activations"]),
    destroy=extend_schema(description="Delete activation log", tags=["activations"]),
)
class ActivationLogViewSet(viewsets.ModelViewSet):
    """ViewSet for ActivationLog model"""
    queryset = ActivationLog.objects.select_related('user', 'activator', 'bunker', 'activation_key')
    serializer_class = ActivationLogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'bunker', 'is_b2b', 'verified']
    
    def get_queryset(self):
        """Filter logs based on user permissions"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Non-staff can only see their own logs
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description="Upload ADIF log file (.adi format) for activation",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'ADIF log file (.adi)'
                    }
                }
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'qsos_processed': {'type': 'integer'},
                    'hunters_updated': {'type': 'integer'},
                    'b2b_qsos': {'type': 'integer'},
                    'bunker': {'type': 'string'},
                    'activator': {'type': 'string'},
                    'warnings': {'type': 'array', 'items': {'type': 'string'}},
                    'errors': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        tags=["activations"]
    )
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_adif(self, request):
        """
        Upload ADIF (.adi) log file for activation.
        
        The file should contain QSO records with:
        - MY_SIG_INFO: Bunker reference (e.g., B/SP-0039)
        - OPERATOR or STATION_CALLSIGN: Activator callsign
        - CALL: Hunter callsigns
        - QSO_DATE, TIME_ON: Date/time of contacts
        
        The system will:
        1. Parse the ADIF file
        2. Validate bunker reference and activator
        3. Create activation logs for each QSO
        4. Award hunter points (1 point per QSO, 2x for B2B)
        5. Award activator points
        6. Update user statistics
        """
        # Check for uploaded file
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file uploaded. Please upload an .adi file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file extension
        if not uploaded_file.name.endswith('.adi'):
            return Response(
                {'error': 'Invalid file format. Please upload a .adi (ADIF) file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': 'Invalid file encoding. File must be UTF-8 encoded.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process the log
        service = LogImportService()
        result = service.process_adif_upload(file_content, request.user)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description="List licenses", tags=["activations"]),
    retrieve=extend_schema(description="Retrieve license details", tags=["activations"]),
    create=extend_schema(description="Issue new license", tags=["activations"]),
    update=extend_schema(description="Update license", tags=["activations"]),
    destroy=extend_schema(description="Revoke license", tags=["activations"]),
)
class LicenseViewSet(viewsets.ModelViewSet):
    """ViewSet for License model"""
    queryset = License.objects.select_related('issued_to', 'issued_by')
    serializer_class = LicenseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['issued_to', 'license_type', 'is_active']
    
    def get_queryset(self):
        """Filter licenses based on user permissions"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Non-staff can only see their own licenses
            queryset = queryset.filter(issued_to=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        """Set issued_by to current user"""
        serializer.save(issued_by=self.request.user)

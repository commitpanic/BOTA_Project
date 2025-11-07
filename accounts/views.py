"""
API views for accounts app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend

from .models import UserStatistics, UserRole, UserRoleAssignment, PointsTransaction, PointsTransactionBatch
from .serializers import (
    UserSerializer, UserStatisticsSerializer, UserRoleSerializer,
    UserRoleAssignmentSerializer, UserRegistrationSerializer,
    UserProfileSerializer, PointsTransactionSerializer, PointsTransactionBatchSerializer
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(description="List all users", tags=["accounts"]),
    retrieve=extend_schema(description="Retrieve user details", tags=["accounts"]),
    create=extend_schema(description="Create new user", tags=["accounts"]),
    update=extend_schema(description="Update user", tags=["accounts"]),
    partial_update=extend_schema(description="Partially update user", tags=["accounts"]),
    destroy=extend_schema(description="Delete user", tags=["accounts"]),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['callsign', 'email']
    ordering_fields = ['date_joined', 'callsign']
    
    def get_queryset(self):
        """Filter queryset based on permissions"""
        queryset = User.objects.select_related('statistics')
        if not self.request.user.is_staff:
            # Non-staff can only see active users
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @extend_schema(
        description="Get current user profile",
        tags=["accounts"],
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        description="Register new user",
        request=UserRegistrationSerializer,
        responses={201: UserSerializer},
        tags=["accounts"]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(description="List user statistics", tags=["accounts"]),
    retrieve=extend_schema(description="Retrieve user statistics", tags=["accounts"]),
    update=extend_schema(description="Update user statistics", tags=["accounts"]),
    partial_update=extend_schema(description="Partially update user statistics", tags=["accounts"]),
)
class UserStatisticsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserStatistics model.
    Provides statistics management.
    """
    queryset = UserStatistics.objects.all()
    serializer_class = UserStatisticsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    ordering_fields = ['hunter_points', 'activator_points', 'b2b_points', 'last_updated']
    
    @extend_schema(
        description="Get leaderboard by total points",
        tags=["accounts"],
        parameters=[
            OpenApiParameter(name='limit', description='Number of results', type=int)
        ]
    )
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get top users by total points"""
        limit = int(request.query_params.get('limit', 10))
        stats = UserStatistics.objects.select_related('user').order_by(
            '-hunter_points', '-activator_points', '-b2b_points'
        )[:limit]
        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Recalculate user points from transaction history (authoritative source)",
        tags=["accounts"],
        responses={200: UserStatisticsSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def recalculate(self, request, pk=None):
        """Recalculate user statistics from PointsTransaction records"""
        stats = self.get_object()
        stats.recalculate_from_transactions()
        serializer = self.get_serializer(stats)
        return Response({
            'message': f'Points recalculated for user {stats.user.callsign}',
            'statistics': serializer.data
        })


@extend_schema_view(
    list=extend_schema(description="List user roles", tags=["accounts"]),
    retrieve=extend_schema(description="Retrieve role details", tags=["accounts"]),
    create=extend_schema(description="Create new role", tags=["accounts"]),
    update=extend_schema(description="Update role", tags=["accounts"]),
    partial_update=extend_schema(description="Partially update role", tags=["accounts"]),
    destroy=extend_schema(description="Delete role", tags=["accounts"]),
)
class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserRole model.
    Provides role management.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['name', 'description']


@extend_schema_view(
    list=extend_schema(description="List role assignments", tags=["accounts"]),
    retrieve=extend_schema(description="Retrieve assignment details", tags=["accounts"]),
    create=extend_schema(description="Assign role to user", tags=["accounts"]),
    update=extend_schema(description="Update role assignment", tags=["accounts"]),
    destroy=extend_schema(description="Remove role assignment", tags=["accounts"]),
)
class UserRoleAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserRoleAssignment model.
    Provides role assignment management.
    """
    queryset = UserRoleAssignment.objects.all()
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'role', 'is_active']


@extend_schema_view(
    list=extend_schema(description="List points transactions", tags=["points"]),
    retrieve=extend_schema(description="Retrieve transaction details", tags=["points"]),
)
class PointsTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for PointsTransaction model - READ ONLY.
    Transactions are immutable and created only via PointsService.
    """
    queryset = PointsTransaction.objects.select_related(
        'user', 'bunker', 'diploma', 'activation_log', 'created_by'
    ).order_by('-created_at')
    serializer_class = PointsTransactionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'transaction_type', 'is_reversed', 'bunker', 'diploma']
    ordering_fields = ['created_at', 'total_points']
    
    def get_queryset(self):
        """Filter by user if requested"""
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    @extend_schema(
        description="Get points transaction history for a specific user",
        tags=["points"],
        parameters=[
            OpenApiParameter(name='transaction_type', description='Filter by transaction type', type=str),
            OpenApiParameter(name='limit', description='Number of results', type=int)
        ]
    )
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)/history')
    def user_history(self, request, user_id=None):
        """Get transaction history for specific user"""
        from django.db.models import Sum
        
        transactions = PointsTransaction.objects.filter(
            user_id=user_id, is_reversed=False
        ).select_related('bunker', 'diploma', 'activation_log')
        
        # Filter by transaction type if provided
        trans_type = request.query_params.get('transaction_type')
        if trans_type:
            transactions = transactions.filter(transaction_type=trans_type)
        
        # Limit results
        limit = int(request.query_params.get('limit', 50))
        transactions = transactions.order_by('-created_at')[:limit]
        
        # Calculate totals
        aggregates = PointsTransaction.objects.filter(
            user_id=user_id, is_reversed=False
        ).aggregate(
            activator_points=Sum('activator_points'),
            hunter_points=Sum('hunter_points'),
            b2b_points=Sum('b2b_points'),
            event_points=Sum('event_points'),
            diploma_points=Sum('diploma_points')
        )
        
        # Calculate total from sum of all categories
        total_pts = sum(v or 0 for v in aggregates.values())
        aggregates['total_points'] = total_pts
        
        return Response({
            'user_id': int(user_id),
            'total_transactions': transactions.count(),
            'totals': aggregates,
            'transactions': self.get_serializer(transactions, many=True).data
        })


@extend_schema_view(
    list=extend_schema(description="List transaction batches", tags=["points"]),
    retrieve=extend_schema(description="Retrieve batch details", tags=["points"]),
)
class PointsTransactionBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for PointsTransactionBatch model - READ ONLY.
    Batches group related transactions (e.g., from log upload).
    """
    queryset = PointsTransactionBatch.objects.select_related(
        'log_upload', 'created_by'
    ).prefetch_related('transactions').order_by('-created_at')
    serializer_class = PointsTransactionBatchSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['log_upload', 'created_by']
    ordering_fields = ['created_at']

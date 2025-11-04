"""
API views for accounts app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend

from .models import UserStatistics, UserRole, UserRoleAssignment
from .serializers import (
    UserSerializer, UserStatisticsSerializer, UserRoleSerializer,
    UserRoleAssignmentSerializer, UserRegistrationSerializer,
    UserProfileSerializer
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

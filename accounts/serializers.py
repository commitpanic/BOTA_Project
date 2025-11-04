"""
Serializers for accounts app.
Handles user authentication, statistics, and role management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserStatistics, UserRole, UserRoleAssignment

User = get_user_model()


class UserStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for UserStatistics model"""
    total_points = serializers.ReadOnlyField()
    
    class Meta:
        model = UserStatistics
        fields = [
            'id', 'user', 
            'total_activator_qso', 'unique_activations', 'activator_b2b_qso',
            'total_hunter_qso', 'unique_bunkers_hunted',
            'total_b2b_qso', 'total_points', 'hunter_points', 
            'activator_points', 'b2b_points', 'event_points', 'diploma_points',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'last_updated', 'total_points']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description', 'permissions', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for UserRoleAssignment model"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_callsign = serializers.CharField(source='assigned_by.callsign', read_only=True)
    
    class Meta:
        model = UserRoleAssignment
        fields = [
            'id', 'user', 'role', 'role_name', 
            'assigned_by', 'assigned_by_callsign',
            'assigned_at', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    statistics = UserStatisticsSerializer(read_only=True)
    role_assignments = UserRoleAssignmentSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'callsign',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',
            'statistics', 'role_assignments', 
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'email': {'required': True},
            'callsign': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password match if provided"""
        if 'password' in attrs or 'password_confirm' in attrs:
            if attrs.get('password') != attrs.get('password_confirm'):
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'callsign', 'password', 'password_confirm']
    
    def validate(self, attrs):
        """Validate password match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            callsign=validated_data['callsign'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Simplified serializer for user profile display"""
    statistics = UserStatisticsSerializer(read_only=True)
    total_diplomas = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'callsign',
            'date_joined', 'statistics', 'total_diplomas'
        ]
        read_only_fields = ['id', 'email', 'callsign', 'date_joined']
    
    def get_total_diplomas(self, obj):
        """Get total number of diplomas earned"""
        return obj.diplomas.count()

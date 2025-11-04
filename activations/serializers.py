"""
Serializers for activations app.
Handles activation keys, logs, and licenses.
"""
import datetime
from rest_framework import serializers
from .models import ActivationKey, ActivationLog, License


class LicenseSerializer(serializers.ModelSerializer):
    """Serializer for License model"""
    issued_to_callsign = serializers.CharField(source='issued_to.callsign', read_only=True)
    
    class Meta:
        model = License
        fields = [
            'id', 'license_number', 'license_type',
            'title_pl', 'title_en', 'description_pl', 'description_en',
            'issued_to', 'issued_to_callsign',
            'valid_from', 'valid_until', 'is_active',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ActivationLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivationLog model"""
    user_callsign = serializers.CharField(source='user.callsign', read_only=True)
    bunker_reference = serializers.CharField(source='bunker.reference_number', read_only=True)
    activator_callsign = serializers.CharField(source='activator.callsign', read_only=True, allow_null=True)
    activation_key_value = serializers.CharField(source='activation_key.key', read_only=True, allow_null=True)
    activation_date_utc = serializers.SerializerMethodField()
    end_date_utc = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivationLog
        fields = [
            'id', 'user', 'user_callsign',
            'bunker', 'bunker_reference',
            'activator', 'activator_callsign',
            'activation_key', 'activation_key_value',
            'activation_date', 'activation_date_utc',
            'end_date', 'end_date_utc',
            'qso_count', 'is_b2b', 'mode', 'band',
            'notes', 'verified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_activation_date_utc(self, obj):
        """Format activation date with UTC suffix for UI display"""
        if obj.activation_date:
            # Convert to UTC if not already
            utc_time = obj.activation_date.astimezone(datetime.timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M UTC')
        return None
    
    def get_end_date_utc(self, obj):
        """Format end date with UTC suffix for UI display"""
        if obj.end_date:
            utc_time = obj.end_date.astimezone(datetime.timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M UTC')
        return None


class ActivationKeySerializer(serializers.ModelSerializer):
    """Serializer for ActivationKey model"""
    bunker_reference = serializers.CharField(source='bunker.reference_number', read_only=True)
    assigned_to_callsign = serializers.CharField(source='assigned_to.callsign', read_only=True, allow_null=True)
    activation_logs = ActivationLogSerializer(many=True, read_only=True)
    is_valid = serializers.SerializerMethodField()
    can_use = serializers.SerializerMethodField()
    valid_from_utc = serializers.SerializerMethodField()
    valid_until_utc = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivationKey
        fields = [
            'id', 'key', 'bunker', 'bunker_reference',
            'assigned_to', 'assigned_to_callsign',
            'valid_from', 'valid_from_utc',
            'valid_until', 'valid_until_utc',
            'max_uses', 'times_used', 'is_active',
            'notes', 'activation_logs',
            'is_valid', 'can_use', 'created_at'
        ]
        read_only_fields = ['id', 'key', 'created_at', 'times_used']
    
    def get_is_valid(self, obj):
        """Check if key is currently valid"""
        return obj.is_valid_now()
    
    def get_can_use(self, obj):
        """Check if key can be used by request user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_used_by(request.user)
        return False
    
    def get_valid_from_utc(self, obj):
        """Format valid_from with UTC suffix"""
        if obj.valid_from:
            utc_time = obj.valid_from.astimezone(datetime.timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M UTC')
        return None
    
    def get_valid_until_utc(self, obj):
        """Format valid_until with UTC suffix"""
        if obj.valid_until:
            utc_time = obj.valid_until.astimezone(datetime.timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M UTC')
        return None


class ActivationKeyUsageSerializer(serializers.Serializer):
    """Serializer for using an activation key"""
    key = serializers.CharField(required=True)
    bunker_reference = serializers.CharField(required=False)
    is_b2b = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate activation key usage"""
        return attrs

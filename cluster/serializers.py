"""
Serializers for cluster app.
Handles cluster grouping, members, alerts, and spotting.
"""
from rest_framework import serializers
from .models import Cluster, ClusterMember, ClusterAlert, Spot
from django.utils import timezone
from datetime import timedelta


class ClusterAlertSerializer(serializers.ModelSerializer):
    """Serializer for ClusterAlert model"""
    
    class Meta:
        model = ClusterAlert
        fields = [
            'id', 'cluster', 'alert_type', 'title_pl', 'title_en', 
            'message_pl', 'message_en',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClusterMemberSerializer(serializers.ModelSerializer):
    """Serializer for ClusterMember model"""
    bunker_reference = serializers.CharField(source='bunker.reference_number', read_only=True)
    bunker_name_en = serializers.CharField(source='bunker.name_en', read_only=True)
    
    class Meta:
        model = ClusterMember
        fields = [
            'id', 'cluster', 'bunker', 'bunker_reference', 'bunker_name_en',
            'display_order', 'notes', 'join_date'
        ]
        read_only_fields = ['id', 'join_date']


class ClusterSerializer(serializers.ModelSerializer):
    """Serializer for Cluster model"""
    members = ClusterMemberSerializer(many=True, read_only=True)
    alerts = ClusterAlertSerializer(many=True, read_only=True)
    bunker_count = serializers.SerializerMethodField()
    active_bunker_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cluster
        fields = [
            'id', 'name_pl', 'name_en', 'description_pl', 'description_en',
            'region', 'is_active', 'created_at', 'updated_at',
            'members', 'alerts', 'bunker_count', 'active_bunker_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bunker_count(self, obj):
        """Get total bunker count"""
        return obj.get_bunker_count()
    
    def get_active_bunker_count(self, obj):
        """Get active bunker count"""
        return obj.get_active_bunkers().count()
    
    def get_is_currently_active(self, obj):
        """Check if cluster is currently active"""
        return obj.is_currently_active()


class ClusterListSerializer(serializers.ModelSerializer):
    """Simplified serializer for cluster list views"""
    bunker_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cluster
        fields = [
            'id', 'name_en', 'name_pl', 'region',
            'is_active', 'bunker_count'
        ]
    
    def get_bunker_count(self, obj):
        """Get total bunker count"""
        return obj.get_bunker_count()


class SpotSerializer(serializers.ModelSerializer):
    """Serializer for Spot model (spotting system)"""
    spotter_callsign = serializers.CharField(source='spotter.callsign', read_only=True)
    time_since_update = serializers.SerializerMethodField()
    bunker_name = serializers.CharField(source='bunker.name_en', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Spot
        fields = [
            'id', 'activator_callsign', 'spotter', 'spotter_callsign',
            'frequency', 'band', 'bunker_reference', 'bunker', 'bunker_name',
            'comment', 'created_at', 'updated_at', 'expires_at',
            'is_active', 'time_since_update', 'is_expired', 'respot_count'
        ]
        read_only_fields = ['id', 'spotter', 'band', 'bunker', 'created_at', 'updated_at', 'expires_at', 'is_active', 'respot_count']
    
    def get_time_since_update(self, obj):
        """Get human-readable time since last update"""
        return obj.time_since_update()
    
    def get_is_expired(self, obj):
        """Check if spot has expired"""
        return obj.is_expired()
    
    def validate_activator_callsign(self, value):
        """Validate activator callsign format"""
        import re
        if not re.match(r'^[A-Z0-9]{3,10}$', value.upper()):
            raise serializers.ValidationError(
                "Callsign must be 3-10 alphanumeric characters (uppercase)"
            )
        return value.upper()
    
    def validate_frequency(self, value):
        """Validate frequency is in amateur radio bands"""
        from .models import detect_band_from_frequency
        band = detect_band_from_frequency(value)
        if not band:
            raise serializers.ValidationError(
                "Frequency must be within amateur radio bands (1.8-450 MHz)"
            )
        return value
    
    def validate_bunker_reference(self, value):
        """Validate bunker reference format (optional)"""
        if not value:
            return value
        import re
        if not re.match(r'^B/[A-Z]{2}-[0-9]{4}$', value.upper()):
            raise serializers.ValidationError(
                "Bunker reference must be in format: B/SP-0039"
            )
        return value.upper()
    
    def create(self, validated_data):
        """
        Create or update spot if similar one exists.
        If spot exists with same activator + similar frequency + bunker, refresh it instead.
        """
        activator = validated_data['activator_callsign']
        frequency = validated_data['frequency']
        bunker_ref = validated_data.get('bunker_reference', '')
        
        # Check for existing active spot (within 0.01 MHz of frequency)
        from decimal import Decimal
        freq_tolerance = Decimal('0.01')
        existing_spot = Spot.objects.filter(
            activator_callsign=activator,
            frequency__gte=frequency - freq_tolerance,
            frequency__lte=frequency + freq_tolerance,
            bunker_reference=bunker_ref,
            is_active=True
        ).first()
        
        if existing_spot:
            # Update existing spot
            existing_spot.frequency = frequency
            existing_spot.comment = validated_data.get('comment', '')
            existing_spot.spotter = validated_data['spotter']
            existing_spot.refresh_expiration()
            return existing_spot
        else:
            # Create new spot
            validated_data['expires_at'] = timezone.now() + timedelta(minutes=30)
            return super().create(validated_data)

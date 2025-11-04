"""
Serializers for cluster app.
Handles cluster grouping, members, and alerts.
"""
from rest_framework import serializers
from .models import Cluster, ClusterMember, ClusterAlert


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

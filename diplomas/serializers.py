"""
Serializers for diplomas app.
Handles diploma types, issued diplomas, progress tracking, and verification.
"""
from rest_framework import serializers
from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification


class DiplomaTypeSerializer(serializers.ModelSerializer):
    """Serializer for DiplomaType model"""
    total_issued = serializers.SerializerMethodField()
    is_time_limited = serializers.SerializerMethodField()
    is_currently_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = DiplomaType
        fields = [
            'id', 'name_pl', 'name_en', 'description_pl', 'description_en',
            'category',
            # Point requirements
            'min_activator_points', 'min_hunter_points', 'min_b2b_points',
            # Bunker count requirements
            'min_unique_activations', 'min_total_activations',
            'min_unique_hunted', 'min_total_hunted',
            # Time limitation
            'valid_from', 'valid_to', 'is_time_limited', 'is_currently_valid',
            # Display
            'template_image', 'is_active', 'display_order',
            'total_issued', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_time_limited', 'is_currently_valid']
    
    def get_total_issued(self, obj):
        """Get total diplomas issued of this type"""
        return obj.get_total_issued()
    
    def get_is_time_limited(self, obj):
        """Check if diploma is time-limited"""
        return obj.is_time_limited()
    
    def get_is_currently_valid(self, obj):
        """Check if time-limited diploma is currently valid"""
        return obj.is_currently_valid()


class DiplomaVerificationSerializer(serializers.ModelSerializer):
    """Serializer for DiplomaVerification model"""
    diploma_number = serializers.CharField(source='diploma.diploma_number', read_only=True)
    user_callsign = serializers.CharField(source='diploma.user.callsign', read_only=True)
    
    class Meta:
        model = DiplomaVerification
        fields = [
            'id', 'diploma', 'diploma_number', 'user_callsign',
            'verified_at', 'verified_by_ip', 'verified_by_user',
            'verification_method', 'notes'
        ]
        read_only_fields = ['id', 'verified_at']


class DiplomaSerializer(serializers.ModelSerializer):
    """Serializer for Diploma model"""
    diploma_type_name_en = serializers.CharField(source='diploma_type.name_en', read_only=True)
    diploma_type_name_pl = serializers.CharField(source='diploma_type.name_pl', read_only=True)
    user_callsign = serializers.CharField(source='user.callsign', read_only=True)
    issued_by_callsign = serializers.CharField(source='issued_by.callsign', read_only=True)
    verifications = DiplomaVerificationSerializer(many=True, read_only=True)
    verification_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Diploma
        fields = [
            'id', 'diploma_type', 'diploma_type_name_en', 'diploma_type_name_pl',
            'user', 'user_callsign',
            'issue_date', 'diploma_number', 'verification_code',
            'pdf_file',
            # Points at issuance
            'activator_points_earned', 'hunter_points_earned', 'b2b_points_earned',
            # Administration
            'issued_by', 'issued_by_callsign', 'notes',
            'verifications', 'verification_count'
        ]
        read_only_fields = ['id', 'issue_date', 'diploma_number', 'verification_code']
    
    def get_verification_count(self, obj):
        """Get total verification count"""
        return obj.verifications.count()


class DiplomaListSerializer(serializers.ModelSerializer):
    """Simplified serializer for diploma list views"""
    diploma_type_name_en = serializers.CharField(source='diploma_type.name_en', read_only=True)
    user_callsign = serializers.CharField(source='user.callsign', read_only=True)
    category = serializers.CharField(source='diploma_type.category', read_only=True)
    
    class Meta:
        model = Diploma
        fields = [
            'id', 'diploma_number', 'diploma_type_name_en',
            'user_callsign', 'category', 'issue_date'
        ]


class DiplomaProgressSerializer(serializers.ModelSerializer):
    """Serializer for DiplomaProgress model"""
    diploma_type_name_en = serializers.CharField(source='diploma_type.name_en', read_only=True)
    diploma_type_name_pl = serializers.CharField(source='diploma_type.name_pl', read_only=True)
    user_callsign = serializers.CharField(source='user.callsign', read_only=True)
    requirements = serializers.SerializerMethodField()
    current_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = DiplomaProgress
        fields = [
            'id', 'user', 'user_callsign',
            'diploma_type', 'diploma_type_name_en', 'diploma_type_name_pl',
            # Point progress
            'activator_points', 'hunter_points', 'b2b_points',
            # Bunker count progress
            'unique_activations', 'total_activations',
            'unique_hunted', 'total_hunted',
            # Completion status
            'percentage_complete', 'is_eligible',
            'current_progress', 'requirements', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated', 'current_progress', 'requirements']
    
    def get_requirements(self, obj):
        """Get requirements from diploma type"""
        dt = obj.diploma_type
        requirements = {}
        
        # Add point requirements
        if dt.min_activator_points > 0:
            requirements['min_activator_points'] = dt.min_activator_points
        if dt.min_hunter_points > 0:
            requirements['min_hunter_points'] = dt.min_hunter_points
        if dt.min_b2b_points > 0:
            requirements['min_b2b_points'] = dt.min_b2b_points
        
        # Add bunker count requirements
        if dt.min_unique_activations > 0:
            requirements['min_unique_activations'] = dt.min_unique_activations
        if dt.min_total_activations > 0:
            requirements['min_total_activations'] = dt.min_total_activations
        if dt.min_unique_hunted > 0:
            requirements['min_unique_hunted'] = dt.min_unique_hunted
        if dt.min_total_hunted > 0:
            requirements['min_total_hunted'] = dt.min_total_hunted
        
        return requirements
    
    def get_current_progress(self, obj):
        """Get current progress values"""
        progress = {}
        
        # Add point progress
        if obj.diploma_type.min_activator_points > 0:
            progress['activator_points'] = obj.activator_points
        if obj.diploma_type.min_hunter_points > 0:
            progress['hunter_points'] = obj.hunter_points
        if obj.diploma_type.min_b2b_points > 0:
            progress['b2b_points'] = obj.b2b_points
        
        # Add bunker count progress
        if obj.diploma_type.min_unique_activations > 0:
            progress['unique_activations'] = obj.unique_activations
        if obj.diploma_type.min_total_activations > 0:
            progress['total_activations'] = obj.total_activations
        if obj.diploma_type.min_unique_hunted > 0:
            progress['unique_hunted'] = obj.unique_hunted
        if obj.diploma_type.min_total_hunted > 0:
            progress['total_hunted'] = obj.total_hunted
        
        return progress


class DiplomaVerifySerializer(serializers.Serializer):
    """Serializer for diploma verification"""
    diploma_number = serializers.CharField(required=False)
    verification_code = serializers.UUIDField(required=False)
    
    def validate(self, attrs):
        """Validate that either diploma_number or verification_code is provided"""
        if not attrs.get('diploma_number') and not attrs.get('verification_code'):
            raise serializers.ValidationError(
                "Either diploma_number or verification_code must be provided."
            )
        return attrs


class DiplomaProgressUpdateSerializer(serializers.Serializer):
    """Serializer for updating diploma progress"""
    progress_updates = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        help_text="Dictionary of progress key-value pairs to update"
    )
    
    def validate_progress_updates(self, value):
        """Validate progress updates"""
        if not value:
            raise serializers.ValidationError("Progress updates cannot be empty.")
        return value

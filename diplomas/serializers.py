"""
Serializers for diplomas app.
Handles diploma types, issued diplomas, progress tracking, and verification.
"""
from rest_framework import serializers
from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification


class DiplomaTypeSerializer(serializers.ModelSerializer):
    """Serializer for DiplomaType model"""
    total_issued = serializers.SerializerMethodField()
    
    class Meta:
        model = DiplomaType
        fields = [
            'id', 'name_pl', 'name_en', 'description_pl', 'description_en',
            'category', 'requirements', 'points_awarded',
            'template_image', 'is_active', 'display_order',
            'total_issued', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_issued(self, obj):
        """Get total diplomas issued of this type"""
        return obj.get_total_issued()


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
            'pdf_file', 'requirements_met',
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
    
    class Meta:
        model = DiplomaProgress
        fields = [
            'id', 'user', 'user_callsign',
            'diploma_type', 'diploma_type_name_en', 'diploma_type_name_pl',
            'current_progress', 'percentage_complete', 'is_eligible',
            'requirements', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']
    
    def get_requirements(self, obj):
        """Get requirements from diploma type"""
        return obj.diploma_type.requirements


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

"""
Serializers for bunkers app.
Handles bunker management, photos, resources, and inspections.
"""
from rest_framework import serializers
from .models import BunkerCategory, Bunker, BunkerPhoto, BunkerResource, BunkerInspection


class BunkerCategorySerializer(serializers.ModelSerializer):
    """Serializer for BunkerCategory model"""
    bunker_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BunkerCategory
        fields = [
            'id', 'name_pl', 'name_en', 'description_pl', 'description_en',
            'icon', 'display_order', 'bunker_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bunker_count(self, obj):
        """Get total number of bunkers in this category"""
        return obj.bunkers.count()


class BunkerPhotoSerializer(serializers.ModelSerializer):
    """Serializer for BunkerPhoto model"""
    uploaded_by_callsign = serializers.CharField(source='uploaded_by.callsign', read_only=True)
    approved_by_callsign = serializers.CharField(source='approved_by.callsign', read_only=True)
    
    class Meta:
        model = BunkerPhoto
        fields = [
            'id', 'bunker', 'photo', 'caption_pl', 'caption_en',
            'uploaded_by', 'uploaded_by_callsign', 
            'uploaded_at', 'approved_by', 'approved_by_callsign', 
            'approval_date', 'is_approved'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'approved_by', 'approval_date']


class BunkerResourceSerializer(serializers.ModelSerializer):
    """Serializer for BunkerResource model"""
    added_by_callsign = serializers.CharField(source='added_by.callsign', read_only=True)
    
    class Meta:
        model = BunkerResource
        fields = [
            'id', 'bunker', 'title_pl', 'title_en', 'url', 'resource_type',
            'added_by', 'added_by_callsign', 'created_at'
        ]
        read_only_fields = ['id', 'added_by', 'created_at']


class BunkerInspectionSerializer(serializers.ModelSerializer):
    """Serializer for BunkerInspection model"""
    user_callsign = serializers.CharField(source='user.callsign', read_only=True)
    
    class Meta:
        model = BunkerInspection
        fields = [
            'id', 'bunker', 'user', 'user_callsign',
            'inspection_date', 'notes', 'verified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BunkerSerializer(serializers.ModelSerializer):
    """Serializer for Bunker model"""
    category_name_en = serializers.CharField(source='category.name_en', read_only=True)
    category_name_pl = serializers.CharField(source='category.name_pl', read_only=True)
    photos = BunkerPhotoSerializer(many=True, read_only=True)
    resources = BunkerResourceSerializer(many=True, read_only=True)
    recent_inspections = serializers.SerializerMethodField()
    created_by_callsign = serializers.CharField(source='created_by.callsign', read_only=True)
    verified_by_callsign = serializers.CharField(source='verified_by.callsign', read_only=True)
    
    class Meta:
        model = Bunker
        fields = [
            'id', 'reference_number', 'name_pl', 'name_en', 
            'description_pl', 'description_en',
            'category', 'category_name_en', 'category_name_pl',
            'latitude', 'longitude',
            'is_verified', 'verified_by', 'verified_by_callsign', 'verification_date',
            'created_by', 'created_by_callsign', 'created_at', 'updated_at',
            'photos', 'resources', 'recent_inspections'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'verified_by', 'verification_date']
    
    def get_recent_inspections(self, obj):
        """Get 3 most recent inspections"""
        inspections = obj.inspections.all()[:3]
        return BunkerInspectionSerializer(inspections, many=True).data
    
    def validate(self, attrs):
        """Validate GPS coordinates"""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})
        
        return attrs


class BunkerListSerializer(serializers.ModelSerializer):
    """Simplified serializer for bunker list views"""
    category_name_en = serializers.CharField(source='category.name_en', read_only=True)
    primary_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Bunker
        fields = [
            'id', 'reference_number', 'name_en', 'name_pl',
            'category_name_en', 'latitude', 'longitude',
            'is_verified', 'primary_photo'
        ]
    
    def get_primary_photo(self, obj):
        """Get URL of first approved photo"""
        photo = obj.photos.filter(is_approved=True).first()
        if photo:
            request = self.context.get('request')
            if request and photo.photo:
                return request.build_absolute_uri(photo.photo.url)
        return None

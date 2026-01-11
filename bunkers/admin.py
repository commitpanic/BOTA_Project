from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    BunkerCategory,
    Bunker,
    BunkerPhoto,
    BunkerResource,
    BunkerInspection,
    BunkerRequest,
    BunkerCorrectionRequest
)


@admin.register(BunkerCategory)
class BunkerCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerCategory"""
    list_display = ['name_en', 'name_pl', 'icon', 'display_order', 'bunker_count']
    list_editable = ['display_order']
    search_fields = ['name_en', 'name_pl', 'description_en', 'description_pl']
    ordering = ['display_order', 'name_en']
    
    fieldsets = (
        ('English', {
            'fields': ('name_en', 'description_en')
        }),
        ('Polish', {
            'fields': ('name_pl', 'description_pl')
        }),
        ('Display', {
            'fields': ('icon', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def bunker_count(self, obj):
        """Display count of bunkers in this category"""
        count = obj.bunkers.count()
        return format_html('<strong>{}</strong> bunkers', count)
    bunker_count.short_description = 'Bunkers'


class BunkerPhotoInline(admin.TabularInline):
    """Inline for managing bunker photos"""
    model = BunkerPhoto
    extra = 0
    fields = ['photo', 'caption_en', 'caption_pl', 'is_approved', 'uploaded_by']
    readonly_fields = ['uploaded_by', 'uploaded_at']
    can_delete = True


class BunkerResourceInline(admin.TabularInline):
    """Inline for managing bunker resources"""
    model = BunkerResource
    extra = 0
    fields = ['title_en', 'url', 'resource_type', 'added_by']
    readonly_fields = ['added_by', 'created_at']


class BunkerInspectionInline(admin.TabularInline):
    """Inline for viewing bunker inspections"""
    model = BunkerInspection
    extra = 0
    fields = ['user', 'inspection_date', 'verified', 'notes']
    readonly_fields = ['user', 'inspection_date', 'created_at']
    can_delete = False


@admin.register(Bunker)
class BunkerAdmin(admin.ModelAdmin):
    """Admin configuration for Bunker"""
    list_display = [
        'reference_number',
        'name_en',
        'category',
        'coordinates_display',
        'verified_status',
        'photo_count',
        'inspection_count'
    ]
    list_filter = ['is_verified', 'category', 'created_at']
    search_fields = [
        'reference_number',
        'name_en',
        'name_pl',
        'description_en',
        'description_pl'
    ]
    ordering = ['reference_number']
    inlines = [BunkerPhotoInline, BunkerResourceInline, BunkerInspectionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reference_number', 'category')
        }),
        ('English Content', {
            'fields': ('name_en', 'description_en')
        }),
        ('Polish Content', {
            'fields': ('name_pl', 'description_pl')
        }),
        ('GPS Coordinates', {
            'fields': ('latitude', 'longitude'),
            'description': 'Enter coordinates in decimal format (e.g., 54.403844)'
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verification_date'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'verification_date']
    
    actions = ['mark_as_verified', 'mark_as_unverified']
    
    def coordinates_display(self, obj):
        """Display GPS coordinates as clickable Google Maps link"""
        lat, lon = obj.get_coordinates()
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        return format_html(
            '<a href="{}" target="_blank">{}, {}</a>',
            maps_url, f"{lat:.6f}", f"{lon:.6f}"
        )
    coordinates_display.short_description = 'GPS Coordinates'
    
    def verified_status(self, obj):
        """Display verification status with icon"""
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    verified_status.short_description = 'Status'
    
    def photo_count(self, obj):
        """Display count of photos"""
        count = obj.photos.count()
        approved = obj.photos.filter(is_approved=True).count()
        return format_html('{} ({} approved)', count, approved)
    photo_count.short_description = 'Photos'
    
    def inspection_count(self, obj):
        """Display count of inspections"""
        return obj.inspections.count()
    inspection_count.short_description = 'Inspections'
    
    def mark_as_verified(self, request, queryset):
        """Admin action to verify selected bunkers"""
        updated = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verification_date=timezone.now()
        )
        self.message_user(request, f'{updated} bunker(s) marked as verified.')
    mark_as_verified.short_description = 'Mark selected bunkers as verified'
    
    def mark_as_unverified(self, request, queryset):
        """Admin action to unverify selected bunkers"""
        updated = queryset.update(
            is_verified=False,
            verified_by=None,
            verification_date=None
        )
        self.message_user(request, f'{updated} bunker(s) marked as unverified.')
    mark_as_unverified.short_description = 'Mark selected bunkers as unverified'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on new bunkers"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BunkerPhoto)
class BunkerPhotoAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerPhoto"""
    list_display = [
        'photo_thumbnail',
        'bunker',
        'caption_en',
        'uploaded_by',
        'approval_status',
        'uploaded_at'
    ]
    list_filter = ['is_approved', 'uploaded_at', 'bunker__category']
    search_fields = ['bunker__reference_number', 'caption_en', 'caption_pl']
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Photo', {
            'fields': ('bunker', 'photo')
        }),
        ('Captions', {
            'fields': ('caption_en', 'caption_pl')
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approval_date')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['uploaded_by', 'uploaded_at', 'approved_by', 'approval_date']
    
    actions = ['approve_photos', 'reject_photos']
    
    def photo_thumbnail(self, obj):
        """Display small thumbnail of photo"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.photo.url if hasattr(obj.photo, 'url') else ''
            )
        return '-'
    photo_thumbnail.short_description = 'Thumbnail'
    
    def approval_status(self, obj):
        """Display approval status with icon"""
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    approval_status.short_description = 'Status'
    
    def approve_photos(self, request, queryset):
        """Admin action to approve selected photos"""
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approval_date=timezone.now()
        )
        self.message_user(request, f'{updated} photo(s) approved.')
    approve_photos.short_description = 'Approve selected photos'
    
    def reject_photos(self, request, queryset):
        """Admin action to reject selected photos"""
        updated = queryset.update(
            is_approved=False,
            approved_by=None,
            approval_date=None
        )
        self.message_user(request, f'{updated} photo(s) rejected.')
    reject_photos.short_description = 'Reject selected photos'


@admin.register(BunkerResource)
class BunkerResourceAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerResource"""
    list_display = ['title_en', 'bunker', 'resource_type', 'url_link', 'added_by', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['title_en', 'title_pl', 'bunker__reference_number', 'url']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Resource Information', {
            'fields': ('bunker', 'resource_type', 'url')
        }),
        ('Titles', {
            'fields': ('title_en', 'title_pl')
        }),
        ('Metadata', {
            'fields': ('added_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['added_by', 'created_at']
    
    def url_link(self, obj):
        """Display clickable URL"""
        return format_html('<a href="{}" target="_blank">View →</a>', obj.url)
    url_link.short_description = 'Link'


@admin.register(BunkerInspection)
class BunkerInspectionAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerInspection"""
    list_display = ['bunker', 'user', 'inspection_date', 'verified', 'created_at']
    list_filter = ['verified', 'inspection_date', 'bunker__category']
    search_fields = [
        'bunker__reference_number',
        'user__callsign',
        'user__email',
        'notes'
    ]
    ordering = ['-inspection_date']
    
    fieldsets = (
        ('Inspection Details', {
            'fields': ('bunker', 'user', 'inspection_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Verification', {
            'fields': ('verified',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    actions = ['verify_inspections', 'unverify_inspections']
    
    def verify_inspections(self, request, queryset):
        """Admin action to verify selected inspections"""
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} inspection(s) verified.')
    verify_inspections.short_description = 'Verify selected inspections'
    
    def unverify_inspections(self, request, queryset):
        """Admin action to unverify selected inspections"""
        updated = queryset.update(verified=False)
        self.message_user(request, f'{updated} inspection(s) unverified.')
    unverify_inspections.short_description = 'Unverify selected inspections'


@admin.register(BunkerRequest)
class BunkerRequestAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerRequest"""
    list_display = [
        'reference_number',
        'name',
        'requested_by',
        'status_display',
        'created_at',
        'reviewed_by'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'reference_number',
        'name',
        'bunker_type',
        'requested_by__callsign',
        'requested_by__email'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('reference_number', 'name', 'bunker_type')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'locator')
        }),
        ('Description', {
            'fields': ('description', 'additional_info', 'photo_url')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'bunker'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('requested_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['requested_by', 'created_at', 'updated_at']
    
    actions = ['approve_requests', 'reject_requests']
    
    def status_display(self, obj):
        """Display status with colored badge"""
        if obj.status == 'pending':
            return format_html('<span style="color: orange;">⏳ Pending</span>')
        elif obj.status == 'approved':
            return format_html('<span style="color: green;">✓ Approved</span>')
        elif obj.status == 'rejected':
            return format_html('<span style="color: red;">✗ Rejected</span>')
    status_display.short_description = 'Status'
    
    def approve_requests(self, request, queryset):
        """Admin action to approve bunker requests"""
        from bunkers.models import BunkerCategory
        
        default_category, _ = BunkerCategory.objects.get_or_create(
            name_en='WW2 Bunker',
            defaults={
                'name_pl': 'Bunkier z II WŚ',
                'description_en': 'World War 2 fortification',
                'description_pl': 'Fortyfikacja z czasów II Wojny Światowej',
            }
        )
        
        approved_count = 0
        for bunker_request in queryset.filter(status='pending'):
            try:
                bunker = Bunker.objects.create(
                    reference_number=bunker_request.reference_number,
                    name_en=bunker_request.name,
                    name_pl=bunker_request.name,
                    description_en=f"{bunker_request.bunker_type}. {bunker_request.description}",
                    description_pl=f"{bunker_request.bunker_type}. {bunker_request.description}",
                    category=default_category,
                    latitude=bunker_request.latitude,
                    longitude=bunker_request.longitude,
                    is_verified=True,
                    verified_by=request.user,
                    created_by=bunker_request.requested_by
                )
                
                bunker_request.status = 'approved'
                bunker_request.reviewed_by = request.user
                bunker_request.bunker = bunker
                bunker_request.save()
                approved_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error approving {bunker_request.reference_number}: {str(e)}',
                    level='error'
                )
        
        if approved_count > 0:
            self.message_user(request, f'{approved_count} request(s) approved and bunkers created.')
    approve_requests.short_description = 'Approve and create bunkers'
    
    def reject_requests(self, request, queryset):
        """Admin action to reject bunker requests"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            rejection_reason='Rejected by admin'
        )
        self.message_user(request, f'{updated} request(s) rejected.')
    reject_requests.short_description = 'Reject selected requests'


@admin.register(BunkerCorrectionRequest)
class BunkerCorrectionRequestAdmin(admin.ModelAdmin):
    """Admin configuration for BunkerCorrectionRequest"""
    list_display = [
        'id',
        'bunker_link',
        'requested_by',
        'status_badge',
        'created_at',
        'has_changes_display'
    ]
    list_filter = ['status', 'created_at', 'reviewed_at']
    search_fields = [
        'bunker__reference_number',
        'bunker__name_en',
        'bunker__name_pl',
        'requested_by__callsign',
        'correction_reason'
    ]
    readonly_fields = [
        'bunker',
        'requested_by',
        'created_at',
        'updated_at',
        'reviewed_by',
        'reviewed_at',
        'current_values_display'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Info', {
            'fields': (
                'bunker',
                'requested_by',
                'status',
                'created_at',
                'current_values_display'
            )
        }),
        ('Proposed Changes', {
            'fields': (
                'new_name_pl',
                'new_name_en',
                'new_description_pl',
                'new_description_en',
                'new_latitude',
                'new_longitude',
                'new_category',
            )
        }),
        ('Explanation', {
            'fields': (
                'correction_reason',
                'additional_info'
            )
        }),
        ('Review', {
            'fields': (
                'rejection_reason',
                'reviewed_by',
                'reviewed_at'
            )
        }),
    )
    
    actions = ['approve_corrections', 'reject_corrections']
    
    def bunker_link(self, obj):
        """Link to bunker detail page"""
        return format_html(
            '<a href="/admin/bunkers/bunker/{}/change/">{}</a>',
            obj.bunker.id,
            obj.bunker.reference_number
        )
    bunker_link.short_description = 'Bunker'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_changes_display(self, obj):
        """Show if correction has any changes"""
        return obj.has_changes()
    has_changes_display.short_description = 'Has Changes'
    has_changes_display.boolean = True
    
    def current_values_display(self, obj):
        """Display current bunker values for comparison"""
        bunker = obj.bunker
        html = f"""
        <table class="table table-sm">
            <tr><th>Field</th><th>Current Value</th></tr>
            <tr><td>Name (PL)</td><td>{bunker.name_pl}</td></tr>
            <tr><td>Name (EN)</td><td>{bunker.name_en}</td></tr>
            <tr><td>Category</td><td>{bunker.category.name_en}</td></tr>
            <tr><td>Coordinates</td><td>{bunker.latitude}, {bunker.longitude}</td></tr>
        </table>
        """
        return format_html(html)
    current_values_display.short_description = 'Current Values'
    
    def approve_corrections(self, request, queryset):
        """Admin action to approve correction requests and apply changes"""
        approved_count = 0
        
        for correction in queryset.filter(status='pending'):
            try:
                bunker = correction.bunker
                
                # Apply corrections
                if correction.new_name_pl:
                    bunker.name_pl = correction.new_name_pl
                if correction.new_name_en:
                    bunker.name_en = correction.new_name_en
                if correction.new_description_pl:
                    bunker.description_pl = correction.new_description_pl
                if correction.new_description_en:
                    bunker.description_en = correction.new_description_en
                if correction.new_latitude:
                    bunker.latitude = correction.new_latitude
                if correction.new_longitude:
                    bunker.longitude = correction.new_longitude
                if correction.new_category:
                    bunker.category = correction.new_category
                
                bunker.save()
                
                # Update correction request status
                correction.status = 'approved'
                correction.reviewed_by = request.user
                correction.reviewed_at = timezone.now()
                correction.save()
                
                approved_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error applying correction for {correction.bunker.reference_number}: {str(e)}',
                    level='error'
                )
        
        if approved_count > 0:
            self.message_user(request, f'{approved_count} correction(s) approved and applied.')
    approve_corrections.short_description = 'Approve and apply corrections'
    
    def reject_corrections(self, request, queryset):
        """Admin action to reject correction requests"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Rejected by admin'
        )
        self.message_user(request, f'{updated} correction(s) rejected.')
    reject_corrections.short_description = 'Reject selected corrections'

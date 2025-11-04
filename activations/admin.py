from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ActivationKey, ActivationLog, License


class ActivationLogInline(admin.TabularInline):
    """Inline for viewing activation logs under activation keys"""
    model = ActivationLog
    extra = 0
    fields = ['user', 'activation_date', 'qso_count', 'is_b2b', 'verified']
    readonly_fields = ['user', 'activation_date', 'qso_count', 'is_b2b', 'verified']
    can_delete = False


@admin.register(ActivationKey)
class ActivationKeyAdmin(admin.ModelAdmin):
    """Admin configuration for ActivationKey"""
    list_display = [
        'key',
        'bunker',
        'assigned_to',
        'validity_status',
        'usage_display',
        'is_active',
        'created_by'
    ]
    list_filter = ['is_active', 'valid_from', 'valid_until', 'bunker__category']
    search_fields = ['key', 'bunker__reference_number', 'bunker__name_en', 'notes']
    ordering = ['-created_at']
    autocomplete_fields = ['bunker', 'assigned_to']
    inlines = [ActivationLogInline]
    
    fieldsets = (
        ('Key Information', {
            'fields': ('key', 'bunker', 'assigned_to')
        }),
        ('Validity', {
            'fields': ('is_active', 'valid_from', 'valid_until')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'times_used'),
            'description': 'Leave max_uses blank for unlimited usage'
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['times_used', 'created_at', 'updated_at']
    
    actions = ['generate_new_keys', 'activate_keys', 'deactivate_keys', 'extend_validity']
    
    def validity_status(self, obj):
        """Display validity status with color coding"""
        if obj.is_valid_now():
            return format_html('<span style="color: green;">✓ Valid</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">✗ Inactive</span>')
        elif obj.valid_from > timezone.now():
            return format_html('<span style="color: orange;">⏰ Not Started</span>')
        elif obj.valid_until and obj.valid_until < timezone.now():
            return format_html('<span style="color: red;">✗ Expired</span>')
        elif obj.max_uses and obj.times_used >= obj.max_uses:
            return format_html('<span style="color: red;">✗ Used Up</span>')
        return format_html('<span style="color: gray;">?</span>')
    validity_status.short_description = 'Status'
    
    def usage_display(self, obj):
        """Display usage statistics"""
        if obj.max_uses:
            return format_html('{} / {} uses', obj.times_used, obj.max_uses)
        return format_html('{} uses', obj.times_used)
    usage_display.short_description = 'Usage'
    
    def generate_new_keys(self, request, queryset):
        """Admin action to generate new keys for selected bunkers"""
        from .models import ActivationKey
        count = 0
        for key_obj in queryset:
            new_key = ActivationKey.generate_key()
            ActivationKey.objects.create(
                key=new_key,
                bunker=key_obj.bunker,
                valid_from=timezone.now(),
                is_active=True,
                created_by=request.user
            )
            count += 1
        self.message_user(request, f'{count} new key(s) generated.')
    generate_new_keys.short_description = 'Generate new keys for selected bunkers'
    
    def activate_keys(self, request, queryset):
        """Admin action to activate selected keys"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} key(s) activated.')
    activate_keys.short_description = 'Activate selected keys'
    
    def deactivate_keys(self, request, queryset):
        """Admin action to deactivate selected keys"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} key(s) deactivated.')
    deactivate_keys.short_description = 'Deactivate selected keys'
    
    def extend_validity(self, request, queryset):
        """Admin action to extend validity by 30 days"""
        from datetime import timedelta
        count = 0
        for key in queryset:
            if key.valid_until:
                key.valid_until = key.valid_until + timedelta(days=30)
            else:
                key.valid_until = timezone.now() + timedelta(days=30)
            key.save()
            count += 1
        self.message_user(request, f'{count} key(s) extended by 30 days.')
    extend_validity.short_description = 'Extend validity by 30 days'
    
    def save_model(self, request, obj, form, change):
        """Auto-generate key if not provided and set created_by"""
        if not change:  # New object
            if not obj.key:
                obj.key = ActivationKey.generate_key()
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ActivationLog)
class ActivationLogAdmin(admin.ModelAdmin):
    """Admin configuration for ActivationLog"""
    list_display = [
        'user',
        'bunker',
        'activation_date',
        'duration_display',
        'qso_count',
        'b2b_status',
        'verification_status'
    ]
    list_filter = ['verified', 'is_b2b', 'activation_date', 'bunker__category']
    search_fields = [
        'user__callsign',
        'user__email',
        'bunker__reference_number',
        'bunker__name_en',
        'notes'
    ]
    ordering = ['-activation_date']
    autocomplete_fields = ['bunker', 'user', 'activation_key']
    
    fieldsets = (
        ('Activation Details', {
            'fields': ('user', 'bunker', 'activation_key')
        }),
        ('Date & Time', {
            'fields': ('activation_date', 'end_date')
        }),
        ('Statistics', {
            'fields': ('qso_count', 'is_b2b')
        }),
        ('Verification', {
            'fields': ('verified', 'verified_by')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['verify_activations', 'unverify_activations']
    
    def duration_display(self, obj):
        """Display activation duration"""
        hours = obj.get_duration_hours()
        if hours is not None:
            return format_html('{:.1f} hours', hours)
        return '-'
    duration_display.short_description = 'Duration'
    
    def b2b_status(self, obj):
        """Display B2B status"""
        if obj.is_b2b:
            return format_html('<span style="color: purple;">★ B2B</span>')
        return '-'
    b2b_status.short_description = 'B2B'
    
    def verification_status(self, obj):
        """Display verification status"""
        if obj.verified:
            verifier = f" by {obj.verified_by.callsign}" if obj.verified_by else ""
            return format_html('<span style="color: green;">✓ Verified{}</span>', verifier)
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    verification_status.short_description = 'Verification'
    
    def verify_activations(self, request, queryset):
        """Admin action to verify selected activations"""
        updated = queryset.update(verified=True, verified_by=request.user)
        self.message_user(request, f'{updated} activation(s) verified.')
    verify_activations.short_description = 'Verify selected activations'
    
    def unverify_activations(self, request, queryset):
        """Admin action to unverify selected activations"""
        updated = queryset.update(verified=False, verified_by=None)
        self.message_user(request, f'{updated} activation(s) unverified.')
    unverify_activations.short_description = 'Unverify selected activations'


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """Admin configuration for License"""
    list_display = [
        'license_number',
        'license_type_display',
        'title_en',
        'issued_to',
        'validity_status',
        'date_range_display',
        'bunker_restriction'
    ]
    list_filter = ['license_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = [
        'license_number',
        'title_en',
        'title_pl',
        'issued_to__callsign',
        'issued_to__email'
    ]
    ordering = ['-valid_from']
    filter_horizontal = ['bunkers']
    autocomplete_fields = ['issued_to', 'issued_by']
    
    fieldsets = (
        ('License Information', {
            'fields': ('license_number', 'license_type', 'is_active')
        }),
        ('English Content', {
            'fields': ('title_en', 'description_en')
        }),
        ('Polish Content', {
            'fields': ('title_pl', 'description_pl')
        }),
        ('Assignment', {
            'fields': ('issued_to', 'bunkers'),
            'description': 'Leave bunkers blank to authorize all bunkers'
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('issued_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_licenses', 'deactivate_licenses', 'extend_licenses']
    
    def license_type_display(self, obj):
        """Display license type with color coding"""
        colors = {
            'contest': 'blue',
            'special_event': 'purple',
            'temporary': 'orange',
            'training': 'green',
            'other': 'gray'
        }
        color = colors.get(obj.license_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_license_type_display()
        )
    license_type_display.short_description = 'Type'
    
    def validity_status(self, obj):
        """Display validity status"""
        if obj.is_valid_now():
            return format_html('<span style="color: green;">✓ Valid</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">✗ Inactive</span>')
        elif obj.valid_from > timezone.now():
            return format_html('<span style="color: orange;">⏰ Not Started</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    validity_status.short_description = 'Status'
    
    def date_range_display(self, obj):
        """Display validity date range"""
        start = obj.valid_from.strftime('%Y-%m-%d')
        end = obj.valid_until.strftime('%Y-%m-%d')
        return format_html('{}<br>to<br>{}', start, end)
    date_range_display.short_description = 'Valid Period'
    
    def bunker_restriction(self, obj):
        """Display bunker restrictions"""
        count = obj.bunkers.count()
        if count == 0:
            return format_html('<span style="color: green;">All Bunkers</span>')
        return format_html('<strong>{}</strong> bunker(s)', count)
    bunker_restriction.short_description = 'Bunker Access'
    
    def activate_licenses(self, request, queryset):
        """Admin action to activate selected licenses"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} license(s) activated.')
    activate_licenses.short_description = 'Activate selected licenses'
    
    def deactivate_licenses(self, request, queryset):
        """Admin action to deactivate selected licenses"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} license(s) deactivated.')
    deactivate_licenses.short_description = 'Deactivate selected licenses'
    
    def extend_licenses(self, request, queryset):
        """Admin action to extend licenses by 30 days"""
        from datetime import timedelta
        count = 0
        for license in queryset:
            license.valid_until = license.valid_until + timedelta(days=30)
            license.save()
            count += 1
        self.message_user(request, f'{count} license(s) extended by 30 days.')
    extend_licenses.short_description = 'Extend validity by 30 days'
    
    def save_model(self, request, obj, form, change):
        """Auto-set issued_by on new licenses"""
        if not change:  # New object
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)

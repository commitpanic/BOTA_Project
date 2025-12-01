from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ActivationLog


# ActivationKey and License admin disabled in V2 - models not actively used


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
    autocomplete_fields = ['bunker', 'user']
    
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

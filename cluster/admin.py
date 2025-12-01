from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Cluster, Spot, SpotHistory
# Unused in V2: ClusterMember, ClusterAlert


# ClusterMember and ClusterAlert admin disabled in V2 - models not actively used
# class ClusterMemberInline(admin.TabularInline):
#     """Inline for managing cluster members (bunkers in cluster)"""
#     model = ClusterMember
#     extra = 1
#     fields = ['bunker', 'display_order', 'notes', 'added_by', 'join_date']
#     readonly_fields = ['added_by', 'join_date']
#     autocomplete_fields = ['bunker']
#
# class ClusterAlertInline(admin.TabularInline):
#     """Inline for managing cluster alerts"""
#     model = ClusterAlert
#     extra = 0
#     fields = ['title_en', 'alert_type', 'is_active', 'start_date', 'end_date']
#     readonly_fields = ['created_at']


# Cluster admin disabled in V2 - model not actively used
# @admin.register(Cluster)
# class ClusterAdmin(admin.ModelAdmin):
#     """Admin configuration for Cluster - DISABLED IN V2"""
#     pass


# @admin.register(ClusterMember)
# class ClusterMemberAdmin(admin.ModelAdmin):
#     """Admin configuration for ClusterMember - DISABLED IN V2"""
#     pass
#
# @admin.register(ClusterAlert)
# class ClusterAlertAdmin(admin.ModelAdmin):
#     """Admin configuration for ClusterAlert - DISABLED IN V2"""
#     pass


class SpotHistoryInline(admin.TabularInline):
    """Inline for viewing spot history"""
    model = SpotHistory
    extra = 0
    fields = ['respotter', 'respotted_at', 'comment']
    readonly_fields = ['respotter', 'respotted_at']
    can_delete = False


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    """Admin configuration for Spot (Spotting System)"""
    list_display = [
        'activator_callsign',
        'frequency_display',
        'bunker_display',
        'spotter',
        'time_display',
        'status_display',
        'created_at'
    ]
    list_filter = ['band', 'is_active', 'created_at', 'expires_at']
    search_fields = [
        'activator_callsign',
        'spotter__callsign',
        'bunker_reference',
        'comment'
    ]
    ordering = ['-updated_at']
    autocomplete_fields = ['bunker', 'spotter']
    inlines = [SpotHistoryInline]
    
    fieldsets = (
        ('Spot Information', {
            'fields': ('activator_callsign', 'frequency', 'band', 'bunker_reference', 'bunker')
        }),
        ('Additional Information', {
            'fields': ('comment', 'spotter')
        }),
        ('Status & Timing', {
            'fields': ('is_active', 'created_at', 'updated_at', 'expires_at')
        }),
    )
    readonly_fields = ['band', 'created_at', 'updated_at']
    
    actions = ['mark_inactive', 'refresh_spots', 'cleanup_expired']
    
    def frequency_display(self, obj):
        """Display frequency with band"""
        return format_html(
            '<strong>{} MHz</strong><br><span style="color: blue;">({})</span>',
            obj.frequency,
            obj.band if obj.band else 'Unknown'
        )
    frequency_display.short_description = 'Frequency/Band'
    
    def bunker_display(self, obj):
        """Display bunker reference or N/A"""
        if obj.bunker_reference:
            if obj.bunker:
                return format_html(
                    '<strong>{}</strong><br><small>{}</small>',
                    obj.bunker_reference,
                    obj.bunker.name_en
                )
            return obj.bunker_reference
        return format_html('<span style="color: gray;">N/A</span>')
    bunker_display.short_description = 'Bunker'
    
    def time_display(self, obj):
        """Display time since last update"""
        return format_html(
            '<span title="{}">{}</span>',
            obj.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.time_since_update()
        )
    time_display.short_description = 'Last Heard'
    
    def status_display(self, obj):
        """Display active status with expiration info"""
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        elif obj.is_active:
            mins_left = int((obj.expires_at - timezone.now()).total_seconds() / 60)
            return format_html(
                '<span style="color: green;">✓ Active</span><br><small>{} min left</small>',
                mins_left
            )
        return format_html('<span style="color: gray;">✗ Inactive</span>')
    status_display.short_description = 'Status'
    
    def mark_inactive(self, request, queryset):
        """Admin action to mark selected spots as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} spot(s) marked as inactive.')
    mark_inactive.short_description = 'Mark selected spots as inactive'
    
    def refresh_spots(self, request, queryset):
        """Admin action to refresh expiration time for selected spots"""
        count = 0
        for spot in queryset:
            spot.refresh_expiration()
            count += 1
        self.message_user(request, f'{count} spot(s) refreshed (extended by 30 minutes).')
    refresh_spots.short_description = 'Refresh selected spots (extend +30 min)'
    
    def cleanup_expired(self, request, queryset):
        """Admin action to mark expired spots as inactive"""
        expired_spots = queryset.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        count = expired_spots.update(is_active=False)
        self.message_user(request, f'{count} expired spot(s) marked as inactive.')
    cleanup_expired.short_description = 'Cleanup expired spots'


@admin.register(SpotHistory)
class SpotHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for SpotHistory"""
    list_display = [
        'spot',
        'respotter',
        'respotted_at',
        'comment'
    ]
    list_filter = ['respotted_at', 'respotter']
    search_fields = [
        'spot__activator_callsign',
        'respotter__callsign',
        'comment'
    ]
    ordering = ['-respotted_at']
    readonly_fields = ['respotted_at']

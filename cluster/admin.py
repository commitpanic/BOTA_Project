from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Cluster, ClusterMember, ClusterAlert


class ClusterMemberInline(admin.TabularInline):
    """Inline for managing cluster members (bunkers in cluster)"""
    model = ClusterMember
    extra = 1
    fields = ['bunker', 'display_order', 'notes', 'added_by', 'join_date']
    readonly_fields = ['added_by', 'join_date']
    autocomplete_fields = ['bunker']


class ClusterAlertInline(admin.TabularInline):
    """Inline for managing cluster alerts"""
    model = ClusterAlert
    extra = 0
    fields = ['title_en', 'alert_type', 'is_active', 'start_date', 'end_date']
    readonly_fields = ['created_at']


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    """Admin configuration for Cluster"""
    list_display = [
        'name_en',
        'name_pl',
        'region',
        'bunker_count_display',
        'active_status',
        'created_by',
        'created_at'
    ]
    list_filter = ['is_active', 'region', 'created_at']
    search_fields = ['name_en', 'name_pl', 'description_en', 'description_pl', 'region']
    ordering = ['region', 'name_en']
    inlines = [ClusterMemberInline, ClusterAlertInline]
    
    fieldsets = (
        ('English Content', {
            'fields': ('name_en', 'description_en')
        }),
        ('Polish Content', {
            'fields': ('name_pl', 'description_pl')
        }),
        ('Location & Status', {
            'fields': ('region', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_clusters', 'deactivate_clusters']
    
    def bunker_count_display(self, obj):
        """Display count of bunkers in cluster"""
        count = obj.get_bunker_count()
        active = obj.get_active_bunkers().count()
        return format_html('<strong>{}</strong> total ({} verified)', count, active)
    bunker_count_display.short_description = 'Bunkers'
    
    def active_status(self, obj):
        """Display active status with icon"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">✗ Inactive</span>')
    active_status.short_description = 'Status'
    
    def activate_clusters(self, request, queryset):
        """Admin action to activate selected clusters"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} cluster(s) activated.')
    activate_clusters.short_description = 'Activate selected clusters'
    
    def deactivate_clusters(self, request, queryset):
        """Admin action to deactivate selected clusters"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} cluster(s) deactivated.')
    deactivate_clusters.short_description = 'Deactivate selected clusters'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on new clusters"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClusterMember)
class ClusterMemberAdmin(admin.ModelAdmin):
    """Admin configuration for ClusterMember"""
    list_display = [
        'bunker',
        'cluster',
        'display_order',
        'added_by',
        'join_date'
    ]
    list_filter = ['cluster', 'join_date', 'bunker__category']
    search_fields = [
        'bunker__reference_number',
        'bunker__name_en',
        'bunker__name_pl',
        'cluster__name_en',
        'cluster__name_pl',
        'notes'
    ]
    ordering = ['cluster', 'display_order']
    autocomplete_fields = ['bunker', 'cluster']
    
    fieldsets = (
        ('Membership', {
            'fields': ('cluster', 'bunker', 'display_order')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('added_by', 'join_date'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['added_by', 'join_date']
    
    def save_model(self, request, obj, form, change):
        """Auto-set added_by on new memberships"""
        if not change:  # New object
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClusterAlert)
class ClusterAlertAdmin(admin.ModelAdmin):
    """Admin configuration for ClusterAlert"""
    list_display = [
        'title_en',
        'cluster',
        'alert_type_display',
        'status_display',
        'date_range_display',
        'created_by'
    ]
    list_filter = ['alert_type', 'is_active', 'start_date', 'cluster']
    search_fields = [
        'title_en',
        'title_pl',
        'message_en',
        'message_pl',
        'cluster__name_en',
        'cluster__name_pl'
    ]
    ordering = ['-start_date']
    autocomplete_fields = ['cluster']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('cluster', 'alert_type')
        }),
        ('English Content', {
            'fields': ('title_en', 'message_en')
        }),
        ('Polish Content', {
            'fields': ('title_pl', 'message_pl')
        }),
        ('Schedule', {
            'fields': ('is_active', 'start_date', 'end_date'),
            'description': 'Leave end_date blank for alerts without expiration'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_alerts', 'deactivate_alerts', 'extend_alerts']
    
    def alert_type_display(self, obj):
        """Display alert type with color coding"""
        colors = {
            'info': 'blue',
            'event': 'green',
            'warning': 'orange',
            'special': 'purple'
        }
        color = colors.get(obj.alert_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_alert_type_display()
        )
    alert_type_display.short_description = 'Type'
    
    def status_display(self, obj):
        """Display current status with icon"""
        if obj.is_currently_active():
            return format_html('<span style="color: green;">✓ Active Now</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">✗ Disabled</span>')
        elif obj.start_date > timezone.now():
            return format_html('<span style="color: orange;">⏰ Scheduled</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    status_display.short_description = 'Status'
    
    def date_range_display(self, obj):
        """Display date range"""
        start = obj.start_date.strftime('%Y-%m-%d %H:%M')
        if obj.end_date:
            end = obj.end_date.strftime('%Y-%m-%d %H:%M')
            return format_html('{}<br>to<br>{}', start, end)
        return format_html('{}<br>(no end date)', start)
    date_range_display.short_description = 'Date Range'
    
    def activate_alerts(self, request, queryset):
        """Admin action to activate selected alerts"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} alert(s) activated.')
    activate_alerts.short_description = 'Activate selected alerts'
    
    def deactivate_alerts(self, request, queryset):
        """Admin action to deactivate selected alerts"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} alert(s) deactivated.')
    deactivate_alerts.short_description = 'Deactivate selected alerts'
    
    def extend_alerts(self, request, queryset):
        """Admin action to extend alerts by 7 days"""
        from datetime import timedelta
        count = 0
        for alert in queryset:
            if alert.end_date:
                alert.end_date = alert.end_date + timedelta(days=7)
                alert.save()
                count += 1
        self.message_user(request, f'{count} alert(s) extended by 7 days.')
    extend_alerts.short_description = 'Extend selected alerts by 7 days'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on new alerts"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

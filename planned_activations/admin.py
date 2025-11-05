from django.contrib import admin
from .models import PlannedActivation


@admin.register(PlannedActivation)
class PlannedActivationAdmin(admin.ModelAdmin):
    list_display = ['callsign', 'bunker', 'planned_date', 'planned_time_start', 'user', 'created_at']
    list_filter = ['planned_date', 'created_at', 'bunker']
    search_fields = ['callsign', 'bunker__reference_number', 'bunker__name_pl', 'bunker__name_en', 'user__callsign', 'comments']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'planned_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'bunker', 'callsign')
        }),
        ('Date & Time', {
            'fields': ('planned_date', 'planned_time_start', 'planned_time_end')
        }),
        ('Operating Details', {
            'fields': ('bands', 'modes', 'comments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

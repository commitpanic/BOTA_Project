from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserStatistics, UserRole, UserRoleAssignment


class UserStatisticsInline(admin.StackedInline):
    """
    Inline admin for UserStatistics - shows statistics within User admin.
    """
    model = UserStatistics
    can_delete = False
    verbose_name_plural = 'Statistics'
    fields = (
        ('total_activator_qso', 'unique_activations', 'activator_b2b_qso'),
        ('total_hunter_qso', 'unique_bunkers_hunted'),
        ('total_b2b_qso',),
        ('total_points', 'hunter_points', 'activator_points'),
        ('b2b_points', 'event_points', 'diploma_points'),
    )
    readonly_fields = ('last_updated', 'created_at')


class UserRoleAssignmentInline(admin.TabularInline):
    """
    Inline admin for UserRoleAssignment - manage user roles within User admin.
    """
    model = UserRoleAssignment
    fk_name = 'user'  # Specify which ForeignKey to use
    extra = 1
    fields = ('role', 'is_active', 'assigned_at')
    readonly_fields = ('assigned_at',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with email authentication and callsign.
    """
    list_display = ('email', 'callsign', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'callsign')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('callsign',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'callsign', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    inlines = [UserStatisticsInline, UserRoleAssignmentInline]
    
    def get_inline_instances(self, request, obj=None):
        """Only show inlines when editing existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    """
    Admin interface for UserStatistics - view and manage user activity stats.
    """
    list_display = (
        'user',
        'total_points',
        'total_activator_qso',
        'total_hunter_qso',
        'total_b2b_qso',
        'last_updated'
    )
    list_filter = ('last_updated', 'created_at')
    search_fields = ('user__email', 'user__callsign')
    readonly_fields = ('last_updated', 'created_at')
    ordering = ('-total_points',)
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Activator Statistics'), {
            'fields': ('total_activator_qso', 'unique_activations', 'activator_b2b_qso'),
        }),
        (_('Hunter Statistics'), {
            'fields': ('total_hunter_qso', 'unique_bunkers_hunted'),
        }),
        (_('General Statistics'), {
            'fields': ('total_b2b_qso',),
        }),
        (_('Points System'), {
            'fields': (
                'total_points',
                'hunter_points',
                'activator_points',
                'b2b_points',
                'event_points',
                'diploma_points'
            ),
        }),
        (_('Timestamps'), {
            'fields': ('last_updated', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_total_points']
    
    def recalculate_total_points(self, request, queryset):
        """
        Admin action to recalculate total points for selected users.
        """
        count = 0
        for stats in queryset:
            stats.update_total_points()
            count += 1
        self.message_user(request, f'Successfully recalculated points for {count} users.')
    recalculate_total_points.short_description = 'Recalculate total points'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for UserRole - manage role definitions.
    """
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'permissions')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for UserRoleAssignment - manage role assignments.
    """
    list_display = ('user', 'role', 'is_active', 'assigned_by', 'assigned_at')
    list_filter = ('is_active', 'role', 'assigned_at')
    search_fields = ('user__email', 'user__callsign', 'role__name')
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'is_active')
        }),
        (_('Assignment Info'), {
            'fields': ('assigned_by', 'assigned_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Automatically set assigned_by to current user if not set.
        """
        if not change:  # Only for new assignments
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

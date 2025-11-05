from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserStatistics, UserRole, UserRoleAssignment

# Import SQL Console
from .sql_console_admin import SQLConsole


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
    Enhanced with auto_created field and custom actions.
    """
    list_display = ('callsign', 'email', 'auto_created_status', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('auto_created', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'callsign')
    ordering = ('-date_joined',)
    
    actions = ['deactivate_users', 'activate_users', 'mark_as_team_member', 'unmark_as_team_member']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('callsign', 'auto_created')
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
            'fields': ('email', 'callsign', 'password1', 'password2', 'auto_created'),
        }),
        (_('Permissions (Optional)'), {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    inlines = [UserStatisticsInline, UserRoleAssignmentInline]
    
    def get_inline_instances(self, request, obj=None):
        """Only show inlines when editing existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    def auto_created_status(self, obj):
        """Display auto-created status with badge"""
        from django.utils.html import format_html
        if obj.auto_created:
            return format_html('<span style="background-color: #ffc107; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 11px;">AUTO-CREATED</span>')
        return format_html('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">REGISTERED</span>')
    auto_created_status.short_description = _('Account Type')
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected user accounts"""
        count = queryset.update(is_active=False)
        self.message_user(request, _(f'{count} user(s) deactivated.'))
    deactivate_users.short_description = _('Deactivate selected users')
    
    def activate_users(self, request, queryset):
        """Activate selected user accounts"""
        count = queryset.update(is_active=True)
        self.message_user(request, _(f'{count} user(s) activated.'))
    activate_users.short_description = _('Activate selected users')
    
    def mark_as_team_member(self, request, queryset):
        """Mark selected users as team members (staff)"""
        count = queryset.update(is_staff=True)
        self.message_user(request, _(f'{count} user(s) marked as team members.'))
    mark_as_team_member.short_description = _('Mark as team member (staff)')
    
    def unmark_as_team_member(self, request, queryset):
        """Remove team member status from selected users"""
        count = queryset.update(is_staff=False)
        self.message_user(request, _(f'{count} user(s) unmarked as team members.'))
    unmark_as_team_member.short_description = _('Remove team member status')


# UserStatistics is managed via inline in UserAdmin - no need for separate admin
# Uncomment below if you want direct access to UserStatistics
# @admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    """
    Admin interface for UserStatistics - view and manage user activity stats.
    Hidden by default - managed via User inline.
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


# UserRoleAssignment is managed via inline in UserAdmin - no need for separate admin
# Uncomment below if you want direct access to UserRoleAssignment
# @admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for UserRoleAssignment - manage role assignments.
    Hidden by default - managed via User inline.
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

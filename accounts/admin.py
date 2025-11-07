from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    User, UserStatistics, UserRole, UserRoleAssignment,
    PointsTransaction, PointsTransactionBatch
)

# Import SQL Console
from .sql_console_admin import SQLConsole


class PointsTransactionInline(admin.TabularInline):
    """
    Inline admin for PointsTransaction - shows recent transactions within User admin.
    """
    model = PointsTransaction
    fk_name = 'user'
    extra = 0
    can_delete = False
    max_num = 10  # Show only last 10 transactions
    fields = (
        'created_at',
        'transaction_type',
        'total_points_display',
        'activation_log_link',
        'reason',
        'is_reversed'
    )
    readonly_fields = (
        'created_at',
        'transaction_type',
        'total_points_display',
        'activation_log_link',
        'reason',
        'is_reversed'
    )
    ordering = ('-created_at',)
    
    def total_points_display(self, obj):
        """Display total points with color coding"""
        if obj.total_points > 0:
            return format_html('<span style="color: green; font-weight: bold;">+{}</span>', obj.total_points)
        elif obj.total_points < 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.total_points)
        return obj.total_points
    total_points_display.short_description = _('Points')
    
    def activation_log_link(self, obj):
        """Link to related activation log"""
        if obj.activation_log:
            url = reverse('admin:activations_activationlog_change', args=[obj.activation_log.id])
            return format_html('<a href="{}">{}</a>', url, f'Log #{obj.activation_log.id}')
        return '-'
    activation_log_link.short_description = _('Related Log')
    
    def has_add_permission(self, request, obj=None):
        """Prevent manual creation of transactions"""
        return False


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
    
    actions = ['deactivate_users', 'activate_users', 'mark_as_team_member', 'unmark_as_team_member', 'promote_to_superuser', 'demote_from_superuser']
    
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
    inlines = [UserStatisticsInline, PointsTransactionInline, UserRoleAssignmentInline]
    
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
    
    def promote_to_superuser(self, request, queryset):
        """Promote selected users to superuser status"""
        count = queryset.update(is_superuser=True, is_staff=True)
        self.message_user(request, _(f'{count} user(s) promoted to superuser.'))
    promote_to_superuser.short_description = _('Promote to superuser')
    
    def demote_from_superuser(self, request, queryset):
        """Remove superuser status from selected users"""
        count = queryset.update(is_superuser=False)
        self.message_user(request, _(f'{count} user(s) demoted from superuser.'))
    demote_from_superuser.short_description = _('Remove superuser status')


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
    
    actions = ['recalculate_total_points', 'recalculate_from_transactions']
    
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
    
    def recalculate_from_transactions(self, request, queryset):
        """
        Admin action to rebuild statistics from PointsTransaction audit trail.
        This is the authoritative recalculation method.
        """
        count = 0
        for stats in queryset:
            stats.recalculate_from_transactions()
            count += 1
        self.message_user(
            request,
            f'Successfully recalculated {count} user(s) statistics from transaction history.',
            level='success'
        )
    recalculate_from_transactions.short_description = 'Rebuild from transaction history (authoritative)'


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


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for PointsTransaction - view audit trail of all point operations.
    Read-only to maintain integrity of the audit log.
    """
    list_display = (
        'id',
        'created_at',
        'user_link',
        'transaction_type',
        'points_breakdown',
        'total_points_colored',
        'activation_log_link',
        'batch_link',
        'is_reversed'
    )
    list_filter = (
        'transaction_type',
        'is_reversed',
        'created_at',
        'batch__log_upload'
    )
    search_fields = (
        'user__callsign',
        'user__email',
        'reason',
        'notes'
    )
    readonly_fields = (
        'id',
        'user',
        'transaction_type',
        'activator_points',
        'hunter_points',
        'b2b_points',
        'event_points',
        'diploma_points',
        'total_points',
        'activation_log',
        'bunker',
        'diploma',
        'batch',
        'reverses',
        'reversed_by',
        'reason',
        'notes',
        'created_by',
        'created_at',
        'is_reversed'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Transaction Info'), {
            'fields': (
                'id',
                'transaction_type',
                'user',
                'created_at',
                'created_by'
            )
        }),
        (_('Points Breakdown'), {
            'fields': (
                'activator_points',
                'hunter_points',
                'b2b_points',
                'event_points',
                'diploma_points',
                'total_points'
            )
        }),
        (_('Related Objects'), {
            'fields': (
                'activation_log',
                'bunker',
                'diploma',
                'batch'
            )
        }),
        (_('Reversal Info'), {
            'fields': (
                'is_reversed',
                'reverses',
                'reversed_by'
            ),
            'classes': ('collapse',)
        }),
        (_('Additional Info'), {
            'fields': (
                'reason',
                'notes'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reverse_selected_transactions']
    
    def has_add_permission(self, request):
        """Prevent manual creation - transactions must be created via PointsService"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - transactions are immutable audit trail"""
        return False
    
    def user_link(self, obj):
        """Link to user admin"""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.callsign)
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__callsign'
    
    def points_breakdown(self, obj):
        """Show points breakdown"""
        parts = []
        if obj.activator_points: parts.append(f'A:{obj.activator_points:+d}')
        if obj.hunter_points: parts.append(f'H:{obj.hunter_points:+d}')
        if obj.b2b_points: parts.append(f'B2B:{obj.b2b_points:+d}')
        if obj.event_points: parts.append(f'E:{obj.event_points:+d}')
        if obj.diploma_points: parts.append(f'D:{obj.diploma_points:+d}')
        return ' | '.join(parts) if parts else '-'
    points_breakdown.short_description = _('Breakdown')
    
    def total_points_colored(self, obj):
        """Display total points with color"""
        if obj.total_points > 0:
            return format_html(
                '<span style="color: green; font-weight: bold; font-size: 14px;">+{}</span>',
                obj.total_points
            )
        elif obj.total_points < 0:
            return format_html(
                '<span style="color: red; font-weight: bold; font-size: 14px;">{}</span>',
                obj.total_points
            )
        return '0'
    total_points_colored.short_description = _('Total')
    total_points_colored.admin_order_field = 'total_points'
    
    def activation_log_link(self, obj):
        """Link to activation log"""
        if obj.activation_log:
            url = reverse('admin:activations_activationlog_change', args=[obj.activation_log.id])
            return format_html('<a href="{}">Log #{}</a>', url, obj.activation_log.id)
        return '-'
    activation_log_link.short_description = _('QSO Log')
    
    def batch_link(self, obj):
        """Link to batch"""
        if obj.batch:
            url = reverse('admin:accounts_pointstransactionbatch_change', args=[obj.batch.id])
            return format_html('<a href="{}">Batch #{}</a>', url, obj.batch.id)
        return '-'
    batch_link.short_description = _('Batch')
    
    def reverse_selected_transactions(self, request, queryset):
        """Admin action to reverse selected transactions"""
        count = 0
        errors = []
        
        for transaction in queryset:
            if transaction.is_reversed:
                errors.append(f'Transaction #{transaction.id} is already reversed')
                continue
            
            try:
                transaction.reverse(
                    reason=f'Manual reversal by admin {request.user.callsign}',
                    created_by=request.user
                )
                count += 1
            except Exception as e:
                errors.append(f'Error reversing transaction #{transaction.id}: {str(e)}')
        
        if count:
            self.message_user(request, f'Successfully reversed {count} transaction(s).')
        
        if errors:
            self.message_user(request, 'Errors: ' + '; '.join(errors), level='error')
    
    reverse_selected_transactions.short_description = _('Reverse selected transactions')


@admin.register(PointsTransactionBatch)
class PointsTransactionBatchAdmin(admin.ModelAdmin):
    """
    Admin interface for PointsTransactionBatch - view and manage transaction batches.
    """
    list_display = (
        'id',
        'name',
        'created_at',
        'transaction_count_display',
        'total_points_display',
        'log_upload_link',
        'is_reversed'
    )
    list_filter = (
        'is_reversed',
        'created_at'
    )
    search_fields = (
        'name',
        'description',
        'log_upload__filename'
    )
    readonly_fields = (
        'name',
        'description',
        'log_upload',
        'created_by',
        'created_at',
        'is_reversed',
        'reversed_at',
        'transaction_count_display',
        'total_points_display'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Batch Info'), {
            'fields': (
                'name',
                'description',
                'created_by',
                'created_at'
            )
        }),
        (_('Statistics'), {
            'fields': (
                'transaction_count_display',
                'total_points_display'
            )
        }),
        (_('Related Objects'), {
            'fields': (
                'log_upload',
            )
        }),
        (_('Reversal Info'), {
            'fields': (
                'is_reversed',
                'reversed_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reverse_selected_batches']
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - batches are audit trail"""
        return False
    
    def transaction_count_display(self, obj):
        """Display transaction count"""
        count = obj.transactions.count()
        return format_html(
            '<a href="{}?batch__id__exact={}">{} transactions</a>',
            reverse('admin:accounts_pointstransaction_changelist'),
            obj.id,
            count
        )
    transaction_count_display.short_description = _('Transactions')
    
    def total_points_display(self, obj):
        """Calculate and display total points"""
        from django.db.models import Sum
        total = obj.transactions.aggregate(total=Sum('total_points'))['total'] or 0
        if total > 0:
            return format_html('<span style="color: green; font-weight: bold;">+{}</span>', total)
        elif total < 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', total)
        return '0'
    total_points_display.short_description = _('Total Points')
    
    def log_upload_link(self, obj):
        """Link to log upload"""
        if obj.log_upload:
            url = reverse('admin:activations_logupload_change', args=[obj.log_upload.id])
            return format_html('<a href="{}">{}</a>', url, obj.log_upload.filename)
        return '-'
    log_upload_link.short_description = _('Log Upload')
    
    def reverse_selected_batches(self, request, queryset):
        """Admin action to reverse entire batches"""
        count = 0
        errors = []
        
        for batch in queryset:
            if batch.is_reversed:
                errors.append(f'Batch #{batch.id} is already reversed')
                continue
            
            try:
                batch.reverse_all(
                    reason=f'Batch reversal by admin {request.user.callsign}',
                    created_by=request.user
                )
                count += 1
            except Exception as e:
                errors.append(f'Error reversing batch #{batch.id}: {str(e)}')
        
        if count:
            self.message_user(request, f'Successfully reversed {count} batch(es).')
        
        if errors:
            self.message_user(request, 'Errors: ' + '; '.join(errors), level='error')
    
    reverse_selected_batches.short_description = _('Reverse selected batches')

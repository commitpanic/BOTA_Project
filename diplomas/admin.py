from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import DiplomaType, Diploma, DiplomaProgress, DiplomaVerification, FontFile, DiplomaLayoutElement
from .forms import DiplomaLayoutElementForm
import json


@admin.register(FontFile)
class FontFileAdmin(admin.ModelAdmin):
    """Admin for FontFile model"""
    list_display = ['name', 'font_type', 'is_active', 'uploaded_at', 'preview_path']
    list_filter = ['font_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['uploaded_at', 'preview_path']
    
    fieldsets = (
        (_('Font Information'), {
            'fields': ('name', 'font_type', 'font_file')
        }),
        (_('Status'), {
            'fields': ('is_active', 'uploaded_at')
        }),
        (_('Preview'), {
            'fields': ('preview_path',)
        }),
    )
    
    def preview_path(self, obj):
        """Display font file path"""
        if obj.font_file:
            return format_html(
                '<code>{}</code><br><small>Use in config as: <strong>{}</strong></small>',
                obj.font_file.path if hasattr(obj.font_file, 'path') else obj.font_file.name,
                obj.get_font_family_name()
            )
        return "-"
    preview_path.short_description = _("Font Path & Usage")


class DiplomaLayoutElementInline(admin.TabularInline):
    """Inline admin for layout elements"""
    model = DiplomaLayoutElement
    form = DiplomaLayoutElementForm
    extra = 0
    fields = ('element_type', 'enabled', 'x_position', 'y_position', 'font_family', 'font_size', 'bold', 'italic', 'color', 'qr_size')
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        """Make element_type readonly for existing objects"""
        if obj:
            return ['element_type']
        return []
    
    class Media:
        css = {
            'all': ('admin/css/diploma_layout_inline.css',)
        }
        js = ('admin/js/diploma_layout_inline.js',)
    
    def get_formset(self, request, obj=None, **kwargs):
        """Ensure all element types are present"""
        formset = super().get_formset(request, obj, **kwargs)
        
        # If editing existing diploma type, create missing elements with defaults
        if obj and obj.pk:
            existing_types = set(obj.layout_elements.values_list('element_type', flat=True))
            all_types = [choice[0] for choice in DiplomaLayoutElement.ELEMENT_TYPES]
            
            for element_type in all_types:
                if element_type not in existing_types:
                    # Create default element
                    defaults = self._get_default_for_element(element_type)
                    DiplomaLayoutElement.objects.create(
                        diploma_type=obj,
                        element_type=element_type,
                        **defaults
                    )
        
        return formset
    
    def _get_default_for_element(self, element_type):
        """Get default values for each element type"""
        defaults = {
            'callsign': {'x_position': 14.5, 'y_position': 10, 'font_size': 24, 'bold': True},
            'diploma_name': {'x_position': 14.5, 'y_position': 12, 'font_size': 16, 'bold': False},
            'date': {'x_position': 14.5, 'y_position': 4, 'font_size': 10, 'bold': False},
            'points': {'x_position': 14.5, 'y_position': 8, 'font_size': 12, 'bold': False},
            'diploma_number': {'x_position': 14.5, 'y_position': 2, 'font_size': 10, 'bold': False},
            'qr_code': {'x_position': 26, 'y_position': 2, 'font_size': 10, 'bold': False, 'qr_size': 3.0},
        }
        return defaults.get(element_type, {'x_position': 14.5, 'y_position': 10, 'font_size': 12, 'bold': False})


class DiplomaInline(admin.TabularInline):
    """Inline admin for diplomas on DiplomaType page"""
    model = Diploma
    extra = 0
    fields = ('user', 'diploma_number', 'issue_date', 'verification_code')
    readonly_fields = ('diploma_number', 'issue_date', 'verification_code')
    can_delete = False


class ProgressInline(admin.TabularInline):
    """Inline admin for progress records on DiplomaType page"""
    model = DiplomaProgress
    extra = 0
    fields = ('user', 'percentage_complete', 'is_eligible', 'last_updated')
    readonly_fields = ('percentage_complete', 'last_updated')
    can_delete = False


@admin.register(DiplomaType)
class DiplomaTypeAdmin(admin.ModelAdmin):
    """Admin for DiplomaType model"""
    list_display = ['name_en', 'name_pl', 'category', 'requirements_summary', 'time_limited_badge', 'is_active', 'total_issued', 'preview_button']
    list_filter = ['category', 'is_active']
    search_fields = ['name_en', 'name_pl', 'description_en', 'description_pl']
    readonly_fields = ['created_at', 'updated_at', 'total_issued', 'preview_button', 'available_fonts']
    
    fieldsets = (
        (_('Names'), {
            'fields': ('name_pl', 'name_en')
        }),
        (_('Descriptions'), {
            'fields': ('description_pl', 'description_en')
        }),
        (_('Point Requirements'), {
            'fields': ('min_activator_points', 'min_hunter_points', 'min_b2b_points'),
            'description': _('Each QSO as activator = 1 activator point, each hunted QSO = 1 hunter point, each B2B QSO = 1 B2B point')
        }),
        (_('Bunker Count Requirements'), {
            'fields': (
                ('min_unique_activations', 'min_total_activations'),
                ('min_unique_hunted', 'min_total_hunted')
            ),
            'description': _('Set minimum bunker counts: unique = different bunkers, total = all activations/hunts (including repeats). Set to 0 for no requirement.'),
            'classes': ('collapse',)
        }),
        (_('Time Limitation (for Special Diplomas)'), {
            'fields': ('valid_from', 'valid_to'),
            'description': _('Leave empty for permanent diplomas. Set dates for time-limited/special event diplomas.'),
            'classes': ('collapse',)
        }),
        (_('PDF Template'), {
            'fields': ('template_image', 'available_fonts', 'preview_button'),
            'description': _('Upload a background image for the diploma PDF (optional). Use Layout Elements section below to configure text positioning and styling.')
        }),
        (_('Display Settings'), {
            'fields': ('category', 'is_active', 'display_order')
        }),
        (_('Statistics'), {
            'fields': ('total_issued', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DiplomaLayoutElementInline, ProgressInline, DiplomaInline]
    
    def get_urls(self):
        """Add custom URLs for preview"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:diploma_type_id>/preview/', 
                 self.admin_site.admin_view(self.preview_diploma),
                 name='diplomas_diplomatype_preview'),
        ]
        return custom_urls + urls
    
    def preview_button(self, obj):
        """Display preview button"""
        if obj.pk:
            url = reverse('admin:diplomas_diplomatype_preview', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #417690; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">Preview PDF</a>',
                url
            )
        return "-"
    preview_button.short_description = _("Preview")
    
    def available_fonts(self, obj):
        """Display available fonts"""
        fonts = FontFile.objects.filter(is_active=True).order_by('name', 'font_type')
        
        if not fonts.exists():
            return format_html(
                '<div style="background: #fff3cd; padding: 10px; border-radius: 5px;">'
                '<strong>No custom fonts uploaded.</strong><br>'
                'Default fonts available: <code>Lato</code>, <code>Lato-Bold</code>, <code>Helvetica</code>, <code>Helvetica-Bold</code>'
                '</div>'
            )
        
        font_html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
        font_html += '<strong>Uploaded Custom Fonts:</strong><br><br>'
        font_html += '<table style="width: 100%; border-collapse: collapse;">'
        font_html += '<tr style="background: #e9ecef;"><th style="padding: 8px; text-align: left;">Font Name</th><th style="padding: 8px; text-align: left;">Type</th><th style="padding: 8px; text-align: left;">Use in Config</th></tr>'
        
        for font in fonts:
            font_html += f'<tr style="border-bottom: 1px solid #dee2e6;">'
            font_html += f'<td style="padding: 8px;">{font.name}</td>'
            font_html += f'<td style="padding: 8px;">{font.get_font_type_display()}</td>'
            font_html += f'<td style="padding: 8px;"><code>"{font.get_font_family_name()}"</code></td>'
            font_html += '</tr>'
        
        font_html += '</table><br>'
        font_html += '<small>Built-in fonts: <code>Lato</code>, <code>Lato-Bold</code>, <code>Helvetica</code>, <code>Helvetica-Bold</code></small>'
        font_html += '</div>'
        
        return format_html(font_html)
    available_fonts.short_description = _("Available Fonts")
    
    def preview_diploma(self, request, diploma_type_id):
        """Generate preview PDF for diploma type using new PDF generator"""
        from datetime import date
        from .pdf_generator import generate_diploma_pdf
        
        diploma_type = get_object_or_404(DiplomaType, pk=diploma_type_id)
        
        # Sample data for preview
        callsign = "SP0AAA"
        diploma_name = f"{diploma_type.name_en} / {diploma_type.name_pl}"
        date_text = f"Issue Date: {date.today().strftime('%Y-%m-%d')}"
        points_text = "Points: ACT: 50 | HNT: 75 | B2B: 10"
        diploma_number = "PREVIEW-12345"
        verification_url = "https://bota.pl/verify/PREVIEW-12345"
        
        # Generate PDF
        buffer = generate_diploma_pdf(
            diploma_type=diploma_type,
            callsign=callsign,
            diploma_name=diploma_name,
            date_text=date_text,
            points_text=points_text,
            diploma_number=diploma_number,
            verification_url=verification_url,
            is_preview=True
        )
        
        # Return PDF response
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="preview_{diploma_type.name_en}.pdf"'
        return response
    
    def total_issued(self, obj):
        """Display total issued diplomas"""
        return obj.get_total_issued()
    total_issued.short_description = _("Total Issued")
    
    def requirements_summary(self, obj):
        """Display requirements summary"""
        parts = []
        # Points
        if obj.min_activator_points > 0:
            parts.append(f"ACT:{obj.min_activator_points}")
        if obj.min_hunter_points > 0:
            parts.append(f"HNT:{obj.min_hunter_points}")
        if obj.min_b2b_points > 0:
            parts.append(f"B2B:{obj.min_b2b_points}")
        # Bunker counts
        if obj.min_unique_activations > 0:
            parts.append(f"UA:{obj.min_unique_activations}")
        if obj.min_total_activations > 0:
            parts.append(f"TA:{obj.min_total_activations}")
        if obj.min_unique_hunted > 0:
            parts.append(f"UH:{obj.min_unique_hunted}")
        if obj.min_total_hunted > 0:
            parts.append(f"TH:{obj.min_total_hunted}")
        return " | ".join(parts) if parts else "-"
    requirements_summary.short_description = _("Requirements")
    
    def time_limited_badge(self, obj):
        """Display time limitation badge"""
        if not obj.is_time_limited():
            return format_html('<span style="color: #6c757d;">Permanent</span>')
        
        is_active = obj.is_currently_valid()
        color = '#28a745' if is_active else '#dc3545'
        status = 'Active' if is_active else 'Expired/Future'
        
        date_range = []
        if obj.valid_from:
            date_range.append(f"From: {obj.valid_from}")
        if obj.valid_to:
            date_range.append(f"To: {obj.valid_to}")
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span><br>'
            '<small style="color: #6c757d;">{}</small>',
            color, status, "<br>".join(date_range)
        )
    time_limited_badge.short_description = _("Time Limited")


class DiplomaVerificationInline(admin.TabularInline):
    """Inline admin for verifications on Diploma page"""
    model = DiplomaVerification
    extra = 0
    fields = ('verified_at', 'verified_by_ip', 'verified_by_user', 'verification_method')
    readonly_fields = ('verified_at', 'verified_by_ip', 'verified_by_user')
    can_delete = False


@admin.register(Diploma)
class DiplomaAdmin(admin.ModelAdmin):
    """Admin for Diploma model"""
    list_display = ['diploma_number', 'user_callsign', 'diploma_type_name', 'issue_date', 'verification_badge']
    list_filter = ['diploma_type__category', 'issue_date']
    search_fields = ['diploma_number', 'user__callsign', 'user__email', 'verification_code']
    readonly_fields = ['diploma_number', 'verification_code', 'issue_date', 'qr_code_display']
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        (_('Diploma Information'), {
            'fields': ('diploma_type', 'user', 'issue_date', 'diploma_number')
        }),
        (_('Points at Issuance'), {
            'fields': ('activator_points_earned', 'hunter_points_earned', 'b2b_points_earned')
        }),
        (_('Verification'), {
            'fields': ('verification_code', 'qr_code_display')
        }),
        (_('Files'), {
            'fields': ('pdf_file',)
        }),
        (_('Details'), {
            'fields': ('issued_by', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DiplomaVerificationInline]
    
    actions = ['generate_pdf']
    
    def user_callsign(self, obj):
        """Display user callsign"""
        return obj.user.callsign
    user_callsign.short_description = _("Callsign")
    user_callsign.admin_order_field = 'user__callsign'
    
    def diploma_type_name(self, obj):
        """Display diploma type name"""
        return obj.diploma_type.name_en
    diploma_type_name.short_description = _("Diploma Type")
    diploma_type_name.admin_order_field = 'diploma_type__name_en'
    
    def verification_badge(self, obj):
        """Display verification badge with count"""
        count = obj.verifications.count()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} verifications</span>',
            color, count
        )
    verification_badge.short_description = _("Verifications")
    
    def qr_code_display(self, obj):
        """Display QR code placeholder"""
        return format_html(
            '<div style="padding: 10px; background-color: #f0f0f0; border-radius: 5px;">'
            'QR Code: {}<br>'
            '<small>Verification URL: /diplomas/verify/{}/'
            '</div>',
            obj.verification_code, obj.verification_code
        )
    qr_code_display.short_description = _("QR Code")
    
    def generate_pdf(self, request, queryset):
        """Generate PDF diplomas (placeholder action)"""
        count = queryset.count()
        self.message_user(request, f"PDF generation for {count} diploma(s) would be triggered here.")
    generate_pdf.short_description = _("Generate PDF diplomas")


@admin.register(DiplomaProgress)
class DiplomaProgressAdmin(admin.ModelAdmin):
    """Admin for DiplomaProgress model"""
    list_display = ['user_callsign', 'diploma_type_name', 'points_display', 'progress_bar', 'is_eligible', 'last_updated']
    list_filter = ['diploma_type__category', 'is_eligible']
    search_fields = ['user__callsign', 'user__email', 'diploma_type__name_en']
    readonly_fields = ['last_updated', 'progress_bar_large']
    
    fieldsets = (
        (_('Progress Information'), {
            'fields': ('user', 'diploma_type', 'progress_bar_large')
        }),
        (_('Current Points'), {
            'fields': ('activator_points', 'hunter_points', 'b2b_points')
        }),
        (_('Current Bunker Counts'), {
            'fields': (
                ('unique_activations', 'total_activations'),
                ('unique_hunted', 'total_hunted')
            )
        }),
        (_('Progress Status'), {
            'fields': ('percentage_complete', 'is_eligible', 'last_updated')
        }),
    )
    
    actions = ['recalculate_progress', 'mark_eligible']
    
    def user_callsign(self, obj):
        """Display user callsign"""
        return obj.user.callsign
    user_callsign.short_description = _("Callsign")
    user_callsign.admin_order_field = 'user__callsign'
    
    def diploma_type_name(self, obj):
        """Display diploma type name"""
        return obj.diploma_type.name_en
    diploma_type_name.short_description = _("Diploma Type")
    diploma_type_name.admin_order_field = 'diploma_type__name_en'
    
    def points_display(self, obj):
        """Display current progress vs required"""
        dt = obj.diploma_type
        parts = []
        
        # Points
        if dt.min_activator_points > 0:
            color = '#28a745' if obj.activator_points >= dt.min_activator_points else '#dc3545'
            parts.append(f'<span style="color: {color};">ACT: {obj.activator_points}/{dt.min_activator_points}</span>')
        
        if dt.min_hunter_points > 0:
            color = '#28a745' if obj.hunter_points >= dt.min_hunter_points else '#dc3545'
            parts.append(f'<span style="color: {color};">HNT: {obj.hunter_points}/{dt.min_hunter_points}</span>')
        
        if dt.min_b2b_points > 0:
            color = '#28a745' if obj.b2b_points >= dt.min_b2b_points else '#dc3545'
            parts.append(f'<span style="color: {color};">B2B: {obj.b2b_points}/{dt.min_b2b_points}</span>')
        
        # Bunker counts
        if dt.min_unique_activations > 0:
            color = '#28a745' if obj.unique_activations >= dt.min_unique_activations else '#dc3545'
            parts.append(f'<span style="color: {color};">UA: {obj.unique_activations}/{dt.min_unique_activations}</span>')
        
        if dt.min_unique_hunted > 0:
            color = '#28a745' if obj.unique_hunted >= dt.min_unique_hunted else '#dc3545'
            parts.append(f'<span style="color: {color};">UH: {obj.unique_hunted}/{dt.min_unique_hunted}</span>')
        
        return format_html(' | '.join(parts)) if parts else '-'
    points_display.short_description = _("Progress")
    
    def progress_bar(self, obj):
        """Display progress bar"""
        percentage = float(obj.percentage_complete)
        color = '#28a745' if percentage >= 100 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<div style="width: 100px; height: 20px; background-color: #e9ecef; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background-color: {}; line-height: 20px; text-align: center; color: white; font-size: 11px;">'
            '{}%'
            '</div></div>',
            min(percentage, 100), color, int(percentage)
        )
    progress_bar.short_description = _("Progress")
    
    def progress_bar_large(self, obj):
        """Display large progress bar for detail view"""
        percentage = float(obj.percentage_complete)
        color = '#28a745' if percentage >= 100 else '#ffc107' if percentage >= 50 else '#dc3545'
        
        dt = obj.diploma_type
        requirements_html = '<ul>'
        
        # Points requirements
        if dt.min_activator_points > 0:
            met = '✓' if obj.activator_points >= dt.min_activator_points else '✗'
            requirements_html += f'<li>{met} Activator Points: {obj.activator_points} / {dt.min_activator_points}</li>'
        if dt.min_hunter_points > 0:
            met = '✓' if obj.hunter_points >= dt.min_hunter_points else '✗'
            requirements_html += f'<li>{met} Hunter Points: {obj.hunter_points} / {dt.min_hunter_points}</li>'
        if dt.min_b2b_points > 0:
            met = '✓' if obj.b2b_points >= dt.min_b2b_points else '✗'
            requirements_html += f'<li>{met} B2B Points: {obj.b2b_points} / {dt.min_b2b_points}</li>'
        
        # Bunker count requirements
        if dt.min_unique_activations > 0:
            met = '✓' if obj.unique_activations >= dt.min_unique_activations else '✗'
            requirements_html += f'<li>{met} Unique Activations: {obj.unique_activations} / {dt.min_unique_activations}</li>'
        if dt.min_total_activations > 0:
            met = '✓' if obj.total_activations >= dt.min_total_activations else '✗'
            requirements_html += f'<li>{met} Total Activations: {obj.total_activations} / {dt.min_total_activations}</li>'
        if dt.min_unique_hunted > 0:
            met = '✓' if obj.unique_hunted >= dt.min_unique_hunted else '✗'
            requirements_html += f'<li>{met} Unique Hunted: {obj.unique_hunted} / {dt.min_unique_hunted}</li>'
        if dt.min_total_hunted > 0:
            met = '✓' if obj.total_hunted >= dt.min_total_hunted else '✗'
            requirements_html += f'<li>{met} Total Hunted: {obj.total_hunted} / {dt.min_total_hunted}</li>'
        
        requirements_html += '</ul>'
        
        return format_html(
            '<div style="width: 100%; max-width: 500px; height: 30px; background-color: #e9ecef; border-radius: 5px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background-color: {}; line-height: 30px; text-align: center; color: white; font-weight: bold;">'
            '{}%'
            '</div></div>'
            '<div style="margin-top: 15px;"><strong>Requirements:</strong>{}</div>',
            min(percentage, 100), color, int(percentage),
            requirements_html
        )
    progress_bar_large.short_description = _("Progress Overview")
    
    def recalculate_progress(self, request, queryset):
        """Recalculate progress for selected records"""
        count = 0
        for progress in queryset:
            progress.calculate_progress()
            progress.save()
            count += 1
        self.message_user(request, f"Progress recalculated for {count} record(s).")
    recalculate_progress.short_description = _("Recalculate progress")
    
    def mark_eligible(self, request, queryset):
        """Mark selected records as eligible"""
        count = queryset.filter(percentage_complete__gte=100).update(is_eligible=True)
        self.message_user(request, f"Marked {count} record(s) as eligible.")
    mark_eligible.short_description = _("Mark as eligible (if 100%)")


@admin.register(DiplomaVerification)
class DiplomaVerificationAdmin(admin.ModelAdmin):
    """Admin for DiplomaVerification model"""
    list_display = ['diploma_number', 'user_callsign', 'verified_at', 'verification_method', 'verified_by_ip']
    list_filter = ['verification_method', 'verified_at']
    search_fields = ['diploma__diploma_number', 'diploma__user__callsign', 'verified_by_ip']
    readonly_fields = ['verified_at']
    date_hierarchy = 'verified_at'
    
    fieldsets = (
        (_('Verification Details'), {
            'fields': ('diploma', 'verified_at', 'verification_method')
        }),
        (_('Verifier Information'), {
            'fields': ('verified_by_ip', 'verified_by_user', 'notes')
        }),
    )
    
    def diploma_number(self, obj):
        """Display diploma number"""
        return obj.diploma.diploma_number
    diploma_number.short_description = _("Diploma Number")
    diploma_number.admin_order_field = 'diploma__diploma_number'
    
    def user_callsign(self, obj):
        """Display user callsign"""
        return obj.diploma.user.callsign
    user_callsign.short_description = _("Callsign")
    user_callsign.admin_order_field = 'diploma__user__callsign'

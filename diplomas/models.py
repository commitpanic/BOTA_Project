from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid
import os
import copy


class FontFile(models.Model):
    """
    Uploaded font files for diploma customization.
    Supports TTF and OTF formats.
    """
    FONT_TYPES = [
        ('regular', _('Regular')),
        ('bold', _('Bold')),
        ('italic', _('Italic')),
        ('bold_italic', _('Bold Italic')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Font Name"),
        help_text=_("Display name for this font (e.g., 'Arial', 'Times New Roman')")
    )
    font_file = models.FileField(
        upload_to='diploma_fonts/',
        validators=[FileExtensionValidator(allowed_extensions=['ttf', 'otf'])],
        verbose_name=_("Font File"),
        help_text=_("Upload TTF or OTF font file")
    )
    font_type = models.CharField(
        max_length=20,
        choices=FONT_TYPES,
        default='regular',
        verbose_name=_("Font Type"),
        help_text=_("Specify if this is regular, bold, italic, or bold-italic variant")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Only active fonts appear in diploma configuration")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At")
    )
    
    class Meta:
        verbose_name = _("Font File")
        verbose_name_plural = _("Font Files")
        ordering = ['name', 'font_type']
        unique_together = [['name', 'font_type']]
    
    def __str__(self):
        return f"{self.name} ({self.get_font_type_display()})"
    
    def get_font_family_name(self):
        """Return font family name for reportlab registration"""
        if self.font_type == 'regular':
            return self.name
        elif self.font_type == 'bold':
            return f"{self.name}-Bold"
        elif self.font_type == 'italic':
            return f"{self.name}-Italic"
        elif self.font_type == 'bold_italic':
            return f"{self.name}-BoldItalic"
        return self.name


class DiplomaLayoutElement(models.Model):
    """
    Individual text element configuration for diploma layout.
    Each diploma type has multiple elements (callsign, name, date, etc.)
    """
    ELEMENT_TYPES = [
        ('callsign', _('Callsign')),
        ('diploma_name', _('Diploma Name')),
        ('date', _('Issue Date')),
        ('points', _('Points Information')),
        ('diploma_number', _('Diploma Number')),
        ('qr_code', _('QR Code')),
    ]
    
    diploma_type = models.ForeignKey(
        'DiplomaType',
        on_delete=models.CASCADE,
        related_name='layout_elements',
        verbose_name=_("Diploma Type")
    )
    element_type = models.CharField(
        max_length=20,
        choices=ELEMENT_TYPES,
        verbose_name=_("Element Type")
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
        help_text=_("Show this element on the diploma")
    )
    x_position = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=14.5,
        verbose_name=_("X Position (cm)"),
        help_text=_("Horizontal position from left edge (center alignment)")
    )
    y_position = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        verbose_name=_("Y Position (cm)"),
        help_text=_("Vertical position from bottom edge")
    )
    font_family = models.CharField(
        max_length=100,
        default='Lato',
        verbose_name=_("Font Family"),
        help_text=_("Font name (e.g., Lato, Arial, Times)")
    )
    font_size = models.IntegerField(
        default=24,
        validators=[MinValueValidator(6)],
        verbose_name=_("Font Size"),
        help_text=_("Font size in points (minimum 6)")
    )
    bold = models.BooleanField(
        default=False,
        verbose_name=_("Bold")
    )
    italic = models.BooleanField(
        default=False,
        verbose_name=_("Italic")
    )
    color = models.CharField(
        max_length=7,
        default='#333333',
        verbose_name=_("Color"),
        help_text=_("Text color in hex format (e.g., #333333)")
    )
    
    # For QR code only
    qr_size = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.0,
        null=True,
        blank=True,
        verbose_name=_("QR Code Size (cm)"),
        help_text=_("Only for QR code element")
    )
    
    class Meta:
        verbose_name = _("Layout Element")
        verbose_name_plural = _("Layout Elements")
        ordering = ['element_type']
        unique_together = [['diploma_type', 'element_type']]
    
    def __str__(self):
        return f"{self.diploma_type.name_en} - {self.get_element_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to clear qr_size for non-QR elements"""
        # Only QR code should have qr_size value
        if self.element_type != 'qr_code':
            self.qr_size = None
        elif self.element_type == 'qr_code' and not self.qr_size:
            # Set default QR size if not provided
            self.qr_size = 3.0
        
        super().save(*args, **kwargs)


class DiplomaType(models.Model):
    """
    Types of diplomas that can be earned.
    Examples: Hunter Basic, Hunter Advanced, Activator Bronze, B2B Master, Special Event
    """
    DIPLOMA_CATEGORIES = [
        ('hunter', _('Hunter')),
        ('activator', _('Activator')),
        ('b2b', _('Bunker-to-Bunker')),
        ('special_event', _('Special Event')),
        ('cluster', _('Cluster Achievement')),
        ('other', _('Other')),
    ]

    name_pl = models.CharField(
        max_length=200,
        verbose_name=_("Name (Polish)")
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name=_("Name (English)")
    )
    description_pl = models.TextField(
        verbose_name=_("Description (Polish)")
    )
    description_en = models.TextField(
        verbose_name=_("Description (English)")
    )
    category = models.CharField(
        max_length=20,
        choices=DIPLOMA_CATEGORIES,
        default='other',
        verbose_name=_("Category")
    )
    
    # Point-based requirements
    min_activator_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Activator Points"),
        help_text=_("Each QSO as activator = 1 point")
    )
    min_hunter_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Hunter Points"),
        help_text=_("Each hunted QSO = 1 point")
    )
    min_b2b_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum B2B Points"),
        help_text=_("Each bunker-to-bunker QSO = 1 point")
    )
    
    # Unique bunker requirements (NEW)
    min_unique_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Unique Bunkers Activated"),
        help_text=_("Number of different bunkers activated")
    )
    min_total_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Total Activations"),
        help_text=_("Total number of bunker activations (can repeat same bunker)")
    )
    min_unique_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Unique Bunkers Hunted"),
        help_text=_("Number of different bunkers hunted")
    )
    min_total_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Total Hunted"),
        help_text=_("Total number of bunkers hunted (can repeat same bunker)")
    )
    
    # Date range for special/time-limited diplomas
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid From"),
        help_text=_("Start date for time-limited diploma (leave empty for permanent)")
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid To"),
        help_text=_("End date for time-limited diploma (leave empty for permanent)")
    )
    template_image = models.ImageField(
        upload_to='diploma_templates/',
        blank=True,
        verbose_name=_("Template Image"),
        help_text=_("Background template for PDF generation")
    )
    
    # PDF Layout Configuration - Enhanced with full text styling
    layout_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Layout Configuration"),
        help_text=_(
            "Advanced PDF layout configuration. Structure: "
            "{'callsign': {'enabled': true, 'x': 14.5, 'y': 10, 'font': 'Lato', 'size': 24, 'bold': true, 'italic': false, 'color': '#000000'}, ...} "
            "Available elements: callsign, diploma_name, date, points, diploma_number, qr_code"
        )
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Can this diploma be earned?")
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Diploma Type")
        verbose_name_plural = _("Diploma Types")
        ordering = ['category', 'display_order', 'name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_pl}"

    def get_total_issued(self):
        """Return count of diplomas issued of this type"""
        return self.diplomas.count()
    
    def is_time_limited(self):
        """Check if this is a time-limited diploma"""
        return self.valid_from is not None or self.valid_to is not None
    
    def is_currently_valid(self):
        """Check if diploma can be earned right now (for time-limited diplomas)"""
        if not self.is_time_limited():
            return True
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        
        return True
    
    def get_default_layout_config(self):
        """Return default layout configuration with all styling options"""
        return {
            'callsign': {
                'enabled': True,
                'x': 14.5,
                'y': 10,
                'font': 'Lato',
                'size': 24,
                'bold': True,
                'italic': False,
                'color': '#333333'
            },
            'diploma_name': {
                'enabled': True,
                'x': 14.5,
                'y': 12,
                'font': 'Lato',
                'size': 16,
                'bold': False,
                'italic': False,
                'color': '#333333'
            },
            'date': {
                'enabled': True,
                'x': 14.5,
                'y': 14,
                'font': 'Lato',
                'size': 12,
                'bold': False,
                'italic': False,
                'color': '#666666'
            },
            'points': {
                'enabled': True,
                'x': 14.5,
                'y': 16,
                'font': 'Lato',
                'size': 12,
                'bold': False,
                'italic': False,
                'color': '#666666'
            },
            'diploma_number': {
                'enabled': True,
                'x': 14.5,
                'y': 10.5,
                'font': 'Lato',
                'size': 10,
                'bold': False,
                'italic': False,
                'color': '#999999'
            },
            'qr_code': {
                'enabled': True,
                'x': 2,
                'y': 2,
                'size': 3  # QR code size in cm
            }
        }
    
    def migrate_old_layout_config(self):
        """Migrate old flat layout_config format to new nested format"""
        if not self.layout_config:
            return
        
        # Check if already in new format (has nested dicts)
        if any(isinstance(v, dict) for v in self.layout_config.values()):
            return  # Already migrated
        
        # Old format keys
        old_keys = {
            'callsign_x', 'callsign_y',
            'diploma_name_x', 'diploma_name_y',
            'date_x', 'date_y',
            'points_x', 'points_y',
            'diploma_number_x', 'diploma_number_y',
            'qr_x', 'qr_y'
        }
        
        # Check if this is old format
        if not any(k in self.layout_config for k in old_keys):
            return  # Not old format
        
        # Migrate to new format
        new_config = {}
        
        # Migrate callsign
        if 'callsign_x' in self.layout_config or 'callsign_y' in self.layout_config:
            new_config['callsign'] = {
                'enabled': True,
                'x': self.layout_config.get('callsign_x', 14.5),
                'y': self.layout_config.get('callsign_y', 10),
                'font': 'Lato',
                'size': 24,
                'bold': True,
                'italic': False,
                'color': '#333333'
            }
        
        # Migrate diploma_name
        if 'diploma_name_x' in self.layout_config or 'diploma_name_y' in self.layout_config:
            new_config['diploma_name'] = {
                'enabled': True,
                'x': self.layout_config.get('diploma_name_x', 14.5),
                'y': self.layout_config.get('diploma_name_y', 12),
                'font': 'Lato',
                'size': 16,
                'bold': False,
                'italic': False,
                'color': '#333333'
            }
        
        # Migrate date
        if 'date_x' in self.layout_config or 'date_y' in self.layout_config:
            new_config['date'] = {
                'enabled': True,
                'x': self.layout_config.get('date_x', 14.5),
                'y': self.layout_config.get('date_y', 14),
                'font': 'Lato',
                'size': 12,
                'bold': False,
                'italic': False,
                'color': '#666666'
            }
        
        # Migrate points
        if 'points_x' in self.layout_config or 'points_y' in self.layout_config:
            new_config['points'] = {
                'enabled': True,
                'x': self.layout_config.get('points_x', 14.5),
                'y': self.layout_config.get('points_y', 16),
                'font': 'Lato',
                'size': 12,
                'bold': False,
                'italic': False,
                'color': '#666666'
            }
        
        # Migrate diploma_number
        if 'diploma_number_x' in self.layout_config or 'diploma_number_y' in self.layout_config:
            new_config['diploma_number'] = {
                'enabled': True,
                'x': self.layout_config.get('diploma_number_x', 14.5),
                'y': self.layout_config.get('diploma_number_y', 10.5),
                'font': 'Lato',
                'size': 10,
                'bold': False,
                'italic': False,
                'color': '#999999'
            }
        
        # Migrate QR code
        if 'qr_x' in self.layout_config or 'qr_y' in self.layout_config:
            new_config['qr_code'] = {
                'enabled': True,
                'x': self.layout_config.get('qr_x', 2),
                'y': self.layout_config.get('qr_y', 2),
                'size': 3
            }
        
        # Update with migrated config
        self.layout_config = new_config
    
    def get_layout_config_from_elements(self):
        """
        Build layout config dict from DiplomaLayoutElement objects.
        Returns config compatible with pdf_generator.py format.
        """
        config = {}
        
        for element in self.layout_elements.all():
            element_config = {
                'enabled': element.enabled,
                'x': float(element.x_position),
                'y': float(element.y_position),
                'font': element.font_family,
                'size': element.font_size,
                'bold': element.bold,
                'italic': element.italic,
                'color': element.color,
            }
            
            # Add QR size for qr_code element
            if element.element_type == 'qr_code' and element.qr_size:
                element_config['size'] = float(element.qr_size)
            
            config[element.element_type] = element_config
        
        # If no elements exist yet, return default config
        if not config:
            return self.get_default_layout_config()
        
        return config
    
    def migrate_old_layout_config(self):
        """
        Migrate old flat JSON format to new DiplomaLayoutElement objects.
        Old format: {"callsign_x": 14.5, "callsign_y": 10}
        New format: DiplomaLayoutElement objects in database
        """
        # Check if we already have layout elements
        if self.layout_elements.exists():
            return  # Already migrated
        
        # Check if we have old-style layout_config
        if not self.layout_config:
            return  # No old config to migrate
        
        # Old format keys
        old_keys = {
            'callsign_x', 'callsign_y',
            'diploma_name_x', 'diploma_name_y',
            'date_x', 'date_y',
            'points_x', 'points_y',
            'diploma_number_x', 'diploma_number_y',
            'qr_x', 'qr_y'
        }
        
        # Check if this is old format
        if not any(k in self.layout_config for k in old_keys):
            # Check if it's nested format (also needs migration to DB)
            if any(k in self.layout_config for k in ['callsign', 'diploma_name', 'date', 'points', 'diploma_number', 'qr_code']):
                # Migrate from nested JSON to DiplomaLayoutElement
                for element_type, config in self.layout_config.items():
                    if not isinstance(config, dict):
                        continue
                    
                    element_data = {
                        'diploma_type': self,
                        'element_type': element_type,
                        'enabled': config.get('enabled', True),
                        'x_position': config.get('x', 14.5),
                        'y_position': config.get('y', 10),
                        'font_family': config.get('font', 'Lato'),
                        'font_size': config.get('size', 12),
                        'bold': config.get('bold', False),
                        'italic': config.get('italic', False),
                        'color': config.get('color', '#333333'),
                    }
                    
                    if element_type == 'qr_code':
                        element_data['qr_size'] = config.get('size', 3.0)
                    
                    DiplomaLayoutElement.objects.create(**element_data)
                
                # Clear old JSON config
                self.layout_config = {}
                return
            
            return  # Not old format
        
        # Migrate from flat old format to DiplomaLayoutElement
        element_defaults = {
            'callsign': {'font_size': 24, 'bold': True, 'x': 14.5, 'y': 10},
            'diploma_name': {'font_size': 16, 'bold': False, 'x': 14.5, 'y': 12},
            'date': {'font_size': 12, 'bold': False, 'x': 14.5, 'y': 14, 'color': '#666666'},
            'points': {'font_size': 12, 'bold': False, 'x': 14.5, 'y': 16, 'color': '#666666'},
            'diploma_number': {'font_size': 10, 'bold': False, 'x': 14.5, 'y': 10.5, 'color': '#999999'},
            'qr_code': {'font_size': 10, 'bold': False, 'x': 2, 'y': 2, 'qr_size': 3.0},
        }
        
        for element_type, defaults in element_defaults.items():
            x_key = f'{element_type}_x' if element_type != 'qr_code' else 'qr_x'
            y_key = f'{element_type}_y' if element_type != 'qr_code' else 'qr_y'
            
            if x_key in self.layout_config or y_key in self.layout_config:
                element_data = {
                    'diploma_type': self,
                    'element_type': element_type,
                    'enabled': True,
                    'x_position': self.layout_config.get(x_key, defaults['x']),
                    'y_position': self.layout_config.get(y_key, defaults['y']),
                    'font_family': 'Lato',
                    'font_size': defaults['font_size'],
                    'bold': defaults['bold'],
                    'italic': False,
                    'color': defaults.get('color', '#333333'),
                }
                
                if 'qr_size' in defaults:
                    element_data['qr_size'] = defaults['qr_size']
                
                DiplomaLayoutElement.objects.create(**element_data)
        
        # Clear old JSON config
        self.layout_config = {}
    
    def get_merged_layout_config(self):
        """Get layout config - now from DiplomaLayoutElement objects"""
        # First migrate old format if needed
        self.migrate_old_layout_config()
        
        # Get config from layout elements
        return self.get_layout_config_from_elements()
    
    def migrate_old_layout_config_json_to_json(self):
        """DEPRECATED: Old migration method for JSON-to-JSON migration"""
        
        default_config = self.get_default_layout_config()
        if not self.layout_config:
            return default_config
        
        # Deep merge: update defaults with custom values
        import copy
        merged = copy.deepcopy(default_config)
        for element, settings in self.layout_config.items():
            if element in merged:
                if isinstance(settings, dict):
                    merged[element].update(settings)
                else:
                    merged[element] = settings
            else:
                merged[element] = settings
        
        return merged


class Diploma(models.Model):
    """
    Issued diplomas to users.
    Tracks which users have earned which diplomas.
    """
    diploma_type = models.ForeignKey(
        'DiplomaType',
        on_delete=models.PROTECT,
        related_name='diplomas',
        verbose_name=_("Diploma Type")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diplomas',
        verbose_name=_("User")
    )
    issue_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Issue Date")
    )
    diploma_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Diploma Number"),
        help_text=_("Unique diploma certificate number")
    )
    verification_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("Verification Code"),
        help_text=_("UUID for verifying diploma authenticity")
    )
    pdf_file = models.FileField(
        upload_to='diplomas/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_("PDF File")
    )
    
    # Snapshot of points at time of issuance
    activator_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("Activator Points at Issuance")
    )
    hunter_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("Hunter Points at Issuance")
    )
    b2b_points_earned = models.IntegerField(
        default=0,
        verbose_name=_("B2B Points at Issuance")
    )
    
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_diplomas',
        verbose_name=_("Issued By"),
        help_text=_("Admin who issued/approved the diploma")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Diploma")
        verbose_name_plural = _("Diplomas")
        ordering = ['-issue_date']
        unique_together = ['diploma_type', 'user']
        indexes = [
            models.Index(fields=['user', 'issue_date']),
            models.Index(fields=['diploma_number']),
            models.Index(fields=['verification_code']),
        ]

    def __str__(self):
        return f"{self.diploma_number} - {self.user.callsign} - {self.diploma_type.name_en}"

    def save(self, *args, **kwargs):
        """Override save to generate diploma number if not set"""
        if not self.diploma_number:
            self.diploma_number = self.generate_diploma_number(
                self.diploma_type,
                self.user,
                self.issue_date or timezone.now()
            )
        super().save(*args, **kwargs)

    @staticmethod
    def generate_diploma_number(diploma_type, user, issue_date=None):
        """Generate unique diploma number"""
        if issue_date is None:
            issue_date = timezone.now()
        
        # Format: CATEGORY-YYYY-XXXX (e.g., HNT-2025-0001, ACT-2025-0042)
        category_code = {
            'hunter': 'HNT',
            'activator': 'ACT',
            'b2b': 'B2B',
            'special_event': 'SPE',
            'cluster': 'CLU',
            'other': 'OTH'
        }.get(diploma_type.category, 'DIP')
        
        year = issue_date.year
        
        # Count existing diplomas of this type this year
        from django.db import transaction
        with transaction.atomic():
            count = Diploma.objects.select_for_update().filter(
                diploma_type__category=diploma_type.category,
                issue_date__year=year
            ).count() + 1
        
        return f"{category_code}-{year}-{count:04d}"


class DiplomaProgress(models.Model):
    """
    Tracks user progress toward earning diplomas.
    Automatically updated as users complete activities.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diploma_progress',
        verbose_name=_("User")
    )
    diploma_type = models.ForeignKey(
        'DiplomaType',
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_("Diploma Type")
    )
    # Current point totals
    activator_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Activator Points")
    )
    hunter_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Hunter Points")
    )
    b2b_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("B2B Points")
    )
    # Bunker count totals (NEW)
    unique_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Unique Bunkers Activated")
    )
    total_activations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Activations")
    )
    unique_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Unique Bunkers Hunted")
    )
    total_hunted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Hunted")
    )
    percentage_complete = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Percentage Complete")
    )
    is_eligible = models.BooleanField(
        default=False,
        verbose_name=_("Eligible"),
        help_text=_("Has user met all requirements?")
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated")
    )

    class Meta:
        verbose_name = _("Diploma Progress")
        verbose_name_plural = _("Diploma Progress Records")
        ordering = ['-percentage_complete']
        unique_together = ['user', 'diploma_type']

    def __str__(self):
        return "{} - {} ({}%%)".format(self.user.callsign, self.diploma_type.name_en, self.percentage_complete)

    def calculate_progress(self):
        """Calculate progress percentage based on all requirements"""
        diploma_type = self.diploma_type
        
        # Check if diploma is time-limited and currently valid
        if diploma_type.is_time_limited() and not diploma_type.is_currently_valid():
            self.percentage_complete = Decimal('0.00')
            self.is_eligible = False
            return Decimal('0.00')
        
        # Collect all requirements
        requirements = {
            'activator_points': (self.activator_points, diploma_type.min_activator_points),
            'hunter_points': (self.hunter_points, diploma_type.min_hunter_points),
            'b2b_points': (self.b2b_points, diploma_type.min_b2b_points),
            'unique_activations': (self.unique_activations, diploma_type.min_unique_activations),
            'total_activations': (self.total_activations, diploma_type.min_total_activations),
            'unique_hunted': (self.unique_hunted, diploma_type.min_unique_hunted),
            'total_hunted': (self.total_hunted, diploma_type.min_total_hunted),
        }
        
        # Calculate progress for each requirement
        percentages = []
        all_met = True
        
        for req_name, (current, required) in requirements.items():
            if required > 0:  # Only count requirements that are set
                pct = min(100, (current / required * 100))
                percentages.append(pct)
                if current < required:
                    all_met = False
        
        # If no requirements are set, diploma is automatically earned
        if not percentages:
            self.percentage_complete = Decimal('100.00')
            self.is_eligible = True
            return Decimal('100.00')
        
        # Calculate average percentage across all requirements
        avg_percentage = sum(percentages) / len(percentages)
        self.percentage_complete = Decimal(str(avg_percentage))
        self.is_eligible = all_met
        
        return self.percentage_complete
    
    def update_points(self, activator=None, hunter=None, b2b=None, 
                      unique_activations=None, total_activations=None,
                      unique_hunted=None, total_hunted=None):
        """Update all progress values and recalculate percentage"""
        if activator is not None:
            self.activator_points = activator
        if hunter is not None:
            self.hunter_points = hunter
        if b2b is not None:
            self.b2b_points = b2b
        if unique_activations is not None:
            self.unique_activations = unique_activations
        if total_activations is not None:
            self.total_activations = total_activations
        if unique_hunted is not None:
            self.unique_hunted = unique_hunted
        if total_hunted is not None:
            self.total_hunted = total_hunted
        
        self.calculate_progress()
        self.save()


class DiplomaVerification(models.Model):
    """
    Log of diploma verification checks.
    Track when and by whom diplomas are verified.
    """
    diploma = models.ForeignKey(
        'Diploma',
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name=_("Diploma")
    )
    verified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Verified At")
    )
    verified_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Verified By IP"),
        help_text=_("IP address of verifier")
    )
    verified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diploma_verifications',
        verbose_name=_("Verified By User"),
        help_text=_("User who performed verification (if logged in)")
    )
    verification_method = models.CharField(
        max_length=50,
        choices=[
            ('number', _('Diploma Number')),
            ('code', _('Verification Code')),
            ('qr', _('QR Code Scan')),
            ('manual', _('Manual Check')),
        ],
        default='number',
        verbose_name=_("Verification Method")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Diploma Verification")
        verbose_name_plural = _("Diploma Verifications")
        ordering = ['-verified_at']

    def __str__(self):
        return f"Verification of {self.diploma.diploma_number} at {self.verified_at.strftime('%Y-%m-%d %H:%M')}"

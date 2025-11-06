from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class BunkerCategory(models.Model):
    """
    Categories for bunkers (e.g., Command Bunker, Storage Bunker, Shelter).
    Supports Polish and English translations.
    """
    name_pl = models.CharField(
        max_length=100,
        verbose_name=_("Name (Polish)"),
        help_text=_("Category name in Polish")
    )
    name_en = models.CharField(
        max_length=100,
        verbose_name=_("Name (English)"),
        help_text=_("Category name in English")
    )
    description_pl = models.TextField(
        blank=True,
        verbose_name=_("Description (Polish)"),
        help_text=_("Category description in Polish")
    )
    description_en = models.TextField(
        blank=True,
        verbose_name=_("Description (English)"),
        help_text=_("Category description in English")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icon"),
        help_text=_("Icon class or name for the category (e.g., 'fas fa-shield-alt')")
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which categories are displayed")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bunker Category")
        verbose_name_plural = _("Bunker Categories")
        ordering = ['display_order', 'name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_pl}"


class Bunker(models.Model):
    """
    Main bunker model with GPS coordinates, translations, and verification status.
    """
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Reference Number"),
        help_text=_("Unique reference code for the bunker (e.g., 'BNK-001')")
    )
    name_pl = models.CharField(
        max_length=200,
        verbose_name=_("Name (Polish)"),
        help_text=_("Bunker name in Polish")
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name=_("Name (English)"),
        help_text=_("Bunker name in English")
    )
    description_pl = models.TextField(
        blank=True,
        verbose_name=_("Description (Polish)"),
        help_text=_("Detailed description in Polish")
    )
    description_en = models.TextField(
        blank=True,
        verbose_name=_("Description (English)"),
        help_text=_("Detailed description in English")
    )
    category = models.ForeignKey(
        BunkerCategory,
        on_delete=models.PROTECT,
        related_name='bunkers',
        verbose_name=_("Category")
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name=_("Latitude"),
        help_text=_("GPS latitude coordinate (-90 to 90)")
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name=_("Longitude"),
        help_text=_("GPS longitude coordinate (-180 to 180)")
    )
    locator = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Locator"),
        help_text=_("Maidenhead grid locator (e.g., JO72RI)")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Has this bunker been verified by an administrator?")
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_bunkers',
        verbose_name=_("Verified By")
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verification Date")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bunkers',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bunker")
        verbose_name_plural = _("Bunkers")
        ordering = ['reference_number']
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['category', 'is_verified']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.name_en}"

    def get_coordinates(self):
        """Return tuple of (latitude, longitude)"""
        return (float(self.latitude), float(self.longitude))


class BunkerPhoto(models.Model):
    """
    Photos for bunkers with approval workflow.
    """
    bunker = models.ForeignKey(
        Bunker,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_("Bunker")
    )
    photo = models.ImageField(
        upload_to='bunker_photos/%Y/%m/',
        verbose_name=_("Photo")
    )
    caption_pl = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Caption (Polish)")
    )
    caption_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Caption (English)")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_photos',
        verbose_name=_("Uploaded By")
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Approved"),
        help_text=_("Has this photo been approved by a moderator?")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_photos',
        verbose_name=_("Approved By")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bunker Photo")
        verbose_name_plural = _("Bunker Photos")
        ordering = ['-uploaded_at']

    def __str__(self):
        status = "✓" if self.is_approved else "⏳"
        return f"{status} Photo for {self.bunker.reference_number}"


class BunkerResource(models.Model):
    """
    External resources and links related to bunkers.
    """
    bunker = models.ForeignKey(
        Bunker,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name=_("Bunker")
    )
    title_pl = models.CharField(
        max_length=200,
        verbose_name=_("Title (Polish)")
    )
    title_en = models.CharField(
        max_length=200,
        verbose_name=_("Title (English)")
    )
    url = models.URLField(
        verbose_name=_("URL"),
        help_text=_("External link to resource")
    )
    resource_type = models.CharField(
        max_length=50,
        choices=[
            ('article', _('Article')),
            ('video', _('Video')),
            ('map', _('Map')),
            ('documentation', _('Documentation')),
            ('other', _('Other')),
        ],
        default='other',
        verbose_name=_("Resource Type")
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_resources',
        verbose_name=_("Added By")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bunker Resource")
        verbose_name_plural = _("Bunker Resources")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title_en} ({self.bunker.reference_number})"


class BunkerInspection(models.Model):
    """
    Record of user visits/inspections to bunkers.
    Used for tracking Hunter activities.
    """
    bunker = models.ForeignKey(
        Bunker,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name=_("Bunker")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bunker_inspections',
        verbose_name=_("User")
    )
    inspection_date = models.DateTimeField(
        verbose_name=_("Inspection Date"),
        help_text=_("When did the inspection/visit occur?")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about the inspection")
    )
    verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Has this inspection been verified?")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bunker Inspection")
        verbose_name_plural = _("Bunker Inspections")
        ordering = ['-inspection_date']
        unique_together = ['bunker', 'user', 'inspection_date']

    def __str__(self):
        return f"{self.user.callsign} inspected {self.bunker.reference_number}"


class BunkerRequest(models.Model):
    """
    User requests to add new bunkers - requires admin approval
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Reference Number"),
        help_text=_("Reference code will be assigned automatically upon approval")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
        help_text=_("Bunker name")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description of the bunker")
    )
    bunker_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Type"),
        help_text=_("Type of bunker (e.g., WW2 Battle Bunker)")
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_("Latitude"),
        help_text=_("GPS latitude coordinate")
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_("Longitude"),
        help_text=_("GPS longitude coordinate")
    )
    locator = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Locator"),
        help_text=_("Maidenhead locator (optional)")
    )
    photo_url = models.URLField(
        blank=True,
        verbose_name=_("Photo URL"),
        help_text=_("Link to photo (optional)")
    )
    additional_info = models.TextField(
        blank=True,
        verbose_name=_("Additional Info"),
        help_text=_("Any additional information")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status")
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_("Rejection Reason")
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bunker_requests',
        verbose_name=_("Requested By")
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_bunker_requests',
        verbose_name=_("Reviewed By")
    )
    bunker = models.ForeignKey(
        Bunker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='creation_request',
        verbose_name=_("Created Bunker"),
        help_text=_("The bunker created from this request if approved")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Bunker Request")
        verbose_name_plural = _("Bunker Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['requested_by']),
        ]
    
    def __str__(self):
        return f"{self.reference_number} - {self.name} ({self.get_status_display()})"

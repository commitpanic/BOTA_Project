from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Cluster(models.Model):
    """
    Groups of bunkers organized by region, theme, or historical significance.
    Example: "Linia Mołotowa", "Fortyfikacje Gdańskie", "Forty Modlińskie"
    """
    name_pl = models.CharField(
        max_length=200,
        verbose_name=_("Name (Polish)"),
        help_text=_("Cluster name in Polish")
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name=_("Name (English)"),
        help_text=_("Cluster name in English")
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
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Region"),
        help_text=_("Geographic region (e.g., 'Pomorskie', 'Mazowieckie')")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clusters',
        verbose_name=_("Created By")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Is this cluster currently active?")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Cluster")
        verbose_name_plural = _("Clusters")
        ordering = ['region', 'name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_pl}"

    def get_bunker_count(self):
        """Return the number of bunkers in this cluster"""
        return self.members.count()

    def get_active_bunkers(self):
        """Return queryset of bunkers in this cluster"""
        return self.members.select_related('bunker').filter(bunker__is_verified=True)


class ClusterMember(models.Model):
    """
    Through model linking Bunkers to Clusters.
    A bunker can belong to multiple clusters.
    """
    cluster = models.ForeignKey(
        'Cluster',
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_("Cluster")
    )
    bunker = models.ForeignKey(
        'bunkers.Bunker',
        on_delete=models.CASCADE,
        related_name='cluster_memberships',
        verbose_name=_("Bunker")
    )
    join_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Join Date"),
        help_text=_("When was this bunker added to the cluster?")
    )
    display_order = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Display Order"),
        help_text=_("Order in which bunkers are displayed within the cluster")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about this bunker's role in the cluster")
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_cluster_members',
        verbose_name=_("Added By")
    )

    class Meta:
        verbose_name = _("Cluster Member")
        verbose_name_plural = _("Cluster Members")
        ordering = ['cluster', 'display_order', 'bunker__reference_number']
        unique_together = ['cluster', 'bunker']

    def __str__(self):
        return f"{self.bunker.reference_number} in {self.cluster.name_en}"


class ClusterAlert(models.Model):
    """
    Alerts and announcements for clusters.
    Used to notify users about cluster events, updates, or special activations.
    """
    ALERT_TYPES = [
        ('info', _('Information')),
        ('event', _('Event')),
        ('warning', _('Warning')),
        ('special', _('Special Activation')),
    ]

    cluster = models.ForeignKey(
        'Cluster',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_("Cluster")
    )
    title_pl = models.CharField(
        max_length=200,
        verbose_name=_("Title (Polish)")
    )
    title_en = models.CharField(
        max_length=200,
        verbose_name=_("Title (English)")
    )
    message_pl = models.TextField(
        verbose_name=_("Message (Polish)")
    )
    message_en = models.TextField(
        verbose_name=_("Message (English)")
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        default='info',
        verbose_name=_("Alert Type")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Should this alert be displayed?")
    )
    start_date = models.DateTimeField(
        verbose_name=_("Start Date"),
        help_text=_("When should this alert start being displayed?")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("When should this alert stop being displayed? (leave blank for no end)")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alerts',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Cluster Alert")
        verbose_name_plural = _("Cluster Alerts")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.alert_type.upper()}: {self.title_en} ({self.cluster.name_en})"

    def is_currently_active(self):
        """Check if alert should be displayed based on dates and is_active flag"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.start_date > now:
            return False
        
        if self.end_date and self.end_date < now:
            return False
        
        return True


def detect_band_from_frequency(frequency):
    """
    Detect amateur radio band from frequency in MHz.
    Returns band name (e.g., "40m", "20m") or None if not in amateur band.
    """
    freq = float(frequency)
    
    band_map = [
        (1.8, 2.0, "160m"),
        (3.5, 4.0, "80m"),
        (7.0, 7.3, "40m"),
        (10.1, 10.15, "30m"),
        (14.0, 14.35, "20m"),
        (18.068, 18.168, "17m"),
        (21.0, 21.45, "15m"),
        (24.89, 24.99, "12m"),
        (28.0, 29.7, "10m"),
        (50.0, 54.0, "6m"),
        (144.0, 148.0, "2m"),
        (430.0, 440.0, "70cm"),
    ]
    
    for min_freq, max_freq, band_name in band_map:
        if min_freq <= freq <= max_freq:
            return band_name
    
    return None


class SpotHistory(models.Model):
    """
    History of respots for a spot.
    Records who respotted and when.
    """
    spot = models.ForeignKey(
        'Spot',
        on_delete=models.CASCADE,
        related_name='respot_history',
        verbose_name=_("Spot")
    )
    respotter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='respots',
        verbose_name=_("Respotter"),
        help_text=_("User who made this respot")
    )
    respotted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Respotted At")
    )
    comment = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Comment"),
        help_text=_("Optional comment for this respot")
    )

    class Meta:
        verbose_name = _("Spot History")
        verbose_name_plural = _("Spot History")
        ordering = ['-respotted_at']
        indexes = [
            models.Index(fields=['spot', '-respotted_at']),
            models.Index(fields=['respotter', '-respotted_at']),
        ]

    def __str__(self):
        return f"{self.respotter.callsign} respotted {self.spot.activator_callsign} at {self.respotted_at}"


class Spot(models.Model):
    """
    Real-time spotting system for active bunker activations.
    Spots expire after 30 minutes unless refreshed.
    """
    activator_callsign = models.CharField(
        max_length=20,
        verbose_name=_("Activator Callsign"),
        help_text=_("Callsign of the operator activating the bunker")
    )
    spotter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_spots',
        verbose_name=_("Spotter"),
        help_text=_("User who posted this spot")
    )
    frequency = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('1.8')), MaxValueValidator(Decimal('450.0'))],
        verbose_name=_("Frequency (MHz)"),
        help_text=_("Operating frequency in MHz (e.g., 14.230)")
    )
    band = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Band"),
        help_text=_("Amateur radio band (auto-detected from frequency)")
    )
    bunker_reference = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Bunker Reference"),
        help_text=_("Bunker reference number (e.g., B/SP-0039) - optional")
    )
    bunker = models.ForeignKey(
        'bunkers.Bunker',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spots',
        verbose_name=_("Bunker"),
        help_text=_("Resolved bunker object (if reference provided)")
    )
    comment = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        default='',
        verbose_name=_("Comment"),
        help_text=_("Optional comment (e.g., '73!', 'QRV SSB')")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last time this spot was refreshed")
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires At"),
        help_text=_("When this spot will expire (30 minutes from last update)")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Is this spot still active?")
    )
    respot_count = models.IntegerField(
        default=0,
        verbose_name=_("Respot Count"),
        help_text=_("Number of times this spot has been re-spotted")
    )
    last_respot_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Respot Time"),
        help_text=_("Time of the most recent respot")
    )

    class Meta:
        verbose_name = _("Spot")
        verbose_name_plural = _("Spots")
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['activator_callsign', 'frequency', 'is_active']),
            models.Index(fields=['expires_at', 'is_active']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['band', 'is_active']),
        ]

    def __str__(self):
        bunker_info = self.bunker_reference if self.bunker_reference else "No ref"
        return f"{self.activator_callsign} @ {self.frequency} MHz ({bunker_info})"

    def save(self, *args, **kwargs):
        """Auto-detect band from frequency and set expiration time"""
        # Detect band if not set
        if not self.band:
            detected_band = detect_band_from_frequency(self.frequency)
            self.band = detected_band if detected_band else "Unknown"
        
        # Set expiration time if not set (30 minutes from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        
        # Try to resolve bunker from reference
        if self.bunker_reference and not self.bunker:
            from bunkers.models import Bunker
            try:
                self.bunker = Bunker.objects.get(reference_number=self.bunker_reference)
            except Bunker.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def refresh_expiration(self):
        """Extend the expiration time by 30 minutes from now"""
        self.expires_at = timezone.now() + timedelta(minutes=30)
        self.updated_at = timezone.now()
        self.is_active = True
        self.save()

    def is_expired(self):
        """Check if spot has expired"""
        return timezone.now() > self.expires_at

    def time_since_update(self):
        """Return human-readable time since last update"""
        delta = timezone.now() - self.updated_at
        minutes = int(delta.total_seconds() / 60)
        
        if minutes < 1:
            return _("Just now")
        elif minutes == 1:
            return _("1 min ago")
        else:
            return _("%(minutes)d min ago") % {'minutes': minutes}

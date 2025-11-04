from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


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

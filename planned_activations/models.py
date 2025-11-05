from django.db import models
from django.conf import settings
from bunkers.models import Bunker
from django.utils.translation import gettext_lazy as _


class PlannedActivation(models.Model):
    """Model for planned bunker activations"""
    
    BAND_CHOICES = [
        ('160m', '160m (1.8 MHz)'),
        ('80m', '80m (3.5 MHz)'),
        ('40m', '40m (7 MHz)'),
        ('30m', '30m (10 MHz)'),
        ('20m', '20m (14 MHz)'),
        ('17m', '17m (18 MHz)'),
        ('15m', '15m (21 MHz)'),
        ('12m', '12m (24 MHz)'),
        ('10m', '10m (28 MHz)'),
        ('6m', '6m (50 MHz)'),
        ('2m', '2m (144 MHz)'),
        ('70cm', '70cm (432 MHz)'),
    ]
    
    MODE_CHOICES = [
        ('CW', 'CW'),
        ('SSB', 'SSB'),
        ('FM', 'FM'),
        ('FT8', 'FT8'),
        ('FT4', 'FT4'),
        ('RTTY', 'RTTY'),
        ('PSK31', 'PSK31'),
        ('SSTV', 'SSTV'),
        ('OTHER', _('Other')),
    ]
    
    # Basic info
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='planned_activations',
        verbose_name=_("User")
    )
    bunker = models.ForeignKey(
        Bunker,
        on_delete=models.CASCADE,
        related_name='planned_activations',
        verbose_name=_("Bunker"),
        help_text=_("Which bunker will be activated")
    )
    
    # Date and time
    planned_date = models.DateField(
        verbose_name=_("Planned Date"),
        help_text=_("When do you plan to activate")
    )
    planned_time_start = models.TimeField(
        verbose_name=_("Start Time (UTC)"),
        null=True,
        blank=True,
        help_text=_("Approximate start time in UTC")
    )
    planned_time_end = models.TimeField(
        verbose_name=_("End Time (UTC)"),
        null=True,
        blank=True,
        help_text=_("Approximate end time in UTC")
    )
    
    # Operating details
    callsign = models.CharField(
        max_length=20,
        verbose_name=_("Callsign"),
        help_text=_("Callsign that will be used during activation")
    )
    bands = models.CharField(
        max_length=200,
        verbose_name=_("Bands"),
        help_text=_("Which bands you plan to operate on (comma-separated)")
    )
    modes = models.CharField(
        max_length=200,
        verbose_name=_("Modes"),
        help_text=_("Which modes you plan to use (comma-separated)")
    )
    
    # Additional info
    comments = models.TextField(
        blank=True,
        verbose_name=_("Comments"),
        help_text=_("Additional information about the activation")
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    
    class Meta:
        verbose_name = _("Planned Activation")
        verbose_name_plural = _("Planned Activations")
        ordering = ['planned_date', 'planned_time_start']
        indexes = [
            models.Index(fields=['planned_date']),
            models.Index(fields=['user']),
            models.Index(fields=['bunker']),
        ]
    
    def __str__(self):
        return f"{self.callsign} @ {self.bunker.reference_number} on {self.planned_date}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('planned_activation_detail', kwargs={'pk': self.pk})
    
    def is_past(self):
        """Check if the planned date is in the past"""
        from django.utils import timezone
        return self.planned_date < timezone.now().date()

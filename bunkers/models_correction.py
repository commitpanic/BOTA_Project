"""
Bunker correction request model.
Allows users to suggest corrections to existing bunkers.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class BunkerCorrectionRequest(models.Model):
    """
    User requests to correct existing bunker information - requires admin approval
    Similar to BunkerRequest but for modifications of existing bunkers
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    bunker = models.ForeignKey(
        'Bunker',
        on_delete=models.CASCADE,
        related_name='correction_requests',
        verbose_name=_("Bunker"),
        help_text=_("The bunker to be corrected")
    )
    
    # Fields to be corrected (null = no change requested)
    new_name_pl = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("New Name (Polish)"),
        help_text=_("Leave empty if no change needed")
    )
    new_name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("New Name (English)"),
        help_text=_("Leave empty if no change needed")
    )
    new_description_pl = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("New Description (Polish)"),
        help_text=_("Leave empty if no change needed")
    )
    new_description_en = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("New Description (English)"),
        help_text=_("Leave empty if no change needed")
    )
    new_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_("New Latitude"),
        help_text=_("Leave empty if no change needed")
    )
    new_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_("New Longitude"),
        help_text=_("Leave empty if no change needed")
    )
    new_category = models.ForeignKey(
        'BunkerCategory',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("New Category"),
        help_text=_("Leave empty if no change needed")
    )
    
    # Explanation
    correction_reason = models.TextField(
        verbose_name=_("Correction Reason"),
        help_text=_("Explain why this correction is needed")
    )
    additional_info = models.TextField(
        blank=True,
        verbose_name=_("Additional Info"),
        help_text=_("Any additional information or evidence")
    )
    
    # Status tracking
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
    
    # User tracking
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bunker_correction_requests',
        verbose_name=_("Requested By")
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_bunker_corrections',
        verbose_name=_("Reviewed By")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )
    
    class Meta:
        verbose_name = _("Bunker Correction Request")
        verbose_name_plural = _("Bunker Correction Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['bunker']),
            models.Index(fields=['requested_by']),
        ]
    
    def __str__(self):
        return f"Correction for {self.bunker.reference_number} by {self.requested_by.callsign} ({self.get_status_display()})"
    
    def has_changes(self):
        """Check if any correction fields are filled"""
        return any([
            self.new_name_pl,
            self.new_name_en,
            self.new_description_pl,
            self.new_description_en,
            self.new_latitude,
            self.new_longitude,
            self.new_category,
        ])

"""
Forms for bunker correction requests
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import BunkerCorrectionRequest, BunkerCategory


class BunkerCorrectionRequestForm(forms.ModelForm):
    """Form for submitting bunker correction requests"""
    
    class Meta:
        model = BunkerCorrectionRequest
        fields = [
            'new_name_pl',
            'new_name_en',
            'new_description_pl',
            'new_description_en',
            'new_latitude',
            'new_longitude',
            'new_category',
            'correction_reason',
            'additional_info'
        ]
        widgets = {
            'new_name_pl': forms.TextInput(attrs={'class': 'form-control'}),
            'new_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'new_description_pl': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'new_description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'new_latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'new_longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'new_category': forms.Select(attrs={'class': 'form-select'}),
            'correction_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        """Validate that at least one correction field is filled"""
        cleaned_data = super().clean()
        
        # Check if any correction field is filled
        has_changes = any([
            cleaned_data.get('new_name_pl'),
            cleaned_data.get('new_name_en'),
            cleaned_data.get('new_description_pl'),
            cleaned_data.get('new_description_en'),
            cleaned_data.get('new_latitude'),
            cleaned_data.get('new_longitude'),
            cleaned_data.get('new_category'),
        ])
        
        if not has_changes:
            raise forms.ValidationError(
                _('Please fill in at least one field to correct.')
            )
        
        return cleaned_data
    
    def clean_new_latitude(self):
        """Validate latitude is within Poland bounds"""
        latitude = self.cleaned_data.get('new_latitude')
        if latitude:
            if not (Decimal('49') <= latitude <= Decimal('55')):
                raise forms.ValidationError(
                    _('Latitude must be within Poland (49-55°N)')
                )
        return latitude
    
    def clean_new_longitude(self):
        """Validate longitude is within Poland bounds"""
        longitude = self.cleaned_data.get('new_longitude')
        if longitude:
            if not (Decimal('14') <= longitude <= Decimal('24')):
                raise forms.ValidationError(
                    _('Longitude must be within Poland (14-24°E)')
                )
        return longitude

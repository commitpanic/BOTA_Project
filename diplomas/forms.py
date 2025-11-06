from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DiplomaLayoutElement


class ColorPickerWidget(forms.TextInput):
    """Custom widget for color picker input"""
    input_type = 'color'
    
    def __init__(self, attrs=None):
        default_attrs = {'style': 'width: 80px; height: 40px; cursor: pointer;'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class DiplomaLayoutElementForm(forms.ModelForm):
    """Form for DiplomaLayoutElement with color picker"""
    
    # Override qr_size to not be required
    qr_size = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label=_("QR Code Size (cm)"),
        help_text=_("Only for QR code element"),
        initial=3.0
    )
    
    class Meta:
        model = DiplomaLayoutElement
        fields = '__all__'
        widgets = {
            'color': ColorPickerWidget(),
            'enabled': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
            'bold': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
            'italic': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
        }
    
    def clean(self):
        """Ensure boolean fields are properly handled"""
        cleaned_data = super().clean()
        
        # Explicitly handle boolean fields
        for field in ['enabled', 'bold', 'italic']:
            if field not in cleaned_data or cleaned_data[field] is None:
                cleaned_data[field] = False
        
        return cleaned_data

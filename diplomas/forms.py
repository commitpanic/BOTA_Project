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
    
    class Meta:
        model = DiplomaLayoutElement
        fields = '__all__'
        widgets = {
            'color': ColorPickerWidget(),
            'enabled': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
            'bold': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
            'italic': forms.CheckboxInput(attrs={'class': 'vCheckboxInput'}),
        }
        help_texts = {
            'color': _('Click to choose a color'),
            'qr_size': _('Only for QR code element'),
        }
    
    def clean_qr_size(self):
        """Clear qr_size for non-QR elements"""
        element_type = self.cleaned_data.get('element_type')
        qr_size = self.cleaned_data.get('qr_size')
        
        if element_type != 'qr_code':
            return None
        
        return qr_size
    
    def clean(self):
        """Ensure boolean fields are properly handled"""
        cleaned_data = super().clean()
        
        # Explicitly set boolean fields to False if not provided
        if 'enabled' not in cleaned_data or cleaned_data['enabled'] is None:
            cleaned_data['enabled'] = False
        if 'bold' not in cleaned_data or cleaned_data['bold'] is None:
            cleaned_data['bold'] = False
        if 'italic' not in cleaned_data or cleaned_data['italic'] is None:
            cleaned_data['italic'] = False
        
        return cleaned_data

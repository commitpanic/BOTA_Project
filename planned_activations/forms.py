from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import PlannedActivation


class PlannedActivationForm(forms.ModelForm):
    """Form for creating/editing planned activations"""
    
    class Meta:
        model = PlannedActivation
        fields = [
            'bunker', 'planned_date', 'planned_time_start', 'planned_time_end',
            'callsign', 'bands', 'modes', 'comments'
        ]
        widgets = {
            'bunker': forms.Select(attrs={'class': 'form-select'}),
            'planned_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': 'YYYY-MM-DD'
                }
            ),
            'planned_time_start': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'placeholder': 'HH:MM'
                }
            ),
            'planned_time_end': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'placeholder': 'HH:MM'
                }
            ),
            'callsign': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('e.g., SP3XYZ')
                }
            ),
            'bands': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('e.g., 20m, 40m, 80m')
                }
            ),
            'modes': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('e.g., CW, SSB, FT8')
                }
            ),
            'comments': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': _('Additional information about your activation...')
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill callsign with user's callsign if creating new
        if user and not self.instance.pk:
            self.fields['callsign'].initial = user.callsign
        
        # Make bunker field show reference and name
        self.fields['bunker'].label_from_instance = lambda obj: f"{obj.reference_number} - {obj.name_pl}"
    
    def clean_planned_date(self):
        """Validate that planned date is not in the past"""
        planned_date = self.cleaned_data.get('planned_date')
        if planned_date:
            today = timezone.now().date()
            if planned_date < today:
                raise forms.ValidationError(
                    _('Planned date cannot be in the past. Please select today or a future date.')
                )
        return planned_date

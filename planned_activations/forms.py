from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import PlannedActivation


class PlannedActivationForm(forms.ModelForm):
    """Form for creating/editing planned activations"""
    
    # Custom bunker field with text input for search
    bunker_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Start typing bunker reference or name...'),
            'list': 'bunkerList',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = PlannedActivation
        fields = [
            'bunker', 'planned_date', 'planned_time_start', 'planned_time_end',
            'callsign', 'bands', 'modes', 'comments'
        ]
        widgets = {
            'bunker': forms.HiddenInput(),  # Hidden field to store bunker ID
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
        
        # Pre-fill bunker_search with current bunker name if editing
        if self.instance.pk and self.instance.bunker:
            self.fields['bunker_search'].initial = f"{self.instance.bunker.reference_number} - {self.instance.bunker.name_pl}"
        
        # Reorder fields to show bunker_search before hidden bunker field
        field_order = ['bunker_search', 'bunker', 'planned_date', 'planned_time_start', 
                      'planned_time_end', 'callsign', 'bands', 'modes', 'comments']
        self.order_fields(field_order)
    
    def clean(self):
        """Convert bunker_search to bunker ID"""
        cleaned_data = super().clean()
        bunker_search = cleaned_data.get('bunker_search')
        bunker = cleaned_data.get('bunker')
        
        # If bunker is not set but bunker_search has value, try to find the bunker
        if bunker_search and not bunker:
            from bunkers.models import Bunker
            # Extract reference number (everything before " - ")
            reference = bunker_search.split(' - ')[0].strip()
            try:
                bunker = Bunker.objects.get(reference_number=reference)
                cleaned_data['bunker'] = bunker
            except Bunker.DoesNotExist:
                raise forms.ValidationError({
                    'bunker_search': _('Invalid bunker selected. Please choose from the list.')
                })
        elif not bunker_search and not bunker:
            raise forms.ValidationError({
                'bunker_search': _('Please select a bunker.')
            })
        
        return cleaned_data
    
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

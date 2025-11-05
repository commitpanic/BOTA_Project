"""
Forms for accounts app
"""
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CallsignPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that requires both callsign and email.
    This adds an extra layer of security by verifying user identity.
    """
    callsign = forms.CharField(
        max_length=20,
        required=True,
        label=_("Callsign"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your callsign'),
            'autofocus': True
        })
    )
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address')
        })
    )
    
    def clean(self):
        """
        Validate that both callsign and email match an existing user.
        """
        cleaned_data = super().clean()
        callsign = cleaned_data.get('callsign')
        email = cleaned_data.get('email')
        
        if callsign and email:
            # Check if user exists with both callsign and email
            try:
                user = User.objects.get(callsign=callsign, email=email)
                if not user.is_active:
                    raise forms.ValidationError(
                        _("This account is inactive. Please contact support.")
                    )
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _("No account found with this callsign and email combination.")
                )
        
        return cleaned_data
    
    def get_users(self, email):
        """
        Override to match by both callsign and email.
        This is called by PasswordResetForm to get the user(s) to send email to.
        """
        callsign = self.cleaned_data.get('callsign')
        
        # Get active users matching both callsign and email
        active_users = User._default_manager.filter(
            callsign=callsign,
            email__iexact=email,
            is_active=True
        )
        
        return (
            u for u in active_users
            if u.has_usable_password()
        )

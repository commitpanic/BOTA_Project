"""
Middleware to force password change on first login for users with force_password_change=True
"""
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.contrib import messages
from django.utils.translation import gettext as _


class ForcePasswordChangeMiddleware:
    """
    Middleware that checks if user must change password and redirects to change password page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and must change password
        if request.user.is_authenticated and hasattr(request.user, 'force_password_change'):
            if request.user.force_password_change:
                # Paths that don't require password change (check dynamically)
                exempt_paths = [
                    '/change-password-required/',  # Frontend URL for password change
                    '/accounts/logout/',
                    '/accounts/login/',
                    '/set-language/',
                    '/admin/logout/',
                    '/static/',
                    '/media/',
                    '/jsi18n/',
                ]
                
                # Allow access to exempt paths
                if not any(request.path.startswith(path) for path in exempt_paths):
                    # Only add message once per session
                    if not request.session.get('password_change_warning_shown'):
                        messages.warning(
                            request,
                            _('You must change your password before continuing.')
                        )
                        request.session['password_change_warning_shown'] = True
                    
                    return redirect('change_password_required')

        response = self.get_response(request)
        return response

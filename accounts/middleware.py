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
                # Paths that don't require password change
                # Note: Frontend URLs use i18n patterns (/pl/, /en/, etc.)
                exempt_path_patterns = [
                    '/change-password-required/',  # Password change page (with any language prefix)
                    '/logout/',                     # Logout page
                    '/login/',                      # Login page  
                    '/admin/logout/',              # Admin logout
                    '/static/',                    # Static files
                    '/media/',                     # Media files
                    '/jsi18n/',                    # JavaScript i18n
                    '/i18n/',                      # Language switcher
                ]
                
                # Check if current path matches any exempt pattern
                is_exempt = any(pattern in request.path for pattern in exempt_path_patterns)
                
                if not is_exempt:
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

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
                exempt_url_names = [
                    'change_password_required',
                    'logout',
                    'login',
                    'set_language',
                ]
                
                exempt_path_prefixes = [
                    '/admin/logout/',
                    '/static/',
                    '/media/',
                    '/jsi18n/',
                    '/i18n/',
                ]
                
                # Check if current path is exempt by prefix
                path_exempt = any(request.path.startswith(prefix) for prefix in exempt_path_prefixes)
                
                # Check if current URL name is exempt (handles i18n patterns)
                url_name_exempt = False
                if hasattr(request, 'resolver_match') and request.resolver_match:
                    url_name_exempt = request.resolver_match.url_name in exempt_url_names
                
                if not path_exempt and not url_name_exempt:
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

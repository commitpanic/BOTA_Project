"""
Middleware to force password change on first login for users with force_password_change=True
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _


class ForcePasswordChangeMiddleware:
    """
    Middleware that checks if user must change password and redirects to change password page.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that don't require password change
        self.exempt_paths = [
            reverse('change_password_required'),
            reverse('logout'),
            '/admin/logout/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Check if user is authenticated and must change password
        if request.user.is_authenticated and hasattr(request.user, 'force_password_change'):
            if request.user.force_password_change:
                # Allow access to password change page and logout
                if not any(request.path.startswith(path) for path in self.exempt_paths):
                    messages.warning(
                        request,
                        _('You must change your password before continuing.')
                    )
                    return redirect('change_password_required')

        response = self.get_response(request)
        return response

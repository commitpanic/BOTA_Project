"""
Simple health check view for testing Render deployment
"""
from django.http import JsonResponse
from django.conf import settings
import os

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database': 'connected' if 'DATABASE_URL' in os.environ else 'sqlite',
    })

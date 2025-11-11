"""
Simple health check view for testing Render deployment
"""
from django.http import JsonResponse
from django.conf import settings
import os
from pathlib import Path

def health_check(request):
    """Simple health check endpoint with static files debugging"""
    static_root = Path(settings.STATIC_ROOT)
    images_dir = static_root / 'images'
    logo_file = images_dir / 'bota_logo.png'
    
    return JsonResponse({
        'status': 'ok',
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database': 'connected' if 'DATABASE_URL' in os.environ else 'sqlite',
        'static_root': str(settings.STATIC_ROOT),
        'static_root_exists': static_root.exists(),
        'images_dir_exists': images_dir.exists(),
        'logo_exists': logo_file.exists(),
        'static_url': settings.STATIC_URL,
    })

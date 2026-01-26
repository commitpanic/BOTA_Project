"""
Production diagnostics view
"""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
import os
import sys


@never_cache
def production_diagnostics(request):
    """Debug endpoint to check production configuration"""
    
    # Get database info
    from django.conf import settings
    from django.db import connection
    
    db_info = {
        'engine': settings.DATABASES['default']['ENGINE'],
        'name': settings.DATABASES['default'].get('NAME', 'N/A'),
    }
    
    # Try to connect to database
    db_connection = 'unknown'
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_connection = 'success'
    except Exception as e:
        db_connection = f'failed: {str(e)}'
    
    # Check installed apps
    installed_apps = list(settings.INSTALLED_APPS)
    
    # Check migrations
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        migrations = out.getvalue()
    except Exception as e:
        migrations = f'Error: {str(e)}'
    
    diagnostics = {
        'python_version': sys.version,
        'django_version': __import__('django').get_version(),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database': db_info,
        'database_connection': db_connection,
        'database_url_set': 'DATABASE_URL' in os.environ,
        'render_env': os.environ.get('RENDER', 'not set'),
        'render_hostname': os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'not set'),
        'installed_apps': installed_apps,
        'migrations': migrations[:1000] if len(migrations) > 1000 else migrations,
        'static_root': str(settings.STATIC_ROOT),
        'static_url': settings.STATIC_URL,
    }
    
    return JsonResponse(diagnostics, json_dumps_params={'indent': 2})

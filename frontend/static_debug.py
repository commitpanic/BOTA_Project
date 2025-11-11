"""
Debug view for checking static files on Render
"""
from django.http import HttpResponse
from django.conf import settings
import os
from pathlib import Path

def static_files_debug(request):
    """Show information about static files"""
    static_root = Path(settings.STATIC_ROOT)
    
    html = ["<html><head><title>Static Files Debug</title></head><body>"]
    html.append("<h1>Static Files Debug</h1>")
    
    html.append(f"<p><strong>STATIC_ROOT:</strong> {settings.STATIC_ROOT}</p>")
    html.append(f"<p><strong>STATIC_URL:</strong> {settings.STATIC_URL}</p>")
    html.append(f"<p><strong>BASE_DIR:</strong> {settings.BASE_DIR}</p>")
    
    html.append(f"<h2>Checking paths:</h2>")
    html.append(f"<p>static_root exists: {static_root.exists()}</p>")
    
    if static_root.exists():
        html.append("<h3>Contents of staticfiles/:</h3>")
        html.append("<ul>")
        try:
            for item in sorted(static_root.iterdir())[:20]:
                html.append(f"<li>{item.name} ({'DIR' if item.is_dir() else 'FILE'})</li>")
        except Exception as e:
            html.append(f"<li>Error listing: {e}</li>")
        html.append("</ul>")
        
        images_dir = static_root / 'images'
        html.append(f"<p>images/ exists: {images_dir.exists()}</p>")
        
        if images_dir.exists():
            html.append("<h3>Contents of staticfiles/images/:</h3>")
            html.append("<ul>")
            try:
                for item in sorted(images_dir.iterdir()):
                    html.append(f"<li>{item.name} ({item.stat().st_size} bytes)</li>")
            except Exception as e:
                html.append(f"<li>Error listing: {e}</li>")
            html.append("</ul>")
    else:
        html.append("<p style='color: red;'>❌ STATIC_ROOT does not exist!</p>")
    
    html.append("</body></html>")
    
    return HttpResponse('\n'.join(html))

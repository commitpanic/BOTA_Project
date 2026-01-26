import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from bunkers.models import Bunker

# Update first bunker with test info_url
bunker = Bunker.objects.first()
if bunker:
    bunker.info_url = 'https://example.com/bunker-info'
    bunker.save()
    print(f"Updated {bunker.reference_number}")
    print(f"Info URL: {bunker.info_url}")
    print(f"Check: http://127.0.0.1:8000/bunkers/{bunker.reference_number}/")
else:
    print("No bunkers found")

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from bunkers.models import Bunker

bunkers = Bunker.objects.all()[:3]
print(f"Total bunkers: {Bunker.objects.count()}")

for b in bunkers:
    print(f"\nBunker: {b.reference_number}")
    print(f"  Has info_url attr: {hasattr(b, 'info_url')}")
    print(f"  Info URL value: '{b.info_url}'")
    print(f"  Locator: '{b.locator}'")

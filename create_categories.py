"""
Quick script to create default bunker categories
Run with: python create_categories.py
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from bunkers.models import BunkerCategory

# Create default categories
categories = [
    {
        'name_en': 'Military',
        'name_pl': 'Wojskowy',
        'description_en': 'Military bunkers and fortifications',
        'description_pl': 'Bunkry i fortyfikacje wojskowe',
        'display_order': 1
    },
    {
        'name_en': 'Observation',
        'name_pl': 'Obserwacyjny',
        'description_en': 'Observation posts and towers',
        'description_pl': 'Stanowiska i wieże obserwacyjne',
        'display_order': 2
    },
    {
        'name_en': 'Shelter',
        'name_pl': 'Schron',
        'description_en': 'Civilian shelters',
        'description_pl': 'Schrony cywilne',
        'display_order': 3
    },
    {
        'name_en': 'Command',
        'name_pl': 'Dowodzenia',
        'description_en': 'Command and control bunkers',
        'description_pl': 'Bunkry dowodzenia',
        'display_order': 4
    },
]

for cat_data in categories:
    category, created = BunkerCategory.objects.get_or_create(
        name_en=cat_data['name_en'],
        defaults=cat_data
    )
    if created:
        print(f"✓ Created category: {category.name_en} / {category.name_pl}")
    else:
        print(f"• Category already exists: {category.name_en}")

print(f"\nTotal categories: {BunkerCategory.objects.count()}")

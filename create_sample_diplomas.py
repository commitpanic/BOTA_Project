"""
Script to create sample diploma types for BOTA Project
Uruchom: python create_sample_diplomas.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from diplomas.models import DiplomaType

# Usuń istniejące przykładowe dyplomy (opcjonalnie)
# DiplomaType.objects.all().delete()

diplomas_data = [
    # ACTIVATOR DIPLOMAS
    {
        'name_en': 'Activator Bronze',
        'name_pl': 'Brązowy Aktywator',
        'description_en': 'Activate 10 unique bunkers',
        'description_pl': 'Aktywuj 10 różnych bunkrów',
        'category': 'activator',
        'min_activator_points': 10,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'min_unique_activations': 10,
        'is_active': True,
        'display_order': 1,
    },
    {
        'name_en': 'Activator Silver',
        'name_pl': 'Srebrny Aktywator',
        'description_en': 'Activate 25 unique bunkers',
        'description_pl': 'Aktywuj 25 różnych bunkrów',
        'category': 'activator',
        'min_activator_points': 50,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'min_unique_activations': 25,
        'is_active': True,
        'display_order': 2,
    },
    {
        'name_en': 'Activator Gold',
        'name_pl': 'Złoty Aktywator',
        'description_en': 'Activate 50 unique bunkers and make 200 QSOs',
        'description_pl': 'Aktywuj 50 różnych bunkrów i wykonaj 200 QSO',
        'category': 'activator',
        'min_activator_points': 200,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'min_unique_activations': 50,
        'is_active': True,
        'display_order': 3,
    },
    {
        'name_en': 'Activator Platinum',
        'name_pl': 'Platynowy Aktywator',
        'description_en': 'Activate 100 unique bunkers and make 500 QSOs',
        'description_pl': 'Aktywuj 100 różnych bunkrów i wykonaj 500 QSO',
        'category': 'activator',
        'min_activator_points': 500,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'min_unique_activations': 100,
        'is_active': True,
        'display_order': 4,
    },
    
    # HUNTER DIPLOMAS
    {
        'name_en': 'Hunter Bronze',
        'name_pl': 'Brązowy Łowca',
        'description_en': 'Work 10 unique bunkers',
        'description_pl': 'Połącz się z 10 różnymi bunkrami',
        'category': 'hunter',
        'min_activator_points': 0,
        'min_hunter_points': 10,
        'min_b2b_points': 0,
        'min_unique_hunts': 10,
        'is_active': True,
        'display_order': 10,
    },
    {
        'name_en': 'Hunter Silver',
        'name_pl': 'Srebrny Łowca',
        'description_en': 'Work 25 unique bunkers',
        'description_pl': 'Połącz się z 25 różnymi bunkrami',
        'category': 'hunter',
        'min_activator_points': 0,
        'min_hunter_points': 50,
        'min_b2b_points': 0,
        'min_unique_hunts': 25,
        'is_active': True,
        'display_order': 11,
    },
    {
        'name_en': 'Hunter Gold',
        'name_pl': 'Złoty Łowca',
        'description_en': 'Work 50 unique bunkers and make 200 QSOs',
        'description_pl': 'Połącz się z 50 różnymi bunkrami i wykonaj 200 QSO',
        'category': 'hunter',
        'min_activator_points': 0,
        'min_hunter_points': 200,
        'min_b2b_points': 0,
        'min_unique_hunts': 50,
        'is_active': True,
        'display_order': 12,
    },
    {
        'name_en': 'Hunter Platinum',
        'name_pl': 'Platynowy Łowca',
        'description_en': 'Work 100 unique bunkers and make 500 QSOs',
        'description_pl': 'Połącz się z 100 różnymi bunkrami i wykonaj 500 QSO',
        'category': 'hunter',
        'min_activator_points': 0,
        'min_hunter_points': 500,
        'min_b2b_points': 0,
        'min_unique_hunts': 100,
        'is_active': True,
        'display_order': 13,
    },
    
    # B2B DIPLOMAS
    {
        'name_en': 'B2B Starter',
        'name_pl': 'Start B2B',
        'description_en': 'Complete 5 confirmed Bunker-to-Bunker contacts',
        'description_pl': 'Wykonaj 5 potwierdzonych łączności Bunker-to-Bunker',
        'category': 'b2b',
        'min_activator_points': 0,
        'min_hunter_points': 0,
        'min_b2b_points': 5,
        'is_active': True,
        'display_order': 20,
    },
    {
        'name_en': 'B2B Bronze',
        'name_pl': 'Brązowy B2B',
        'description_en': 'Complete 10 confirmed Bunker-to-Bunker contacts',
        'description_pl': 'Wykonaj 10 potwierdzonych łączności Bunker-to-Bunker',
        'category': 'b2b',
        'min_activator_points': 0,
        'min_hunter_points': 0,
        'min_b2b_points': 10,
        'is_active': True,
        'display_order': 21,
    },
    {
        'name_en': 'B2B Silver',
        'name_pl': 'Srebrny B2B',
        'description_en': 'Complete 25 confirmed Bunker-to-Bunker contacts',
        'description_pl': 'Wykonaj 25 potwierdzonych łączności Bunker-to-Bunker',
        'category': 'b2b',
        'min_activator_points': 0,
        'min_hunter_points': 0,
        'min_b2b_points': 25,
        'is_active': True,
        'display_order': 22,
    },
    {
        'name_en': 'B2B Gold',
        'name_pl': 'Złoty B2B',
        'description_en': 'Complete 50 confirmed Bunker-to-Bunker contacts',
        'description_pl': 'Wykonaj 50 potwierdzonych łączności Bunker-to-Bunker',
        'category': 'b2b',
        'min_activator_points': 0,
        'min_hunter_points': 0,
        'min_b2b_points': 50,
        'is_active': True,
        'display_order': 23,
    },
    
    # COMBINED DIPLOMAS (require multiple categories)
    {
        'name_en': 'All-Rounder Bronze',
        'name_pl': 'Brązowy Wszechstronny',
        'description_en': 'Master all three categories: Activator, Hunter and B2B',
        'description_pl': 'Opanuj wszystkie trzy kategorie: Aktywator, Łowca i B2B',
        'category': 'other',
        'min_activator_points': 25,
        'min_hunter_points': 25,
        'min_b2b_points': 5,
        'min_unique_activations': 10,
        'min_unique_hunts': 10,
        'is_active': True,
        'display_order': 30,
    },
    {
        'name_en': 'All-Rounder Silver',
        'name_pl': 'Srebrny Wszechstronny',
        'description_en': 'Advanced mastery of all categories',
        'description_pl': 'Zaawansowane opanowanie wszystkich kategorii',
        'category': 'other',
        'min_activator_points': 100,
        'min_hunter_points': 100,
        'min_b2b_points': 15,
        'min_unique_activations': 25,
        'min_unique_hunts': 25,
        'is_active': True,
        'display_order': 31,
    },
    {
        'name_en': 'All-Rounder Gold',
        'name_pl': 'Złoty Wszechstronny',
        'description_en': 'Elite mastery of all categories',
        'description_pl': 'Elitarne opanowanie wszystkich kategorii',
        'category': 'other',
        'min_activator_points': 250,
        'min_hunter_points': 250,
        'min_b2b_points': 30,
        'min_unique_activations': 50,
        'min_unique_hunts': 50,
        'is_active': True,
        'display_order': 32,
    },
    
    # SPECIAL EVENT DIPLOMAS
    {
        'name_en': 'First Contact',
        'name_pl': 'Pierwszy Kontakt',
        'description_en': 'Complete your first bunker activation',
        'description_pl': 'Wykonaj swoją pierwszą aktywację bunkra',
        'category': 'special_event',
        'min_activator_points': 1,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'is_active': True,
        'display_order': 40,
    },
    {
        'name_en': 'Weekend Warrior',
        'name_pl': 'Wojownik Weekendowy',
        'description_en': 'Activate 5 bunkers in a single weekend',
        'description_pl': 'Aktywuj 5 bunkrów w jeden weekend',
        'category': 'special_event',
        'min_activator_points': 15,
        'min_hunter_points': 0,
        'min_b2b_points': 0,
        'min_unique_activations': 5,
        'is_active': True,
        'display_order': 41,
    },
]

print("Creating sample diploma types...")
print("=" * 60)

created_count = 0
updated_count = 0

for diploma_data in diplomas_data:
    diploma, created = DiplomaType.objects.update_or_create(
        name_en=diploma_data['name_en'],
        defaults=diploma_data
    )
    
    if created:
        created_count += 1
        print(f"✓ Created: {diploma.name_en} ({diploma.get_category_display()})")
    else:
        updated_count += 1
        print(f"↻ Updated: {diploma.name_en} ({diploma.get_category_display()})")

print("=" * 60)
print(f"\nSummary:")
print(f"  Created: {created_count} diplomas")
print(f"  Updated: {updated_count} diplomas")
print(f"  Total:   {created_count + updated_count} diplomas")
print("\n✓ All diploma types created successfully!")
print("\nYou can now:")
print("  1. View them in admin: http://127.0.0.1:8000/admin/diplomas/diplomatype/")
print("  2. Check API: http://127.0.0.1:8000/api/diplomas/types/")
print("  3. See progress on dashboard")

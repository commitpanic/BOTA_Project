"""
Management command to create example diploma types
"""
from django.core.management.base import BaseCommand
from diplomas.models import DiplomaType


class Command(BaseCommand):
    help = 'Create example diploma types with various requirement combinations'

    def handle(self, *args, **options):
        """Create example diploma types"""
        
        diploma_data = [
            {
                'name_pl': 'Eksplorator',
                'name_en': 'Explorer',
                'description_pl': 'Dla operatorów, którzy aktywowali co najmniej 10 różnych bunkrów',
                'description_en': 'For operators who activated at least 10 different bunkers',
                'category': 'activator',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 10,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Maratończyk',
                'name_en': 'Marathon',
                'description_pl': 'Dla operatorów z co najmniej 50 aktywacjami (łącznie)',
                'description_en': 'For operators with at least 50 activations (total)',
                'category': 'activator',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 50,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Aktywator Brązowy',
                'name_en': 'Activator Bronze',
                'description_pl': 'Dla operatorów z minimum 50 punktami aktywatora',
                'description_en': 'For operators with minimum 50 activator points',
                'category': 'activator',
                'min_activator_points': 50,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Aktywator Srebrny',
                'name_en': 'Activator Silver',
                'description_pl': 'Dla operatorów z minimum 150 punktami aktywatora',
                'description_en': 'For operators with minimum 150 activator points',
                'category': 'activator',
                'min_activator_points': 150,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Aktywator Złoty',
                'name_en': 'Activator Gold',
                'description_pl': 'Dla operatorów z minimum 300 punktami aktywatora',
                'description_en': 'For operators with minimum 300 activator points',
                'category': 'activator',
                'min_activator_points': 300,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Łowca Brązowy',
                'name_en': 'Hunter Bronze',
                'description_pl': 'Dla operatorów z minimum 50 punktami łowcy',
                'description_en': 'For operators with minimum 50 hunter points',
                'category': 'hunter',
                'min_activator_points': 0,
                'min_hunter_points': 50,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Łowca Srebrny',
                'name_en': 'Hunter Silver',
                'description_pl': 'Dla operatorów z minimum 150 punktami łowcy',
                'description_en': 'For operators with minimum 150 hunter points',
                'category': 'hunter',
                'min_activator_points': 0,
                'min_hunter_points': 150,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Łowca Złoty',
                'name_en': 'Hunter Gold',
                'description_pl': 'Dla operatorów z minimum 300 punktami łowcy',
                'description_en': 'For operators with minimum 300 hunter points',
                'category': 'hunter',
                'min_activator_points': 0,
                'min_hunter_points': 300,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Mistrz Łowca',
                'name_en': 'Hunter Master',
                'description_pl': 'Dla operatorów z 100 punktami łowcy i 50 unikalnymi łowami',
                'description_en': 'For operators with 100 hunter points and 50 unique hunted bunkers',
                'category': 'hunter',
                'min_activator_points': 0,
                'min_hunter_points': 100,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 50,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'B2B Brązowy',
                'name_en': 'B2B Bronze',
                'description_pl': 'Dla operatorów z minimum 25 punktami B2B',
                'description_en': 'For operators with minimum 25 B2B points',
                'category': 'b2b',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 25,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'B2B Srebrny',
                'name_en': 'B2B Silver',
                'description_pl': 'Dla operatorów z minimum 75 punktami B2B',
                'description_en': 'For operators with minimum 75 B2B points',
                'category': 'b2b',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 75,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'B2B Złoty',
                'name_en': 'B2B Gold',
                'description_pl': 'Dla operatorów z minimum 150 punktami B2B',
                'description_en': 'For operators with minimum 150 B2B points',
                'category': 'b2b',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 150,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Wszechstronny',
                'name_en': 'Versatile',
                'description_pl': 'Dla operatorów aktywnych we wszystkich kategoriach: 30 pkt aktywatora, 30 pkt łowcy, 15 pkt B2B',
                'description_en': 'For operators active in all categories: 30 activator pts, 30 hunter pts, 15 B2B pts',
                'category': 'mixed',
                'min_activator_points': 30,
                'min_hunter_points': 30,
                'min_b2b_points': 15,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Odkrywca',
                'name_en': 'Discoverer',
                'description_pl': 'Dla operatorów, którzy odkryli 25 unikalnych bunkrów (jako łowca)',
                'description_en': 'For operators who discovered 25 unique bunkers (as hunter)',
                'category': 'hunter',
                'min_activator_points': 0,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 0,
                'min_total_activations': 0,
                'min_unique_hunted': 25,
                'min_total_hunted': 0,
                'is_active': True,
            },
            {
                'name_pl': 'Super Aktywator',
                'name_en': 'Super Activator',
                'description_pl': 'Dla operatorów z 200 pkt aktywatora i 20 unikalnymi aktywacjami',
                'description_en': 'For operators with 200 activator pts and 20 unique activations',
                'category': 'activator',
                'min_activator_points': 200,
                'min_hunter_points': 0,
                'min_b2b_points': 0,
                'min_unique_activations': 20,
                'min_total_activations': 0,
                'min_unique_hunted': 0,
                'min_total_hunted': 0,
                'is_active': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in diploma_data:
            diploma, created = DiplomaType.objects.update_or_create(
                name_en=data['name_en'],
                defaults=data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {diploma.name_en}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {diploma.name_en}')
                )
        
        self.stdout.write('\n')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(diploma_data)} diploma types')
        )
        self.stdout.write(f'  • Created: {created_count}')
        self.stdout.write(f'  • Updated: {updated_count}')
        self.stdout.write('\n')
        self.stdout.write('You can now view these diplomas in the admin at /admin/diplomas/diplomatype/')

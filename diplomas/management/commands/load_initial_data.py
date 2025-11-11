"""
Management command to load initial data for BOTA Project
Creates diploma types and bunker categories
"""
from django.core.management.base import BaseCommand
from diplomas.models import DiplomaType
from bunkers.models import BunkerCategory


class Command(BaseCommand):
    help = 'Load initial data (diploma types and bunker categories) for BOTA Project'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading initial data...'))
        
        # Create Bunker Categories
        self.stdout.write('\n=== Creating Bunker Categories ===')
        categories_created = 0
        
        bunker_categories = [
            {
                'name_en': 'Fortification',
                'name_pl': 'Fortyfikacja',
                'description_en': 'Military fortifications and defensive structures',
                'description_pl': 'Fortyfikacje wojskowe i struktury obronne',
            },
            {
                'name_en': 'Bunker',
                'name_pl': 'Schron',
                'description_en': 'Underground or reinforced bunkers',
                'description_pl': 'Podziemne lub wzmocnione schrony',
            },
            {
                'name_en': 'Military Building',
                'name_pl': 'Obiekt Wojskowy',
                'description_en': 'Military buildings and barracks',
                'description_pl': 'Budynki wojskowe i koszary',
            },
            {
                'name_en': 'Artillery Position',
                'name_pl': 'Stanowisko Artylerii',
                'description_en': 'Artillery positions and gun emplacements',
                'description_pl': 'Stanowiska artylerii i działa',
            },
            {
                'name_en': 'Command Post',
                'name_pl': 'Stanowisko Dowodzenia',
                'description_en': 'Command posts and headquarters',
                'description_pl': 'Stanowiska dowodzenia i kwatery główne',
            },
        ]
        
        for cat_data in bunker_categories:
            category, created = BunkerCategory.objects.get_or_create(
                name_en=cat_data['name_en'],
                defaults=cat_data
            )
            if created:
                categories_created += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {category.name_en} / {category.name_pl}'))
            else:
                self.stdout.write(f'  - Exists: {category.name_en}')
        
        self.stdout.write(self.style.SUCCESS(f'\nCreated {categories_created} bunker categories'))
        
        # Create Diploma Types
        self.stdout.write('\n=== Creating Diploma Types ===')
        diplomas_created = 0
        
        diploma_types = [
            # Activator Diplomas
            {
                'category': 'activator',
                'name_en': 'Bronze Activator',
                'name_pl': 'Brązowy Aktywator',
                'description_en': 'Activate 5 different bunkers',
                'description_pl': 'Aktywuj 5 różnych bunkrów',
                'display_order': 1,
                'min_unique_activations': 5,
                'is_active': True,
            },
            {
                'category': 'activator',
                'name_en': 'Silver Activator',
                'name_pl': 'Srebrny Aktywator',
                'description_en': 'Activate 10 different bunkers',
                'description_pl': 'Aktywuj 10 różnych bunkrów',
                'display_order': 2,
                'min_unique_activations': 10,
                'is_active': True,
            },
            {
                'category': 'activator',
                'name_en': 'Gold Activator',
                'name_pl': 'Złoty Aktywator',
                'description_en': 'Activate 25 different bunkers',
                'description_pl': 'Aktywuj 25 różnych bunkrów',
                'display_order': 3,
                'min_unique_activations': 25,
                'is_active': True,
            },
            {
                'category': 'activator',
                'name_en': 'Platinum Activator',
                'name_pl': 'Platynowy Aktywator',
                'description_en': 'Activate 50 different bunkers',
                'description_pl': 'Aktywuj 50 różnych bunkrów',
                'display_order': 4,
                'min_unique_activations': 50,
                'is_active': True,
            },
            {
                'category': 'activator',
                'name_en': 'Diamond Activator',
                'name_pl': 'Diamentowy Aktywator',
                'description_en': 'Activate 100 different bunkers',
                'description_pl': 'Aktywuj 100 różnych bunkrów',
                'display_order': 5,
                'min_unique_activations': 100,
                'is_active': True,
            },
            
            # Hunter Diplomas
            {
                'category': 'hunter',
                'name_en': 'Bronze Hunter',
                'name_pl': 'Brązowy Łowca',
                'description_en': 'Work 5 different bunkers',
                'description_pl': 'Połącz się z 5 różnymi bunkremi',
                'display_order': 1,
                'min_unique_hunted': 5,
                'is_active': True,
            },
            {
                'category': 'hunter',
                'name_en': 'Silver Hunter',
                'name_pl': 'Srebrny Łowca',
                'description_en': 'Work 10 different bunkers',
                'description_pl': 'Połącz się z 10 różnymi bunkremi',
                'display_order': 2,
                'min_unique_hunted': 10,
                'is_active': True,
            },
            {
                'category': 'hunter',
                'name_en': 'Gold Hunter',
                'name_pl': 'Złoty Łowca',
                'description_en': 'Work 25 different bunkers',
                'description_pl': 'Połącz się z 25 różnymi bunkremi',
                'display_order': 3,
                'min_unique_hunted': 25,
                'is_active': True,
            },
            {
                'category': 'hunter',
                'name_en': 'Platinum Hunter',
                'name_pl': 'Platynowy Łowca',
                'description_en': 'Work 50 different bunkers',
                'description_pl': 'Połącz się z 50 różnymi bunkremi',
                'display_order': 4,
                'min_unique_hunted': 50,
                'is_active': True,
            },
            {
                'category': 'hunter',
                'name_en': 'Diamond Hunter',
                'name_pl': 'Diamentowy Łowca',
                'description_en': 'Work 100 different bunkers',
                'description_pl': 'Połącz się z 100 różnymi bunkremi',
                'display_order': 5,
                'min_unique_hunted': 100,
                'is_active': True,
            },
            
            # B2B Diplomas
            {
                'category': 'b2b',
                'name_en': 'B2B Enthusiast',
                'name_pl': 'Entuzjasta B2B',
                'description_en': 'Complete 10 bunker-to-bunker QSOs',
                'description_pl': 'Zrealizuj 10 łączności bunker-bunker',
                'display_order': 1,
                'min_activator_points': 10,
                'is_active': True,
            },
            {
                'category': 'b2b',
                'name_en': 'B2B Expert',
                'name_pl': 'Ekspert B2B',
                'description_en': 'Complete 25 bunker-to-bunker QSOs',
                'description_pl': 'Zrealizuj 25 łączności bunker-bunker',
                'display_order': 2,
                'min_activator_points': 25,
                'is_active': True,
            },
            {
                'category': 'b2b',
                'name_en': 'B2B Master',
                'name_pl': 'Mistrz B2B',
                'description_en': 'Complete 50 bunker-to-bunker QSOs',
                'description_pl': 'Zrealizuj 50 łączności bunker-bunker',
                'display_order': 3,
                'min_activator_points': 50,
                'is_active': True,
            },
            
            # Cluster Diplomas
            {
                'category': 'cluster',
                'name_en': 'Cluster Explorer',
                'name_pl': 'Odkrywca Klastra',
                'description_en': 'Activate or work all bunkers in one cluster',
                'description_pl': 'Aktywuj lub połącz się ze wszystkimi bunkremi w jednym klastrze',
                'display_order': 1,
                'min_activator_points': 5,
                'min_hunter_points': 5,
                'is_active': True,
            },
            {
                'category': 'cluster',
                'name_en': 'Multi-Cluster',
                'name_pl': 'Multi-Klaster',
                'description_en': 'Complete 3 different clusters',
                'description_pl': 'Ukończ 3 różne klastry',
                'display_order': 2,
                'min_activator_points': 15,
                'min_hunter_points': 15,
                'is_active': True,
            },
            
            # Special Event Diplomas
            {
                'category': 'special_event',
                'name_en': 'BOTA Day Participant',
                'name_pl': 'Uczestnik Dnia BOTA',
                'description_en': 'Participate in special BOTA Day event',
                'description_pl': 'Weź udział w specjalnym wydarzeniu Dzień BOTA',
                'display_order': 1,
                'min_activator_points': 1,
                'is_active': False,  # Inactive until event
            },
            {
                'category': 'special_event',
                'name_en': 'Anniversary Edition',
                'name_pl': 'Edycja Rocznicowa',
                'description_en': 'Participate in BOTA anniversary event',
                'description_pl': 'Weź udział w wydarzeniu rocznicowym BOTA',
                'display_order': 2,
                'min_activator_points': 1,
                'is_active': False,  # Inactive until event
            },
        ]
        
        for diploma_data in diploma_types:
            diploma, created = DiplomaType.objects.get_or_create(
                category=diploma_data['category'],
                name_en=diploma_data['name_en'],
                defaults=diploma_data
            )
            if created:
                diplomas_created += 1
                status = "✓" if diploma.is_active else "○"
                self.stdout.write(self.style.SUCCESS(
                    f'  {status} Created: {diploma.category.upper()}: {diploma.name_en} / {diploma.name_pl}'
                ))
            else:
                self.stdout.write(f'  - Exists: {diploma.name_en}')
        
        self.stdout.write(self.style.SUCCESS(f'\nCreated {diplomas_created} diploma types'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('INITIAL DATA LOADED SUCCESSFULLY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total Bunker Categories: {BunkerCategory.objects.count()}')
        self.stdout.write(f'Total Diploma Types: {DiplomaType.objects.count()}')
        self.stdout.write(f'  - Activator: {DiplomaType.objects.filter(category="activator").count()}')
        self.stdout.write(f'  - Hunter: {DiplomaType.objects.filter(category="hunter").count()}')
        self.stdout.write(f'  - B2B: {DiplomaType.objects.filter(category="b2b").count()}')
        self.stdout.write(f'  - Cluster: {DiplomaType.objects.filter(category="cluster").count()}')
        self.stdout.write(f'  - Special Event: {DiplomaType.objects.filter(category="special_event").count()}')
        self.stdout.write('\n' + self.style.SUCCESS('✓ All done!'))

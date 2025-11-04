"""
Management command to import bunkers from CSV file
CSV format: Reference,Name,Type,Lat,Long,Locator
Example: B/SP-0001,A Pz.W. Nord,WW2 Battle Bunker,52.355094,15.467441,JO72RI
"""
import csv
from django.core.management.base import BaseCommand, CommandError
from bunkers.models import Bunker, BunkerCategory
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import bunkers from CSV file (Reference,Name,Type,Lat,Long,Locator)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--skip-header',
            action='store_true',
            help='Skip first row (header)',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        skip_header = options['skip_header']
        
        # Get or create default category
        default_category, created = BunkerCategory.objects.get_or_create(
            name_en='WW2 Bunker',
            defaults={
                'name_pl': 'Bunkier z II WŚ',
                'description_en': 'World War 2 fortification',
                'description_pl': 'Fortyfikacja z czasów II Wojny Światowej',
                'icon': 'fas fa-shield-alt'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created default category: {default_category}'))
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Skip header if requested
                if skip_header:
                    next(reader)
                
                created_count = 0
                updated_count = 0
                error_count = 0
                
                for row_num, row in enumerate(reader, start=1):
                    if len(row) < 5:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Skipping incomplete row')
                        )
                        error_count += 1
                        continue
                    
                    reference = row[0].strip()
                    name = row[1].strip()
                    bunker_type = row[2].strip()
                    
                    try:
                        lat = Decimal(row[3].strip())
                        lon = Decimal(row[4].strip())
                    except (ValueError, IndexError):
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Invalid coordinates for {reference}')
                        )
                        error_count += 1
                        continue
                    
                    # Locator is optional
                    locator = row[5].strip() if len(row) > 5 else ''
                    
                    # Check if bunker exists
                    bunker, created = Bunker.objects.update_or_create(
                        reference_number=reference,
                        defaults={
                            'name_en': name,
                            'name_pl': name,  # Use same name for both languages
                            'description_en': f'{bunker_type}. Locator: {locator}' if locator else bunker_type,
                            'description_pl': f'{bunker_type}. Lokator: {locator}' if locator else bunker_type,
                            'category': default_category,
                            'latitude': lat,
                            'longitude': lon,
                            'is_verified': True,  # Auto-verify imported bunkers
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {reference} - {name}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated: {reference} - {name}')
                        )
                
                # Summary
                self.stdout.write(self.style.SUCCESS('\n' + '='*50))
                self.stdout.write(self.style.SUCCESS(f'Import completed!'))
                self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
                self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
                if error_count > 0:
                    self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
                self.stdout.write(self.style.SUCCESS('='*50))
                
        except FileNotFoundError:
            raise CommandError(f'File "{csv_file}" not found')
        except Exception as e:
            raise CommandError(f'Error processing CSV: {str(e)}')

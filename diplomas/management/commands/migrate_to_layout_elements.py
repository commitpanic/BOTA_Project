from django.core.management.base import BaseCommand
from diplomas.models import DiplomaType


class Command(BaseCommand):
    help = 'Migrate old layout_config JSON to DiplomaLayoutElement objects'

    def handle(self, *args, **options):
        diploma_types = DiplomaType.objects.all()
        migrated_count = 0
        
        for diploma_type in diploma_types:
            # Check if already has layout elements
            if diploma_type.layout_elements.exists():
                self.stdout.write(
                    self.style.WARNING(f'Skipping {diploma_type.name_en} - already has layout elements')
                )
                continue
            
            # Migrate old config
            try:
                diploma_type.migrate_old_layout_config()
                diploma_type.save()
                migrated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Migrated {diploma_type.name_en}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to migrate {diploma_type.name_en}: {str(e)}')
                )
        
        if migrated_count == 0:
            self.stdout.write(self.style.SUCCESS('No diploma types needed migration'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully migrated {migrated_count} diploma type(s)')
            )

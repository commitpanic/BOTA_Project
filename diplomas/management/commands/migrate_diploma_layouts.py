"""
Management command to migrate old diploma layout configs to new format
"""

from django.core.management.base import BaseCommand
from diplomas.models import DiplomaType


class Command(BaseCommand):
    help = 'Migrate old flat layout_config format to new nested format'

    def handle(self, *args, **options):
        diploma_types = DiplomaType.objects.all()
        migrated_count = 0
        
        for diploma_type in diploma_types:
            if diploma_type.layout_config:
                # Store original
                original = dict(diploma_type.layout_config)
                
                # Try migration
                diploma_type.migrate_old_layout_config()
                
                # Check if changed
                if diploma_type.layout_config != original:
                    diploma_type.save()
                    migrated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Migrated layout config for "{diploma_type.name_en}"'
                        )
                    )
        
        if migrated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No diploma types needed migration')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully migrated {migrated_count} diploma type(s)'
                )
            )

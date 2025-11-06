#!/usr/bin/env python
"""
Compile .po files to .mo files without requiring gettext tools
"""
import os
from django.core.management import execute_from_command_line

# Translation files to compile
translation_files = [
    ('locale/pl/LC_MESSAGES/django.po', 'locale/pl/LC_MESSAGES/django.mo'),
    ('planned_activations/locale/pl/LC_MESSAGES/django.po', 'planned_activations/locale/pl/LC_MESSAGES/django.mo')
]

# Try to compile using polib
try:
    import polib
    
    success_count = 0
    for po_file, mo_file in translation_files:
        if os.path.exists(po_file):
            print(f"Compiling {po_file}...")
            po = polib.pofile(po_file)
            po.save_as_mofile(mo_file)
            print(f"Successfully compiled to {mo_file}")
            success_count += 1
        else:
            print(f"Warning: {po_file} not found, skipping...")
    
    print(f"\n✓ {success_count} translation file(s) compiled successfully!")
    print("Please restart your Django development server for changes to take effect.")
    
except ImportError:
    print("polib not installed. Installing...")
    os.system('D:/BOTA/.venv/Scripts/pip.exe install polib')
    
    import polib
    success_count = 0
    for po_file, mo_file in translation_files:
        if os.path.exists(po_file):
            print(f"Compiling {po_file}...")
            po = polib.pofile(po_file)
            po.save_as_mofile(mo_file)
            print(f"Successfully compiled to {mo_file}")
            success_count += 1
        else:
            print(f"Warning: {po_file} not found, skipping...")
    
    print(f"\n✓ {success_count} translation file(s) compiled successfully!")
    print("Please restart your Django development server for changes to take effect.")

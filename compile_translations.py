#!/usr/bin/env python
"""
Compile .po file to .mo file without requiring gettext tools
"""
import os
from django.core.management import execute_from_command_line

# Try to compile using Django's built-in method
try:
    import polib
    
    po_file = 'locale/pl/LC_MESSAGES/django.po'
    mo_file = 'locale/pl/LC_MESSAGES/django.mo'
    
    print(f"Compiling {po_file}...")
    po = polib.pofile(po_file)
    po.save_as_mofile(mo_file)
    print(f"Successfully compiled to {mo_file}")
    
except ImportError:
    print("polib not installed. Installing...")
    os.system('D:/BOTA/.venv/Scripts/pip.exe install polib')
    
    import polib
    po_file = 'locale/pl/LC_MESSAGES/django.po'
    mo_file = 'locale/pl/LC_MESSAGES/django.mo'
    
    print(f"Compiling {po_file}...")
    po = polib.pofile(po_file)
    po.save_as_mofile(mo_file)
    print(f"Successfully compiled to {mo_file}")

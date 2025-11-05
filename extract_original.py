# -*- coding: utf-8 -*-
"""
Extract original translations before Cookie Policy
"""
import re

# Read the broken file  
with open('locale/pl/LC_MESSAGES/django.po.broken', 'r', encoding='utf-8') as f:
    content = f.read()

# Find content before our Cookie Policy additions
match = re.search(r'# Cookie Policy', content)
if match:
    original = content[:match.start()]
    # Fix double-escaped quotes back to normal  
    original = original.replace('\\\\"', '"')
    print(f'✅ Extracted {len(original)} chars of original translations')
    print(f'📝 Found original content ending at position {match.start()}')
    
    with open('locale/pl/LC_MESSAGES/django_original_clean.po', 'w', encoding='utf-8') as f:
        f.write(original)
    print(f'💾 Saved to django_original_clean.po')
else:
    print('❌ Cookie Policy marker not found')

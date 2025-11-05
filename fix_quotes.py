# -*- coding: utf-8 -*-
"""
Fix curly quotes in django.po
Replace typographic quotes ""'' with straight quotes ""''
"""

# Read the file
with open('locale/pl/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace curly quotes with straight quotes
content = content.replace('"', '\\"')  # LEFT DOUBLE QUOTATION MARK (U+201C)
content = content.replace('"', '\\"')  # RIGHT DOUBLE QUOTATION MARK (U+201D)
content = content.replace(''', "\\'")  # LEFT SINGLE QUOTATION MARK (U+2018)
content = content.replace(''', "\\'")  # RIGHT SINGLE QUOTATION MARK (U+2019)

# Write back
with open('locale/pl/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all curly quotes!")
print("🔍 Replaced curly quotes with escaped straight quotes")

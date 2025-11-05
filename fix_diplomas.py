#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix progress bars in diplomas.html"""

import re

# Read the file
with open(r'd:\DEV\BOTA_Project\templates\diplomas.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the old progress-bar format
old_pattern = r'<div class="progress-bar {% if progress\.percentage_complete >= 75 %}bg-success{% elif progress\.percentage_complete >= 50 %}bg-info{% elif progress\.percentage_complete >= 25 %}bg-warning{% endif %}" \s+role="progressbar" \s+style="width: {{ progress\.percentage_complete }}%"'

# New format with inline colors and stringformat
new_format = r'<div class="progress-bar" \n                         role="progressbar" \n                         style="width: {{ progress.percentage_complete|stringformat:"d" }}%; background-color: {% if progress.percentage_complete >= 75 %}#28a745{% elif progress.percentage_complete >= 50 %}#17a2b8{% elif progress.percentage_complete >= 25 %}#ffc107{% else %}#6c757d{% endif %};"'

# Replace all occurrences
new_content = re.sub(old_pattern, new_format, content)

# Write back
with open(r'd:\DEV\BOTA_Project\templates\diplomas.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed diplomas.html - replaced progress bars with inline colors and stringformat")

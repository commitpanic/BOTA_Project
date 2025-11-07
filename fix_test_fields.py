#!/usr/bin/env python3
"""Fix test_point_logic.py by removing invalid model fields"""
import re

input_file = 'd:\\BOTA\\BOTA_Project\\activations\\tests\\test_point_logic.py'
output_file = 'd:\\BOTA\\BOTA_Project\\activations\\tests\\test_point_logic_fixed.py'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove invalid ActivationLog fields
content = re.sub(r",\s*frequency='[^']*'", '', content)
content = re.sub(r",\s*rst_sent='[^']*'", '', content)
content = re.sub(r",\s*rst_rcvd='[^']*'", '', content)

# Remove invalid Bunker fields (but keep category field)
content = re.sub(r",\s*type='[^']*'", '', content)
content = re.sub(r",\s*status='[^']*'", '', content)
content = re.sub(r",\s*submitted_by=self\.\w+", '', content)

# Add category=self.category to Bunker.objects.create where it's missing
content = re.sub(
    r'(bunker2 = Bunker\.objects\.create\([^)]*?)(latitude=)',
    r'\1category=self.category,\n            \2',
    content
)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed file saved to: {output_file}")

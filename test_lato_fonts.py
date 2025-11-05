#!/usr/bin/env python
"""
Test if Lato fonts work correctly with Polish characters
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')

import django
django.setup()

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings

def test_lato_fonts():
    """Test Lato fonts with Polish characters"""
    
    # Register fonts
    fonts_dir = Path(settings.BASE_DIR) / 'static' / 'fonts'
    
    print("Testing Lato fonts...")
    print(f"Fonts directory: {fonts_dir}")
    print()
    
    # Check if fonts exist
    fonts = {
        'Lato': 'Lato-Regular.ttf',
        'Lato-Bold': 'Lato-Bold.ttf',
        'Lato-Italic': 'Lato-Italic.ttf',
        'Lato-BoldItalic': 'Lato-BoldItalic.ttf',
    }
    
    for font_name, font_file in fonts.items():
        font_path = fonts_dir / font_file
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            print(f"✓ Registered {font_name}")
        else:
            print(f"✗ Missing {font_file}")
    
    print()
    
    # Create test PDF
    output_file = fonts_dir / 'test_polish_characters.pdf'
    c = canvas.Canvas(str(output_file), pagesize=A4)
    
    # Polish test text
    polish_text = "Test polskich znaków: ą ć ę ł ń ó ś ź ż Ą Ć Ę Ł Ń Ó Ś Ź Ż"
    
    y_position = 25*cm
    
    c.setFont("Lato", 16)
    c.drawString(2*cm, y_position, "Lato Regular:")
    y_position -= 1*cm
    c.drawString(2*cm, y_position, polish_text)
    y_position -= 2*cm
    
    c.setFont("Lato-Bold", 16)
    c.drawString(2*cm, y_position, "Lato Bold:")
    y_position -= 1*cm
    c.drawString(2*cm, y_position, polish_text)
    y_position -= 2*cm
    
    c.setFont("Lato-Italic", 16)
    c.drawString(2*cm, y_position, "Lato Italic:")
    y_position -= 1*cm
    c.drawString(2*cm, y_position, polish_text)
    y_position -= 2*cm
    
    c.setFont("Lato-BoldItalic", 16)
    c.drawString(2*cm, y_position, "Lato Bold Italic:")
    y_position -= 1*cm
    c.drawString(2*cm, y_position, polish_text)
    
    c.save()
    
    print(f"✓ Test PDF created: {output_file}")
    print()
    print("Open the PDF to verify Polish characters render correctly.")

if __name__ == '__main__':
    test_lato_fonts()

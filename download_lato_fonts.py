#!/usr/bin/env python
"""
Download Lato fonts from Google Fonts for PDF generation
"""
import urllib.request
import os
from pathlib import Path

# Font URLs from Google Fonts (direct links to TTF files)
LATO_FONTS = {
    'Lato-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf',
    'Lato-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf',
    'Lato-Italic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Italic.ttf',
    'Lato-BoldItalic.ttf': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-BoldItalic.ttf',
}

def download_fonts():
    """Download Lato fonts to static/fonts directory"""
    fonts_dir = Path(__file__).parent / 'static' / 'fonts'
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading Lato fonts from Google Fonts repository...")
    print(f"Target directory: {fonts_dir}")
    print()
    
    for filename, url in LATO_FONTS.items():
        output_path = fonts_dir / filename
        
        if output_path.exists():
            print(f"✓ {filename} already exists, skipping")
            continue
        
        try:
            print(f"Downloading {filename}...", end=' ')
            urllib.request.urlretrieve(url, output_path)
            
            # Verify file was downloaded
            if output_path.exists() and output_path.stat().st_size > 0:
                size_kb = output_path.stat().st_size / 1024
                print(f"✓ Done ({size_kb:.1f} KB)")
            else:
                print(f"✗ Failed (file is empty or missing)")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print()
    print("=" * 60)
    print("Font installation complete!")
    print("=" * 60)
    print()
    print("Installed fonts:")
    for font_file in fonts_dir.glob('*.ttf'):
        size_kb = font_file.stat().st_size / 1024
        print(f"  • {font_file.name} ({size_kb:.1f} KB)")

if __name__ == '__main__':
    download_fonts()

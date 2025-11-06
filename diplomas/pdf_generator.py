"""
PDF Generation Utilities for Diploma Certificates
Handles font registration, layout configuration, and PDF rendering
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode
from io import BytesIO
from pathlib import Path
from django.conf import settings


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-1 range for reportlab)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def register_fonts(diploma_type):
    """Register all fonts (built-in + custom uploaded fonts)"""
    from .models import FontFile
    
    registered_fonts = {}
    
    # Register built-in Lato fonts
    try:
        fonts_dir = Path(settings.BASE_DIR) / 'static' / 'fonts'
        lato_regular = fonts_dir / 'Lato-Regular.ttf'
        lato_bold = fonts_dir / 'Lato-Bold.ttf'
        
        if lato_regular.exists():
            pdfmetrics.registerFont(TTFont('Lato', str(lato_regular)))
            registered_fonts['Lato'] = True
        if lato_bold.exists():
            pdfmetrics.registerFont(TTFont('Lato-Bold', str(lato_bold)))
            registered_fonts['Lato-Bold'] = True
    except Exception:
        pass
    
    # Register custom uploaded fonts
    try:
        custom_fonts = FontFile.objects.filter(is_active=True)
        for font in custom_fonts:
            try:
                font_name = font.get_font_family_name()
                pdfmetrics.registerFont(TTFont(font_name, font.font_file.path))
                registered_fonts[font_name] = True
            except Exception:
                pass
    except Exception:
        pass
    
    return registered_fonts


def get_font_name(element_config, registered_fonts):
    """Get appropriate font name based on config and availability"""
    font = element_config.get('font', 'Lato')
    bold = element_config.get('bold', False)
    italic = element_config.get('italic', False)
    
    # Try specific variant first
    if bold and italic:
        font_variant = f"{font}-BoldItalic"
        if font_variant in registered_fonts:
            return font_variant
    elif bold:
        font_variant = f"{font}-Bold"
        if font_variant in registered_fonts:
            return font_variant
    elif italic:
        font_variant = f"{font}-Italic"
        if font_variant in registered_fonts:
            return font_variant
    
    # Fallback to base font
    if font in registered_fonts:
        return font
    
    # Ultimate fallback
    if bold:
        return 'Helvetica-Bold'
    elif italic:
        return 'Helvetica-Oblique'
    return 'Helvetica'


def draw_text_element(c, element_config, text, registered_fonts):
    """Draw a text element with full styling"""
    if not element_config.get('enabled', True):
        return
    
    # Get position
    x = element_config.get('x', 14.5) * cm
    y = element_config.get('y', 10) * cm
    
    # Get font
    font_name = get_font_name(element_config, registered_fonts)
    font_size = element_config.get('size', 12)
    
    # Get color
    color = element_config.get('color', '#333333')
    r, g, b = hex_to_rgb(color)
    
    # Apply styling and draw
    c.setFont(font_name, font_size)
    c.setFillColorRGB(r, g, b)
    c.drawCentredString(x, y, text)


def generate_diploma_pdf(diploma_type, callsign, diploma_name, date_text, points_text, diploma_number, verification_url, is_preview=False):
    """
    Generate diploma PDF with advanced customization
    
    Args:
        diploma_type: DiplomaType instance
        callsign: User's callsign
        diploma_name: Diploma type name
        date_text: Formatted date string
        points_text: Formatted points string  
        diploma_number: Unique diploma number
        verification_url: Full URL for QR code
        is_preview: If True, adds PREVIEW watermark
    
    Returns:
        BytesIO buffer containing PDF data
    """
    # Create PDF buffer
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Register all fonts
    registered_fonts = register_fonts(diploma_type)
    
    # Get merged layout configuration
    layout = diploma_type.get_merged_layout_config()
    
    # Draw background image if exists
    if diploma_type.template_image:
        try:
            img = ImageReader(diploma_type.template_image.path)
            c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=False)
        except Exception:
            # If image fails, draw decorative border
            c.setStrokeColorRGB(0.1, 0.33, 0.56)
            c.setLineWidth(3)
            c.rect(1*cm, 1*cm, width-2*cm, height-2*cm)
            c.setStrokeColorRGB(0.17, 0.35, 0.63)
            c.setLineWidth(1)
            c.rect(1.5*cm, 1.5*cm, width-3*cm, height-3*cm)
    else:
        # No background - draw decorative border
        c.setStrokeColorRGB(0.1, 0.33, 0.56)
        c.setLineWidth(3)
        c.rect(1*cm, 1*cm, width-2*cm, height-2*cm)
        c.setStrokeColorRGB(0.17, 0.35, 0.63)
        c.setLineWidth(1)
        c.rect(1.5*cm, 1.5*cm, width-3*cm, height-3*cm)
    
    # Draw callsign
    if 'callsign' in layout:
        draw_text_element(c, layout['callsign'], callsign, registered_fonts)
    
    # Draw diploma name
    if 'diploma_name' in layout:
        draw_text_element(c, layout['diploma_name'], diploma_name, registered_fonts)
    
    # Draw date
    if 'date' in layout:
        draw_text_element(c, layout['date'], date_text, registered_fonts)
    
    # Draw points
    if 'points' in layout and points_text:
        draw_text_element(c, layout['points'], points_text, registered_fonts)
    
    # Draw diploma number
    if 'diploma_number' in layout:
        draw_text_element(c, layout['diploma_number'], f"Nr: {diploma_number}", registered_fonts)
    
    # Draw QR code
    if 'qr_code' in layout and layout['qr_code'].get('enabled', True):
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        qr_config = layout['qr_code']
        qr_x = qr_config.get('x', 2) * cm
        qr_y = qr_config.get('y', 2) * cm
        qr_size = qr_config.get('size', 3) * cm
        
        c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
    
    # Add preview watermark
    if is_preview:
        c.setFont("Helvetica", 48)
        c.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.3)
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "PREVIEW")
        c.restoreState()
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

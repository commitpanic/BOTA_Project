# Diploma PDF Customization Guide

## Overview
The BOTA system allows full customization of diploma certificates through background images and configurable layouts.

## Features

### 1. Background Templates
- Upload custom background images (PNG, JPG) for each diploma type
- Images are automatically scaled to A4 landscape (29.7 x 21 cm)
- Supports transparent PNGs for overlay effects
- If no background is set, a default decorative border is used

### 2. Layout Configuration
Each diploma type can have custom positioning for text elements using JSON configuration.

#### Available Layout Properties
All positions are in **centimeters from the bottom-left corner**:

```json
{
  "callsign_x": 14.5,        // Horizontal position for callsign
  "callsign_y": 10,          // Vertical position for callsign
  "diploma_name_x": 14.5,    // Horizontal position for diploma name
  "diploma_name_y": 12,      // Vertical position for diploma name
  "date_x": 14.5,            // Horizontal position for issue date
  "date_y": 14,              // Vertical position for issue date
  "points_x": 14.5,          // Horizontal position for points info
  "points_y": 16,            // Vertical position for points info
  "qr_x": 2,                 // Horizontal position for QR code (3x3cm)
  "qr_y": 2                  // Vertical position for QR code (3x3cm)
}
```

#### Default Positions
If `layout_config` is empty or missing properties, these defaults are used:
- **callsign**: 14.5 cm horizontal, 10 cm vertical (center of page)
- **diploma_name**: 14.5 cm horizontal, 12 cm vertical
- **date**: 14.5 cm horizontal, 14 cm vertical
- **points**: 14.5 cm horizontal, 16 cm vertical
- **qr_code**: 2 cm horizontal, 2 cm vertical (bottom-left area)

#### Page Dimensions
- A4 Landscape: **29.7 cm (width) × 21 cm (height)**
- Text is centered horizontally at the specified X coordinate
- Y coordinate is measured from bottom (0) to top (21)

### 3. Preview Functionality

#### How to Preview
1. Go to Django Admin → Diploma Types
2. Select your diploma type
3. Click the **"Preview PDF"** button in the detail view
4. A sample PDF opens in new tab with:
   - Your uploaded background image
   - Sample callsign: "SP0AAA"
   - Sample date: current date
   - Sample points: "ACT: 50 | HNT: 75 | B2B: 10"
   - Sample QR code
   - **"PREVIEW"** watermark (removed in actual diplomas)

## Admin Panel Usage

### Uploading Background Templates

1. Navigate to: **Admin Panel → Diplomas → Diploma Types**
2. Select or create a diploma type
3. Scroll to **"PDF Template & Layout"** section
4. Click **"Choose File"** next to "Template image"
5. Upload your background image (PNG or JPG recommended)
6. Save the diploma type

**Tips:**
- Use high-resolution images (300 DPI)
- A4 landscape: 3508 × 2480 pixels at 300 DPI
- Leave space for text elements (don't put important graphics where text appears)
- Test with preview before assigning diplomas

### Configuring Layout

1. In the same section, find **"Layout config"** field
2. Enter JSON configuration (see format above)
3. Only specify properties you want to change (others use defaults)
4. Click **"Preview PDF"** to test positioning
5. Adjust values and preview again until satisfied
6. Save when ready

**Example - Moving Callsign to Top Center:**
```json
{
  "callsign_x": 14.5,
  "callsign_y": 18
}
```

**Example - Custom Layout for Bottom-Heavy Design:**
```json
{
  "callsign_x": 14.5,
  "callsign_y": 6,
  "diploma_name_x": 14.5,
  "diploma_name_y": 8,
  "date_x": 14.5,
  "date_y": 4,
  "points_x": 14.5,
  "points_y": 10,
  "qr_x": 26,
  "qr_y": 2
}
```

## Text Elements Reference

### What Gets Displayed
1. **Callsign** - User's amateur radio callsign (24pt bold)
2. **Diploma Name** - Bilingual name (EN / PL) (16pt regular)
3. **Issue Date** - Format: "Issue Date: YYYY-MM-DD" (12pt regular)
4. **Points Info** - "Points: ACT: X | HNT: Y | B2B: Z" (12pt regular)
5. **Diploma Number** - Small gray text below diploma name (10pt)
6. **QR Code** - 3×3 cm verification code (bottom-left by default)

### Font Details
- Primary font: **Lato** (supports Polish characters: ą, ć, ę, ł, ń, ó, ś, ź, ż)
- Fallback: Helvetica (if Lato not available)
- Text color: Dark gray (RGB: 0.2, 0.2, 0.2)
- All text is centered horizontally at X coordinate

## Workflow Example

### Creating a Custom Diploma

1. **Design Phase**
   - Create background in graphic editor (Photoshop, GIMP, etc.)
   - Use A4 landscape dimensions
   - Mark areas where text will appear
   - Export as PNG or JPG

2. **Upload Phase**
   - Go to Admin → Diploma Types → Add/Edit
   - Upload your background image
   - Leave layout_config empty initially

3. **Testing Phase**
   - Click "Preview PDF"
   - Check if text is readable over background
   - Note if any elements need repositioning

4. **Adjustment Phase**
   - If text overlaps with background graphics:
     - Move elements using layout_config
     - Preview again
   - Repeat until perfect

5. **Deployment**
   - Save the diploma type
   - Assign to users
   - PDFs will automatically use your design

## Troubleshooting

### Issue: Background Image Not Showing
**Possible causes:**
- Image file not uploaded correctly
- File permissions issue
- Corrupt image file

**Solutions:**
- Re-upload the image
- Check file format (use PNG or JPG)
- Verify image opens normally in image viewer
- Check Django logs for errors

### Issue: Text Not Visible on Background
**Possible causes:**
- Background too dark/busy in text areas
- Text color blends with background

**Solutions:**
- Add semi-transparent overlay to background in text areas
- Adjust background image to have clear zones for text
- Consider using white/light areas where text appears

### Issue: Layout Config Not Applied
**Possible causes:**
- Invalid JSON format
- Typo in property names
- Server not restarted after changes

**Solutions:**
- Validate JSON syntax (use online validator)
- Check property names match documented list
- Refresh browser
- Check Django logs for errors

### Issue: QR Code Not Scanning
**Possible causes:**
- QR code too small
- Background interferes with QR code
- Poor contrast

**Solutions:**
- Move QR code to plain/light area of background
- Ensure 3×3 cm minimum size
- Position away from busy background patterns

## Best Practices

1. **Design Backgrounds with Text in Mind**
   - Leave clear areas for text elements
   - Use consistent color zones
   - Avoid busy patterns where text appears

2. **Test Early, Test Often**
   - Use preview function frequently
   - Test with actual user data when possible
   - Check readability on different screens/prints

3. **Keep It Simple**
   - Don't overcrowd the design
   - Ensure high contrast for readability
   - Remember: this is an official certificate

4. **Consider Printing**
   - Test print on actual paper
   - Check colors translate well to print
   - Ensure QR code remains scannable when printed

5. **Backup Configurations**
   - Save working layout_config values
   - Document your custom positions
   - Keep original background image files

## Technical Notes

- PDF Format: A4 Landscape (29.7 × 21 cm)
- Resolution: Vector text, raster background
- File Size: ~50-100 KB typical
- Generation Time: <1 second
- Background Scaling: Automatic, preserveAspectRatio=False (fills page)
- Font Encoding: UTF-8 (full Polish character support)

## Support

For issues or questions:
1. Check Django admin logs
2. Test with preview function
3. Verify JSON syntax
4. Review this documentation
5. Contact system administrator

---

**Last Updated:** November 6, 2025
**System Version:** BOTA Diploma System v2.0

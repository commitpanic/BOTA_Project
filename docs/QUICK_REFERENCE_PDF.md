# Quick Reference: PDF Diploma System

## For Administrators

### Upload Background Image
1. Admin Panel → Diploma Types → Select diploma type
2. Section: "PDF Template & Layout"
3. Upload image (PNG/JPG recommended)
4. Save

### Configure Layout (Optional)
Add JSON in "Layout config" field:
```json
{
  "callsign_x": 14.5,
  "callsign_y": 10,
  "diploma_name_x": 14.5,
  "diploma_name_y": 12,
  "qr_x": 2,
  "qr_y": 2
}
```
All values in **centimeters** from bottom-left.

### Preview Changes
Click **"Preview PDF"** button → Opens sample PDF in new tab

## For Users

### Download Your Diploma
1. Login to BOTA system
2. Go to "My Diplomas"
3. Click "Download PDF" for any diploma
4. PDF saved to your computer

### Verify a Diploma
1. Scan QR code on diploma
2. Opens verification page
3. Shows: callsign, diploma type, issue date, verification count

## Technical Details

### File Structure
- **View**: `frontend/views.py` → `download_certificate()`
- **Admin**: `diplomas/admin.py` → `DiplomaTypeAdmin.preview_diploma()`
- **Model**: `diplomas/models.py` → `DiplomaType.layout_config`
- **Tests**: `test_pdf_generation.py`
- **Docs**: `docs/DIPLOMA_PDF_CUSTOMIZATION.md`

### Layout Config Keys
- `callsign_x`, `callsign_y` - User's callsign position
- `diploma_name_x`, `diploma_name_y` - Diploma name position
- `date_x`, `date_y` - Issue date position
- `points_x`, `points_y` - Points information position
- `qr_x`, `qr_y` - QR code position (3×3cm)

### Default Values (if not specified)
```json
{
  "callsign_x": 14.5,
  "callsign_y": 10,
  "diploma_name_x": 14.5,
  "diploma_name_y": 12,
  "date_x": 14.5,
  "date_y": 14,
  "points_x": 14.5,
  "points_y": 16,
  "qr_x": 2,
  "qr_y": 2
}
```

### Page Size
- A4 Landscape: **29.7 cm (width) × 21 cm (height)**
- X range: 0 to 29.7 cm
- Y range: 0 to 21 cm

### Fonts
- Primary: **Lato** (Regular & Bold)
- Fallback: **Helvetica**
- Size: Callsign 24pt, Name 16pt, Date/Points 12pt

## Common Tasks

### Test New Background
1. Upload image
2. Click "Preview PDF"
3. Check if text readable
4. Adjust layout_config if needed
5. Preview again
6. Save when satisfied

### Move Element
Example: Move callsign to top
```json
{
  "callsign_y": 18
}
```
Only specify what you're changing!

### Multiple Changes
```json
{
  "callsign_y": 18,
  "diploma_name_y": 16,
  "qr_x": 26
}
```

## Troubleshooting

### Text Not Visible?
- Background too dark in text area
- Solution: Edit background image OR move text

### Background Not Showing?
- Re-upload image
- Check file format (PNG/JPG)
- Verify in Django admin that file uploaded

### Wrong Positioning?
- Check JSON syntax (use validator)
- Values in centimeters, not pixels
- Y=0 is bottom, Y=21 is top

## Support
Full documentation: `docs/DIPLOMA_PDF_CUSTOMIZATION.md`

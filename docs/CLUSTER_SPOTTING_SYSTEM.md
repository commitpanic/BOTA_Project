# BOTA Cluster/Spotting System

## Overview

The Cluster system is a real-time spotting feature that allows users to share and view information about active bunker activations. Similar to DX Cluster systems used in amateur radio, this feature helps operators find and work active bunkers.

## Requirements

### Access Control
- **Public Access**: Anyone can view the cluster/spots page (no login required)
- **Authenticated Access**: Only logged-in users can post spots

### Navigation
- Add "Cluster" / "Klaster" tab to main navigation menu
- Available to all visitors (public page)

### Spot Information

#### Required Fields
- **Activator Callsign**: The callsign of the operator activating the bunker (required)
- **Spotter Callsign**: The callsign of the person posting the spot (auto-filled from logged-in user)
- **Frequency**: Operating frequency in MHz (e.g., 14.230) - used to determine band (required)

#### Optional Fields
- **Bunker Reference**: Bunker reference number (e.g., B/SP-0039) - optional
- **Comment**: Short comment/message (e.g., "73!", "QRV SSB", "CW only") - optional, max length TBD

### Spot Lifetime & Updates
- **Default Lifetime**: Spots are displayed for 30 minutes from the last update
- **Spot Updates**: If the same spot is reposted (same activator + bunker/frequency), reset the timer instead of creating duplicate
- **Expiration**: Spots older than 30 minutes are automatically hidden/removed
- **Last Heard Label**: Display time since last update with label "Last heard" / "Ostatnio słyszany"

### Band Detection
Automatically determine the amateur radio band from frequency:
- 1.8 - 2.0 MHz → 160m
- 3.5 - 4.0 MHz → 80m
- 7.0 - 7.3 MHz → 40m
- 10.1 - 10.15 MHz → 30m
- 14.0 - 14.35 MHz → 20m
- 18.068 - 18.168 MHz → 17m
- 21.0 - 21.45 MHz → 15m
- 24.89 - 24.99 MHz → 12m
- 28.0 - 29.7 MHz → 10m
- 50.0 - 54.0 MHz → 6m
- 144.0 - 148.0 MHz → 2m
- 430.0 - 440.0 MHz → 70cm

### Display & Sorting

#### Table Columns
1. **Activator** - Activator's callsign
2. **Bunker** - Bunker reference (or "N/A" if not provided)
3. **Frequency** - Operating frequency with band (e.g., "14.230 MHz (20m)")
4. **Spotter** - Who posted the spot
5. **Comment** - Optional comment
6. **Last Heard** - Time since last spot (e.g., "2 min ago", "15 min ago")

#### Default Sorting
- Newest spots at the top (sorted by last_heard time, descending)

#### Filtering Options
- **By Activator**: Filter by activator callsign
- **By Spotter**: Filter by spotter callsign
- **By Band**: Filter by radio band (40m, 20m, etc.)

#### Sorting Options
- **Last Heard**: Ascending (oldest first) or Descending (newest first - default)

### Auto-Refresh Functionality
- **Refresh Interval**: 30 seconds
- **Countdown Timer**: Display countdown to next refresh above the table (e.g., "Next refresh in: 27s")
- **Automatic Update**: Page content refreshes without full page reload (AJAX/WebSocket)
- **Visual Indicator**: Show countdown timer counting down from 30s to 0s

### User Interface Elements

#### Spot Submission Form (Authenticated Users Only)
```
┌─────────────────────────────────────────────────────────┐
│ Post a Spot                                             │
├─────────────────────────────────────────────────────────┤
│ Activator Callsign: [____________] (required)           │
│ Frequency (MHz):    [____________] (required)           │
│ Bunker Reference:   [____________] (optional)           │
│ Comment:            [____________] (optional)           │
│                     [Submit Spot]                       │
└─────────────────────────────────────────────────────────┘
```

#### Spots Table Display
```
┌─────────────────────────────────────────────────────────┐
│ Active Spots - Next refresh in: 23s                     │
├─────────────────────────────────────────────────────────┤
│ Filters: [Activator ▼] [Spotter ▼] [Band ▼]           │
│ Sort by: [Last Heard ▼] [▲ Newest First]              │
├──────────┬─────────┬──────────────┬─────────┬──────────┤
│Activator │ Bunker  │ Frequency    │ Spotter │Last Heard│
├──────────┼─────────┼──────────────┼─────────┼──────────┤
│ SP3FCK   │B/SP-0039│14.230(20m)  │ SP1ABC  │ 2 min ago│
│ SP2XYZ   │   N/A   │7.090 (40m)  │ SP3DEF  │ 5 min ago│
│ SP5GHI   │B/SP-0001│21.250(15m)  │ SP6JKL  │12 min ago│
└──────────┴─────────┴──────────────┴─────────┴──────────┘
```

## Technical Implementation

### Database Model

**Spot Model:**
```python
class Spot(models.Model):
    activator_callsign = CharField(max_length=20)
    spotter = ForeignKey(User)  # Who posted the spot
    frequency = DecimalField(max_digits=7, decimal_places=3)  # MHz
    band = CharField(max_length=10)  # Auto-calculated
    bunker_reference = CharField(max_length=20, blank=True, null=True)
    bunker = ForeignKey(Bunker, blank=True, null=True)  # Resolved from reference
    comment = CharField(max_length=200, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)  # For spot updates
    expires_at = DateTimeField()  # created_at + 30 minutes
    is_active = BooleanField(default=True)
```

**Indexes:**
- `activator_callsign, frequency, is_active` (for duplicate detection)
- `expires_at, is_active` (for cleanup queries)
- `created_at` (for sorting)

### API Endpoints

**Public Endpoints (no auth required):**
- `GET /api/spots/` - List active spots (with filtering/sorting)
- `GET /api/spots/active/` - Get only currently active spots (not expired)

**Authenticated Endpoints:**
- `POST /api/spots/` - Create a new spot (or update existing)
- `DELETE /api/spots/{id}/` - Delete own spot (optional feature)

**Query Parameters for GET /api/spots/:**
- `activator` - Filter by activator callsign
- `spotter` - Filter by spotter username
- `band` - Filter by band (e.g., "40m")
- `ordering` - Sort field (default: `-updated_at`)

### Frontend Features

**Technologies:**
- AJAX for auto-refresh (or WebSocket for real-time updates - Phase 2)
- JavaScript countdown timer
- Bootstrap for responsive table design
- Django templates with bilingual support (EN/PL)

**JavaScript Functions:**
- `refreshSpots()` - Fetch and update spot list via AJAX
- `startCountdown()` - Update countdown timer every second
- `submitSpot()` - Post new spot via AJAX
- `detectBand(frequency)` - Calculate band from frequency

### Validation Rules

1. **Frequency Validation:**
   - Must be within valid amateur radio bands
   - Decimal format with 3 decimal places (e.g., 14.230)
   - Range: 1.8 - 450.0 MHz

2. **Callsign Validation:**
   - Standard amateur radio callsign format
   - 3-10 characters
   - Pattern: `[A-Z0-9]+` (uppercase alphanumeric)

3. **Bunker Reference Validation:**
   - Optional field
   - If provided, must match pattern: `B/[A-Z]{2}-[0-9]{4}`
   - Validate against existing bunkers in database (optional warning if not found)

4. **Comment Validation:**
   - Optional field
   - Max length: 200 characters
   - Basic HTML sanitization to prevent XSS

### Spot Update Logic

**When a new spot is submitted:**
```python
# Check if spot already exists (same activator + similar frequency + bunker)
existing_spot = Spot.objects.filter(
    activator_callsign=new_callsign,
    frequency__range=(new_freq - 0.01, new_freq + 0.01),
    bunker=new_bunker,
    is_active=True
).first()

if existing_spot:
    # Update existing spot
    existing_spot.updated_at = now
    existing_spot.expires_at = now + timedelta(minutes=30)
    existing_spot.spotter = current_user  # Update spotter
    existing_spot.comment = new_comment  # Update comment
    existing_spot.save()
else:
    # Create new spot
    Spot.objects.create(...)
```

### Automatic Cleanup

**Background Task (Celery or Django Command):**
- Run every 5 minutes
- Mark spots as inactive where `expires_at < now()`
- Optionally delete spots older than 24 hours

```python
# In management command or Celery task
Spot.objects.filter(
    expires_at__lt=timezone.now(),
    is_active=True
).update(is_active=False)
```

## Future Enhancements (Phase 2)

1. **WebSocket Integration**: Real-time updates using Django Channels
2. **Audio Alerts**: Optional sound notification for new spots
3. **Favorite Activators**: Subscribe to notifications for specific activators
4. **Spot History**: View historical spots (archive)
5. **Spot Statistics**: Most active spotters, most spotted bunkers
6. **Map View**: Display spots on an interactive map
7. **Email/Push Notifications**: Alert users when specific bunkers are spotted
8. **RBN Integration**: Automatic spot posting from Reverse Beacon Network

## Security Considerations

1. **Rate Limiting**: Limit spot posting to prevent spam (e.g., 1 spot per minute per user)
2. **Captcha**: Optional CAPTCHA for spot posting (if abuse occurs)
3. **Content Moderation**: Flag/report system for inappropriate comments
4. **XSS Prevention**: Sanitize all user input, especially comments
5. **CSRF Protection**: Django CSRF tokens for all POST requests

## Localization

**Bilingual Labels:**
- English: "Cluster", "Post a Spot", "Active Spots", "Last heard"
- Polish: "Klaster", "Dodaj Spot", "Aktywne Spoty", "Ostatnio słyszany"

All UI text should use Django's `{% trans %}` template tags for easy translation.

## Testing Requirements

1. **Unit Tests:**
   - Band detection from frequency
   - Spot expiration logic
   - Spot update vs create logic
   - Callsign validation

2. **Integration Tests:**
   - API endpoint responses
   - Filtering and sorting
   - Spot submission workflow

3. **Manual Testing:**
   - Auto-refresh functionality
   - Countdown timer accuracy
   - Responsive design on mobile
   - Bilingual interface switching

## Implementation Phases

### Phase 1 (MVP - Current Scope)
- ✅ Basic spot model and database
- ✅ Spot submission form (authenticated users)
- ✅ Public spot list with filtering/sorting
- ✅ Auto-refresh with countdown timer
- ✅ Band detection from frequency
- ✅ 30-minute spot lifetime
- ✅ Bilingual UI (EN/PL)

### Phase 2 (Future)
- WebSocket real-time updates
- Advanced features (map, notifications, etc.)
- Performance optimization
- Enhanced moderation tools

## Success Metrics

- Spot submission success rate > 95%
- Page load time < 2 seconds
- Auto-refresh latency < 500ms
- User engagement: X spots per day
- Zero XSS/security vulnerabilities

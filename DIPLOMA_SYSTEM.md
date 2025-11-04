# BOTA Diploma System - Point-Based Architecture

## Overview
The BOTA diploma system uses a simple point-based approach where diplomas are automatically awarded when users reach specific point thresholds. No manual verification is needed.

## Point System

### How Points Are Earned

1. **Activator Points**
   - Each QSO made as an activator = **1 point**
   - Example: Activate B/SP-0001 and make 5 QSOs = 5 activator points

2. **Hunter Points**
   - Each hunted QSO (worked another activator) = **1 point**
   - Example: Work 10 different bunker activators = 10 hunter points

3. **B2B Points (Bunker-to-Bunker)**
   - Each B2B QSO (activator-to-activator contact) = **1 point**
   - Example: While activating, work 3 other activators = 3 B2B points

## Diploma Configuration

### Admin Panel Fields

Each diploma type has the following configuration in Django admin:

1. **Basic Information**
   - Name (Polish & English)
   - Description (Polish & English)
   - Category (Hunter, Activator, B2B, Special Event, Cluster, Other)
   - Display Order
   - Is Active (can it be earned?)

2. **Point Requirements**
   - Minimum Activator Points (0-∞)
   - Minimum Hunter Points (0-∞)
   - Minimum B2B Points (0-∞)
   
   **Requirements Logic:**
   - All three categories must meet their minimums
   - Set to 0 to ignore that category
   - Example diploma requiring 50 activator + 100 hunter + 0 B2B points

3. **Time Limitation (Optional - for Special Diplomas)**
   - Valid From: Start date (nullable)
   - Valid To: End date (nullable)
   - Leave both empty for permanent diplomas
   - Set dates for time-limited/special event diplomas

### Example Diploma Configurations

**Hunter Bronze**
- Min Activator Points: 0
- Min Hunter Points: 10
- Min B2B Points: 0
- Valid From: (empty)
- Valid To: (empty)
- Result: Earned when user hunts 10 bunkers

**Activator Silver**
- Min Activator Points: 50
- Min Hunter Points: 0
- Min B2B Points: 0
- Valid From: (empty)
- Valid To: (empty)
- Result: Earned when user makes 50 QSOs as activator

**B2B Expert**
- Min Activator Points: 0
- Min Hunter Points: 0
- Min B2B Points: 25
- Valid From: (empty)
- Valid To: (empty)
- Result: Earned when user makes 25 B2B contacts

**Combo Master**
- Min Activator Points: 100
- Min Hunter Points: 100
- Min B2B Points: 50
- Valid From: (empty)
- Valid To: (empty)
- Result: Earned when user meets ALL three requirements

**Summer Special 2025**
- Min Activator Points: 20
- Min Hunter Points: 20
- Min B2B Points: 0
- Valid From: 2025-06-21
- Valid To: 2025-09-22
- Result: Only earnable during summer 2025, requires 20 activator + 20 hunter points

## Automatic Awarding Process

### When Diplomas Are Checked

The system automatically checks for diploma eligibility after every ADIF import:

1. User uploads ADIF log file
2. System processes QSOs and updates user statistics:
   - Count activator QSOs
   - Count hunter QSOs
   - Count B2B QSOs
3. System updates DiplomaProgress records for each diploma type
4. System checks if requirements are met
5. If eligible and not already awarded, diploma is automatically issued

### DiplomaProgress Model

Each user has a progress record for every active diploma type:

```python
DiplomaProgress
  - user: FK to User
  - diploma_type: FK to DiplomaType
  - activator_points: Current activator point total
  - hunter_points: Current hunter point total
  - b2b_points: Current B2B point total
  - percentage_complete: Overall percentage (0-100%)
  - is_eligible: Boolean (all requirements met?)
  - last_updated: Timestamp
```

### Percentage Calculation

The system calculates percentage completion as a weighted average:

```python
# Example: Diploma requires 50 activator + 100 hunter + 0 B2B
# User has: 30 activator, 75 hunter, 0 B2B

activator_pct = min(100, (30 / 50) * 100) = 60%
hunter_pct = min(100, (75 / 100) * 100) = 75%
b2b_pct = 100% (not required, so 100%)

# Only count categories with requirements (2 in this case)
overall = (60% + 75%) / 2 = 67.5%

# is_eligible = False (both activator AND hunter must reach 100%)
```

### Eligibility vs Percentage

- **Percentage**: Shows overall progress (can be 90% but not eligible)
- **Eligibility**: TRUE only when ALL individual requirements are met
- User must reach 100% in EACH required category to earn diploma

## Database Schema

### DiplomaType Fields

```sql
- id
- name_pl, name_en
- description_pl, description_en
- category (choice field)
- min_activator_points (integer, default 0)
- min_hunter_points (integer, default 0)
- min_b2b_points (integer, default 0)
- valid_from (date, nullable)
- valid_to (date, nullable)
- template_image (file)
- is_active (boolean)
- display_order (integer)
- created_at, updated_at
```

### Diploma Fields

```sql
- id
- diploma_type_id (FK)
- user_id (FK)
- issue_date
- diploma_number (unique, auto-generated)
- verification_code (UUID)
- activator_points_earned (snapshot at issuance)
- hunter_points_earned (snapshot at issuance)
- b2b_points_earned (snapshot at issuance)
- pdf_file
- issued_by_id (FK, nullable)
- notes
```

### DiplomaProgress Fields

```sql
- id
- user_id (FK)
- diploma_type_id (FK)
- activator_points (integer)
- hunter_points (integer)
- b2b_points (integer)
- percentage_complete (decimal)
- is_eligible (boolean)
- last_updated
```

## Implementation Notes

### Service Layer Integration

The `LogImportService` should update diploma progress after each import:

```python
from diplomas.models import DiplomaType, DiplomaProgress, Diploma

def update_diploma_progress(user):
    """Update diploma progress for user after statistics change"""
    
    # Get user's current statistics
    stats = user.statistics
    
    # Get or create progress records for all active diplomas
    active_diplomas = DiplomaType.objects.filter(is_active=True)
    
    for diploma_type in active_diplomas:
        progress, created = DiplomaProgress.objects.get_or_create(
            user=user,
            diploma_type=diploma_type
        )
        
        # Update points based on user statistics
        # Each QSO as activator = 1 activator point
        # Each QSO hunting bunkers = 1 hunter point
        # Each B2B QSO = 1 B2B point
        progress.update_points(
            activator=stats.total_activator_qso,    # Total QSOs as activator
            hunter=stats.total_hunter_qso,          # Total QSOs hunting bunkers
            b2b=stats.activator_b2b_qso             # Total B2B QSOs
        )
        
        # Check if eligible and not already awarded
        if progress.is_eligible:
            existing = Diploma.objects.filter(
                user=user,
                diploma_type=diploma_type
            ).exists()
            
            if not existing:
                # Automatically issue diploma
                Diploma.objects.create(
                    diploma_type=diploma_type,
                    user=user,
                    activator_points_earned=progress.activator_points,
                    hunter_points_earned=progress.hunter_points,
                    b2b_points_earned=progress.b2b_points
                )
```

### Frontend Display

Users can view:

1. **Earned Diplomas** - List of awarded diplomas with numbers
2. **Progress Dashboard** - Progress bars for each diploma type
3. **Diploma Details** - Certificate with verification QR code

### Admin Actions

Administrators can:

1. Create new diploma types with point requirements
2. Set time limitations for special diplomas
3. View all issued diplomas
4. View progress for all users
5. Manually issue diplomas (if needed)
6. Recalculate progress (bulk action)

## Testing Checklist

- [ ] Create diploma with only activator requirement
- [ ] Create diploma with only hunter requirement
- [ ] Create diploma with only B2B requirement
- [ ] Create diploma with combined requirements
- [ ] Create time-limited diploma (future dates)
- [ ] Create time-limited diploma (past dates)
- [ ] Upload ADIF file and verify points increase
- [ ] Verify diploma auto-awards at threshold
- [ ] Verify percentage calculation
- [ ] Verify eligibility logic (all requirements must be met)
- [ ] Test expired time-limited diplomas don't award
- [ ] Test inactive diplomas don't award

## Future Enhancements

1. **Email Notifications** - Send email when diploma is earned
2. **PDF Generation** - Auto-generate certificate PDFs
3. **Social Sharing** - Share diploma achievements
4. **Leaderboards** - Show top diploma earners
5. **Badges** - Visual badges for earned diplomas
6. **Diploma Levels** - Bronze/Silver/Gold tiers for same diploma type
7. **Endorsements** - Peer endorsements for diplomas
8. **Special Conditions** - Additional requirements (specific bunkers, date ranges)

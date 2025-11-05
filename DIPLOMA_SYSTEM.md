# BOTA Diploma System - Comprehensive Requirements Architecture

## Overview
The BOTA diploma system uses a flexible requirements-based approach where diplomas are automatically awarded when users meet specific criteria. Requirements can include:
- **Point-based requirements** (QSO counts)
- **Bunker count requirements** (unique and total bunkers)

No manual verification is needed - diplomas are automatically issued when all requirements are met.

## Requirements System

### Point-Based Requirements

Points are earned through QSO activities:

1. **Activator Points**
   - Each QSO made as an activator = **1 point**
   - Example: Activate B/SP-0001 and make 5 QSOs = 5 activator points

2. **Hunter Points**
   - Each hunted QSO (worked another activator) = **1 point**
   - Example: Work 10 different bunker activators = 10 hunter points

3. **B2B Points (Bunker-to-Bunker)**
   - Each B2B QSO (activator-to-activator contact) = **1 point**
   - Example: While activating, work 3 other activators = 3 B2B points

### Bunker Count Requirements

Count requirements track unique bunkers or total activations/hunts:

1. **Unique Activations**
   - Number of **different bunkers** activated
   - Example: Activate B/SP-0001 and B/SP-0002 = 2 unique activations
   - Multiple visits to same bunker = still counts as 1

2. **Total Activations**
   - Total number of **activation sessions** (including repeats)
   - Example: Activate B/SP-0001 three times + B/SP-0002 once = 4 total activations

3. **Unique Hunted**
   - Number of **different bunkers** hunted
   - Example: Work activators from B/SP-0001 and B/SP-0002 = 2 unique hunted
   - Multiple contacts with same bunker = still counts as 1

4. **Total Hunted**
   - Total number of **hunting QSOs** (including repeats)
   - Example: Work B/SP-0001 ten times + B/SP-0002 once = 11 total hunted

### Requirement Combinations

Diplomas can mix point and count requirements:
- **Pure Point-Based**: "50 activator points" (50 QSOs as activator)
- **Pure Count-Based**: "Activate 10 unique bunkers"
- **Combined**: "25 activator points AND 5 unique activations"
- **Complex**: "50 activator points + 10 unique activations + 20 hunter points + 5 unique hunted"

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
   - All active categories must meet their minimums
   - Set to 0 to ignore that category
   - Example: 50 activator + 100 hunter + 0 B2B points

3. **Bunker Count Requirements** (Collapsed by default)
   - Minimum Unique Activations (0-∞) - Different bunkers activated
   - Minimum Total Activations (0-∞) - All activation sessions including repeats
   - Minimum Unique Hunted (0-∞) - Different bunkers hunted
   - Minimum Total Hunted (0-∞) - All hunting QSOs including repeats
   
   **Count Logic:**
   - Set to 0 to ignore that requirement
   - Can be combined with point requirements
   - Example: 5 unique activations + 20 total activations

4. **Time Limitation (Optional - for Special Diplomas)**
   - Valid From: Start date (nullable)
   - Valid To: End date (nullable)
   - Leave both empty for permanent diplomas
   - Set dates for time-limited/special event diplomas

### Example Diploma Configurations

#### Point-Based Examples

**Hunter Bronze** (Simple Hunter Diploma)

- Min Activator Points: 0
- Min Hunter Points: 10
- Min B2B Points: 0
- All count requirements: 0
- Result: Earned when user makes 10 hunter QSOs

**Activator Silver** (Simple Activator Diploma)

- Min Activator Points: 50
- Min Hunter Points: 0
- Min B2B Points: 0
- All count requirements: 0
- Result: Earned when user makes 50 QSOs as activator

**B2B Expert** (B2B Specialist)

- Min Activator Points: 0
- Min Hunter Points: 0
- Min B2B Points: 25
- All count requirements: 0
- Result: Earned when user makes 25 B2B contacts

#### Count-Based Examples

**Explorer** (Visit Different Bunkers)

- All point requirements: 0
- Min Unique Activations: 10
- Min Total Activations: 0
- Min Unique Hunted: 0
- Min Total Hunted: 0
- Result: Earned when user activates 10 different bunkers (any number of QSOs per bunker)

**Marathon Hunter** (Hunt Different Bunkers)

- All point requirements: 0
- Min Unique Activations: 0
- Min Total Activations: 0
- Min Unique Hunted: 25
- Min Total Hunted: 0
- Result: Earned when user hunts 25 different bunkers

**Dedicated Activator** (Repeat Activations)

- All point requirements: 0
- Min Unique Activations: 0
- Min Total Activations: 50
- Min Unique Hunted: 0
- Min Total Hunted: 0
- Result: Earned when user completes 50 activation sessions (can be same bunker multiple times)

#### Combined Requirements Examples

**Combo Master** (Points + Counts)

- Min Activator Points: 100
- Min Hunter Points: 100
- Min B2B Points: 50
- Min Unique Activations: 5
- Min Unique Hunted: 10
- Result: Earned when user meets ALL requirements (points AND counts)

**Versatile Operator** (Balanced Achievement)

- Min Activator Points: 50
- Min Hunter Points: 50
- Min Unique Activations: 10
- Min Unique Hunted: 10
- Result: Must activate 10 bunkers with 50 QSOs AND hunt 10 bunkers with 50 QSOs

#### Time-Limited Examples

**Summer Special 2025** (Seasonal Event)

- Min Activator Points: 20
- Min Hunter Points: 20
- Min Unique Activations: 5
- Valid From: 2025-06-21
- Valid To: 2025-09-22
- Result: Only earnable during summer 2025, requires both points and unique bunker activations

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
  - unique_activations: Current unique bunkers activated
  - total_activations: Current total activation sessions
  - unique_hunted: Current unique bunkers hunted
  - total_hunted: Current total hunting QSOs
  - percentage_complete: Overall percentage (0-100%)
  - is_eligible: Boolean (all requirements met?)
  - last_updated: Timestamp
```

### Percentage Calculation

The system calculates percentage completion as an average across **all active requirements**:

```python
# Example 1: Point-Based Diploma
# Requires: 50 activator + 100 hunter points
# User has: 30 activator, 75 hunter

activator_pct = (30 / 50) * 100 = 60%
hunter_pct = (75 / 100) * 100 = 75%

# Average of 2 active requirements
overall = (60% + 75%) / 2 = 67.5%
is_eligible = False (must reach 100% in BOTH)

# Example 2: Mixed Requirements
# Requires: 50 activator points + 10 unique activations + 5 unique hunted
# User has: 40 activator points, 8 unique activations, 5 unique hunted

activator_pct = (40 / 50) * 100 = 80%
unique_act_pct = (8 / 10) * 100 = 80%
unique_hunt_pct = (5 / 5) * 100 = 100%

# Average of 3 active requirements
overall = (80% + 80% + 100%) / 3 = 86.7%
is_eligible = False (activator points and unique activations not at 100%)

# Example 3: Count-Only Diploma
# Requires: 15 unique activations
# User has: 15 unique activations

unique_act_pct = (15 / 15) * 100 = 100%

# Only 1 active requirement
overall = 100%
is_eligible = True (diploma awarded!)
```

### Eligibility vs Percentage

- **Percentage**: Shows overall progress across all requirements (can be 90% but not eligible)
- **Eligibility**: TRUE only when ALL individual requirements reach 100%
- User must meet **every single active requirement** (any field > 0) to earn diploma
- Requirements set to 0 are ignored completely

## Database Schema

### DiplomaType Fields

```sql
- id
- name_pl, name_en
- description_pl, description_en
- category (choice field)
-- Point Requirements --
- min_activator_points (integer, default 0)
- min_hunter_points (integer, default 0)
- min_b2b_points (integer, default 0)
-- Bunker Count Requirements --
- min_unique_activations (integer, default 0)
- min_total_activations (integer, default 0)
- min_unique_hunted (integer, default 0)
- min_total_hunted (integer, default 0)
-- Time Limitation --
- valid_from (date, nullable)
- valid_to (date, nullable)
-- Display --
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
-- Point Progress --
- activator_points (integer)
- hunter_points (integer)
- b2b_points (integer)
-- Bunker Count Progress --
- unique_activations (integer)
- total_activations (integer)
- unique_hunted (integer)
- total_hunted (integer)
-- Completion Status --
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
        
        # Update all progress values from user statistics
        # Points: Each QSO = 1 point in respective category
        # Counts: Tracked separately from UserStatistics
        progress.update_points(
            activator=stats.total_activator_qso,            # Total QSOs as activator
            hunter=stats.total_hunter_qso,                  # Total QSOs hunting bunkers
            b2b=stats.activator_b2b_qso,                    # Total B2B QSOs
            unique_activations=stats.unique_activations,     # Unique bunkers activated
            total_activations=stats.total_activator_qso,     # Total activation sessions
            unique_hunted=stats.unique_bunkers_hunted,       # Unique bunkers hunted
            total_hunted=stats.total_hunter_qso             # Total hunting QSOs
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

### Point-Based Testing
- [ ] Create diploma with only activator points requirement
- [ ] Create diploma with only hunter points requirement
- [ ] Create diploma with only B2B points requirement
- [ ] Create diploma with combined point requirements
- [ ] Upload ADIF file and verify points increase
- [ ] Verify diploma auto-awards when point threshold reached

### Count-Based Testing
- [ ] Create diploma requiring unique activations only
- [ ] Create diploma requiring total activations only
- [ ] Create diploma requiring unique hunted only
- [ ] Create diploma requiring total hunted only
- [ ] Verify unique counts don't increase when activating same bunker twice
- [ ] Verify total counts DO increase with repeat activations
- [ ] Upload ADIF file and verify counts update correctly

### Mixed Requirements Testing
- [ ] Create diploma with points + counts requirements
- [ ] Verify percentage calculation includes all active requirements
- [ ] Verify eligibility requires ALL requirements at 100%
- [ ] Test diploma with 6 out of 7 requirements met (should not award)
- [ ] Test diploma awards when final requirement is met

### Time-Limited Testing
- [ ] Create time-limited diploma (future dates)
- [ ] Create time-limited diploma (past dates)
- [ ] Test expired time-limited diplomas don't award
- [ ] Test future time-limited diplomas don't award yet

### General Testing
- [ ] Test inactive diplomas don't award
- [ ] Verify percentage calculation formula (average of active requirements)
- [ ] Test progress bars/circles display correctly
- [ ] Verify admin interface shows all 7 requirement types
- [ ] Test manual progress recalculation in admin

## Recent Updates

### November 2025 - Extended Requirements System
- ✅ Added bunker count requirements (4 new fields)
- ✅ Enhanced progress calculation to handle 7 requirement types
- ✅ Updated admin interface with organized fieldsets
- ✅ Automatic progress updates via ADIF log import
- ✅ Backward compatible (existing point-only diplomas work unchanged)

### Key Changes
1. **DiplomaType Model**: Added `min_unique_activations`, `min_total_activations`, `min_unique_hunted`, `min_total_hunted`
2. **DiplomaProgress Model**: Added corresponding tracking fields
3. **Migrations**: `0003_add_bunker_count_requirements.py` and `0004_add_progress_bunker_counts.py`
4. **Progress Calculation**: Now averages across all active requirements (not just points)
5. **Admin Interface**: New "Bunker Count Requirements" fieldset with clear descriptions

## Future Enhancements

1. **Email Notifications** - Send email when diploma is earned
2. **PDF Generation** - Auto-generate certificate PDFs with all requirement details
3. **Social Sharing** - Share diploma achievements
4. **Leaderboards** - Show top diploma earners per category
5. **Badges** - Visual badges for earned diplomas
6. **Diploma Levels** - Bronze/Silver/Gold tiers for same diploma type
7. **Endorsements** - Peer endorsements for diplomas
8. **Special Conditions** - Additional requirements (specific bunkers, date ranges, band/mode restrictions)
9. **Progress Circles** - Convert linear progress bars to circular indicators (UI enhancement)
10. **Diploma Chains** - Require earning one diploma before another (prerequisites)

# BOTA Point System Logic - CORRECTED

## The Problem (Fixed)

The original implementation had the logic **backwards**:
- ❌ When SP3FCK uploaded his activation log, HE got hunter points
- ❌ The callsigns in his log got activator points
- ❌ This was completely wrong!

## Correct Logic (Now Implemented)

### Scenario: SP3FCK activates bunker B/SP-0001

**SP3FCK's ADIF log contains:**
```
<CALL:6>SP1ABC <QSO_DATE:8>20251104 <TIME_ON:4>1430
<CALL:6>SP2XYZ <QSO_DATE:8>20251104 <TIME_ON:4>1445
<CALL:6>SP3DEF <QSO_DATE:8>20251104 <TIME_ON:4>1500 <MY_SIG:4>BOTA <MY_SIG_INFO:9>B/SP-0002
```

**When SP3FCK uploads this log:**

1. **SP3FCK (the activator) gets:**
   - ✅ +3 activator points (3 QSOs made from bunker)
   - ✅ `total_activator_qso` = 3
   - ✅ +1 B2B point (SP3DEF was also at a bunker)
   - ✅ `activator_b2b_qso` = 1

2. **SP1ABC (in the log) gets:**
   - ✅ +1 hunter point (worked a bunker)
   - ✅ `total_hunter_qso` = 1
   - ✅ `unique_bunkers_hunted` = 1 (if first time working B/SP-0001)

3. **SP2XYZ (in the log) gets:**
   - ✅ +1 hunter point (worked a bunker)
   - ✅ `total_hunter_qso` = 1
   - ✅ `unique_bunkers_hunted` = 1

4. **SP3DEF (in the log, B2B) gets:**
   - ✅ +1 hunter point (worked B/SP-0001)
   - ✅ +1 B2B point (was at B/SP-0002 while working B/SP-0001)
   - ✅ `total_hunter_qso` = 1
   - ✅ `total_b2b_qso` = 1
   - ✅ `unique_bunkers_hunted` = 1

## Diploma Point Mapping

### For Diploma Progress Calculation:

```python
# When updating diploma progress after ADIF import:
progress.update_points(
    activator=stats.total_activator_qso,    # Count of QSOs made FROM bunkers
    hunter=stats.total_hunter_qso,          # Count of QSOs working bunkers
    b2b=stats.activator_b2b_qso             # Count of B2B contacts
)
```

### Example Diploma Requirements:

**Hunter Bronze Diploma:**
```
min_activator_points: 0
min_hunter_points: 10
min_b2b_points: 0
```
✅ Earned when user works 10 bunkers (makes 10 QSOs with activators)

**Activator Silver Diploma:**
```
min_activator_points: 50
min_hunter_points: 0
min_b2b_points: 0
```
✅ Earned when user makes 50 QSOs from bunkers (activates and works 50 stations)

**B2B Expert Diploma:**
```
min_activator_points: 0
min_hunter_points: 0
min_b2b_points: 25
```
✅ Earned when user makes 25 bunker-to-bunker contacts

**All-Rounder Diploma:**
```
min_activator_points: 100
min_hunter_points: 100
min_b2b_points: 50
```
✅ Earned when user has 100 activator QSOs AND 100 hunter QSOs AND 50 B2B QSOs

## Database Fields Reference

### UserStatistics Model:
```python
# Activator fields (for when YOU are at a bunker)
total_activator_qso      # Count of QSOs made from bunkers
unique_activations       # Count of unique bunkers activated
activator_b2b_qso        # Count of B2B QSOs as activator

# Hunter fields (for when you work activators)
total_hunter_qso         # Count of QSOs with bunker activators
unique_bunkers_hunted    # Count of unique bunkers worked

# General
total_b2b_qso            # Total B2B connections (as activator OR hunter)
```

### ActivationLog Model:
```python
user        # FK to User (the HUNTER - person who worked the bunker)
activator   # FK to User (the ACTIVATOR - person at the bunker)
bunker      # FK to Bunker (which bunker was activated)
is_b2b      # Boolean (was the hunter also at a bunker?)
```

## Code Changes Made

### File: `activations/log_import_service.py`

**Line ~160-165 (Fixed QSO processing):**
```python
# Award points to ACTIVATOR (person who uploaded the log = person who was at the bunker)
self._award_activator_points(self.activator, is_b2b)

# Award points to HUNTER (person who worked the bunker = person in the log)
self._award_hunter_points(hunter_user, is_b2b)
```

**Line ~210-230 (Fixed hunter points method):**
```python
def _award_hunter_points(self, hunter_user: User, is_b2b: bool):
    """Award points to hunter for working a bunker"""
    stats, _ = UserStatistics.objects.get_or_create(user=hunter_user)
    
    # Hunter gets 1 point per QSO with a bunker
    stats.total_hunter_qso += 1
    
    # Update unique bunkers hunted count
    unique_bunkers = ActivationLog.objects.filter(
        user=hunter_user
    ).values('bunker').distinct().count()
    stats.unique_bunkers_hunted = unique_bunkers
    
    # B2B: If hunter was also at a bunker
    if is_b2b:
        stats.total_b2b_qso += 1
    
    stats.save()
```

**Line ~240-260 (Fixed activator points method):**
```python
def _award_activator_points(self, activator_user: User, is_b2b: bool):
    """Award points to activator for making QSO from bunker"""
    stats, _ = UserStatistics.objects.get_or_create(user=activator_user)
    
    # Activator gets 1 point per QSO made from bunker
    stats.total_activator_qso += 1
    
    # B2B: If both stations were at bunkers
    if is_b2b:
        stats.activator_b2b_qso += 1
    
    stats.save()
```

**Line ~276-320 (Added diploma integration):**
```python
def _update_diploma_progress(self, user: User):
    """Update diploma progress for user after statistics change"""
    from diplomas.models import DiplomaType, DiplomaProgress, Diploma
    
    stats, _ = UserStatistics.objects.get_or_create(user=user)
    active_diplomas = DiplomaType.objects.filter(is_active=True)
    
    for diploma_type in active_diplomas:
        if diploma_type.is_time_limited() and not diploma_type.is_currently_valid():
            continue
        
        progress, created = DiplomaProgress.objects.get_or_create(
            user=user,
            diploma_type=diploma_type
        )
        
        # Update points based on user statistics
        progress.update_points(
            activator=stats.total_activator_qso,
            hunter=stats.total_hunter_qso,
            b2b=stats.activator_b2b_qso
        )
        
        # Auto-award diploma if eligible
        if progress.is_eligible:
            existing = Diploma.objects.filter(
                user=user,
                diploma_type=diploma_type
            ).exists()
            
            if not existing:
                Diploma.objects.create(
                    diploma_type=diploma_type,
                    user=user,
                    activator_points_earned=progress.activator_points,
                    hunter_points_earned=progress.hunter_points,
                    b2b_points_earned=progress.b2b_points
                )
```

## Testing Steps

1. **Create test diplomas in admin:**
   - Hunter Basic: 0/5/0 (5 hunter points)
   - Activator Basic: 5/0/0 (5 activator points)
   - B2B Basic: 0/0/3 (3 B2B points)

2. **Upload SP3FCK's activation log** with 5 QSOs (including 1 B2B)

3. **Verify SP3FCK gets:**
   - ✅ 5 activator points → Earns Activator Basic diploma
   - ✅ 1 B2B point

4. **Verify hunters get:**
   - ✅ Each gets 1 hunter point
   - ✅ After 5 different logs uploaded, one hunter earns Hunter Basic diploma

5. **Verify B2B contacts:**
   - ✅ Both activator and hunter get B2B points
   - ✅ After 3 B2B contacts, earn B2B Basic diploma

## Summary

✅ **Activator** (person at bunker, uploading log):
- Earns activator points
- One point per QSO made

✅ **Hunter** (person in the log, worked the bunker):
- Earns hunter points
- One point per QSO

✅ **B2B** (both at bunkers):
- Both earn B2B points
- One point per B2B contact

✅ **Diplomas**:
- Automatically awarded when thresholds reached
- Based on total_activator_qso, total_hunter_qso, activator_b2b_qso

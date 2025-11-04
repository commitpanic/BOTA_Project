# B2B (Bunker-to-Bunker) Confirmation Logic

## Overview

B2B (Bunker-to-Bunker) QSOs are special contacts where **both stations are activating bunkers**. B2B points are only awarded when **BOTH activators upload their logs** confirming the contact.

## How B2B Works

### Scenario: Two Activators Making Contact

**Station 1: SP3FCK at B/SP-0001**
**Station 2: SP1ABC at B/SP-0002**

They make a QSO at 14:30 UTC.

### Step 1: SP3FCK Uploads His Log

SP3FCK's ADIF log contains:
```
<CALL:6>SP1ABC <QSO_DATE:8>20251104 <TIME_ON:4>1430 <MY_SIG:4>BOTA <MY_SIG_INFO:9>B/SP-0001 <SIG:4>BOTA <SIG_INFO:9>B/SP-0002
```

**What happens:**
1. ✅ SP3FCK gets +1 activator point (for making QSO from B/SP-0001)
2. ✅ SP1ABC gets +1 hunter point (for working B/SP-0001)
3. ⏳ B2B is PENDING - waiting for SP1ABC's log
4. ℹ️ Log is marked as `is_b2b=True` but B2B points NOT awarded yet

### Step 2: SP1ABC Uploads His Log

SP1ABC's ADIF log contains:
```
<CALL:6>SP3FCK <QSO_DATE:8>20251104 <TIME_ON:4>1430 <MY_SIG:4>BOTA <MY_SIG_INFO:9>B/SP-0002 <SIG:4>BOTA <SIG_INFO:9>B/SP-0001
```

**What happens:**
1. ✅ SP1ABC gets +1 activator point (for making QSO from B/SP-0002)
2. ✅ SP3FCK gets +1 hunter point (for working B/SP-0002)
3. 🔍 System checks: Do we have reciprocal logs?
   - SP3FCK has log: worked SP1ABC at 14:30, B2B marked
   - SP1ABC has log: worked SP3FCK at 14:30, B2B marked
   - Time difference: 0 minutes (within ±30 minute window)
4. ✅ **B2B CONFIRMED!**
5. ✅ SP3FCK gets +1 B2B point (`activator_b2b_qso` increases)
6. ✅ SP1ABC gets +1 B2B point (`activator_b2b_qso` increases)

## Final Statistics

After both logs are uploaded:

**SP3FCK:**
- `total_activator_qso`: 1 (made 1 QSO from bunker)
- `total_hunter_qso`: 1 (worked 1 bunker)
- `activator_b2b_qso`: 1 (confirmed B2B)
- `unique_activations`: 1 (activated B/SP-0001)
- `unique_bunkers_hunted`: 1 (hunted B/SP-0002)

**SP1ABC:**
- `total_activator_qso`: 1 (made 1 QSO from bunker)
- `total_hunter_qso`: 1 (worked 1 bunker)
- `activator_b2b_qso`: 1 (confirmed B2B)
- `unique_activations`: 1 (activated B/SP-0002)
- `unique_bunkers_hunted`: 1 (hunted B/SP-0001)

## B2B Confirmation Rules

### Time Window
- QSOs must be within **±30 minutes** of each other
- This accounts for clock differences and slight time variations in logs
- Example: If SP3FCK logs 14:30 and SP1ABC logs 14:32, it's still confirmed

### Required Conditions
1. ✅ Both logs must have `is_b2b=True` (both marked with SIG/SIG_INFO)
2. ✅ Both logs must exist in database (both uploaded)
3. ✅ QSO times must be within ±30 minutes
4. ✅ Callsigns must be reciprocal (A worked B, B worked A)

### What Prevents B2B Confirmation

❌ **Only one log uploaded**
- If SP3FCK uploads but SP1ABC never uploads his log
- Result: No B2B points, even though SP3FCK marked it as B2B

❌ **One log missing B2B markers**
- If SP3FCK marks B2B but SP1ABC's log doesn't have SIG_INFO
- Result: No B2B points (not confirmed on both sides)

❌ **Time mismatch > 30 minutes**
- If SP3FCK logs 14:00 but SP1ABC logs 15:00
- Result: No B2B points (likely different QSOs)

❌ **Callsigns don't match reciprocally**
- If SP3FCK worked SP1ABC but SP1ABC's log shows he worked SP2XYZ
- Result: No B2B points (not the same contact)

## Technical Implementation

### Database Structure

**ActivationLog fields:**
```python
user          # FK to User (hunter - person who worked the bunker)
activator     # FK to User (activator - person at the bunker)
bunker        # FK to Bunker (which bunker was activated)
is_b2b        # Boolean (was this marked as B2B in ADIF?)
activation_date  # DateTime of the QSO
```

### B2B Confirmation Query

When SP1ABC uploads his log showing he worked SP3FCK:
```python
# Look for reciprocal log
reciprocal_log = ActivationLog.objects.filter(
    activator=hunter,      # SP1ABC was activator in their log
    user=activator,        # SP3FCK was in their log
    activation_date__gte=qso_datetime - 30min,
    activation_date__lte=qso_datetime + 30min,
    is_b2b=True           # They marked it as B2B
).first()

if reciprocal_log:
    # B2B confirmed! Award points to both
    activator.statistics.activator_b2b_qso += 1
    hunter.statistics.activator_b2b_qso += 1
```

## Dashboard Display

The dashboard shows:

```
Activator Points:   1 point per QSO made from bunker
Hunter Points:      1 point per QSO working bunkers
B2B Confirmed:      1 point per confirmed B2B (both logs match)
```

## Diploma System

B2B diplomas use `activator_b2b_qso` field:

**Example B2B Diploma:**
```
min_activator_points: 0
min_hunter_points: 0
min_b2b_points: 25
```

Requirements:
- ✅ 25 confirmed B2B contacts (both logs uploaded)
- ❌ NOT 25 B2B contacts marked in your log (must be confirmed)

## Common Scenarios

### Scenario 1: Immediate Confirmation
1. SP3FCK uploads log at 15:00
2. SP1ABC uploads log at 15:05
3. Both get B2B points immediately when SP1ABC uploads

### Scenario 2: Delayed Confirmation
1. SP3FCK uploads log on Monday
2. SP1ABC uploads log on Friday (5 days later)
3. When SP1ABC uploads, system finds SP3FCK's old log
4. Both get B2B points on Friday

### Scenario 3: Never Confirmed
1. SP3FCK uploads log marking B2B
2. SP1ABC never uploads his log
3. SP3FCK never gets B2B points for this contact
4. SP3FCK still gets activator points (1) for the QSO

### Scenario 4: One-Sided B2B
1. SP3FCK thinks it's B2B, marks it in his log
2. SP1ABC wasn't actually at a bunker (hunter only)
3. SP1ABC uploads log without B2B markers
4. No B2B points awarded (wasn't actually B2B)

## Benefits of This System

✅ **Prevents Fraud:** Can't claim fake B2B points without proof
✅ **Ensures Accuracy:** Both parties must confirm the contact
✅ **Fair Competition:** Everyone judged by same standard
✅ **Retroactive Awards:** Late uploads still get credit when logs match
✅ **Transparent:** Users can see which B2Bs are pending vs confirmed

## Testing Checklist

- [ ] Upload log with B2B marker, verify NO B2B points awarded yet
- [ ] Upload reciprocal log, verify BOTH get B2B points
- [ ] Upload logs with 35-minute time difference, verify NO B2B points
- [ ] Upload log without B2B marker, verify other side doesn't get B2B points
- [ ] Upload same log twice, verify B2B points only awarded once
- [ ] Check diploma progress updates correctly with B2B points
- [ ] Verify dashboard shows correct "B2B Confirmed" count

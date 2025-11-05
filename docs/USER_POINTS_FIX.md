# User Points Recalculation Fix

## Problem

Użytkownicy mieli nieprawidłowe punkty hunterskie:
- **SP3BLZ**: 3 QSO jako hunter → tylko 1 punkt zamiast 3
- **SP3HBF**: 3 QSO → 1 punkt
- **SQ3AKR**: 3 QSO → 1 punkt
- **SQ3SIH**: 3 QSO → 1 punkt
- **SP3BKR**: 3 QSO → 1 punkt
- **SQ3BMJ**: 3 QSO → 1 punkt
- **SP3FCK**: 18 QSO jako activator → tylko 6 punktów

## Przyczyna

System punktów używa **inkrementalnego liczenia** w `activations/log_import_service.py`:

```python
def _award_hunter_points(self, hunter_user: User):
    stats, _ = UserStatistics.objects.get_or_create(user=hunter_user)
    stats.hunter_points += 1  # Inkrementalne dodawanie
    stats.total_hunter_qso += 1
    stats.save()
```

Problem powstaje gdy:
1. Statystyki zostały stworzone z zerami
2. Użytkownik miał już QSO w bazie, ale statystyki nie zostały zaktualizowane
3. Punkty były przyznawane tylko dla **nowych** QSO, nie dla istniejących
4. Duplikaty nie dostają punktów (poprawnie), ale mogły być sytuacje gdzie QSO było w bazie bez punktów

## Rozwiązanie

### 1. Management Command

Stworzony command: `accounts/management/commands/recalculate_user_points.py`

**Funkcjonalność**:
- Przelicza wszystkie statystyki na podstawie rzeczywistych QSO w bazie
- Obsługuje zarówno hunter jak i activator statistics
- Opcja `--callsign` do przeliczenia konkretnego użytkownika
- Opcja `--dry-run` do podglądu zmian bez zapisywania

**Użycie**:
```bash
# Przelicz wszystkich użytkowników
python manage.py recalculate_user_points

# Przelicz konkretnego użytkownika
python manage.py recalculate_user_points --callsign SP3BLZ

# Podgląd bez zmian
python manage.py recalculate_user_points --dry-run
```

### 2. Wykonane naprawy

```bash
python manage.py recalculate_user_points
```

**Rezultat**:
```
✓ SP3HBF: hunter_points: 1 → 3
✓ SQ3AKR: hunter_points: 1 → 3
✓ SQ3SIH: hunter_points: 1 → 3
✓ SP3BKR: hunter_points: 1 → 3
✓ SQ3BMJ: hunter_points: 1 → 3
✓ SP3FCK: activator_points: 6 → 18
```

## Logika przeliczania punktów

### Hunter Points
```python
# 1 punkt za każde QSO gdzie user jest w polu `user` (hunter)
hunter_qsos = ActivationLog.objects.filter(user=user)
stats.hunter_points = hunter_qsos.count()
stats.total_hunter_qso = hunter_qsos.count()
stats.unique_bunkers_hunted = hunter_qsos.values('bunker').distinct().count()
```

### Activator Points
```python
# 1 punkt za każde QSO gdzie user jest w polu `activator` (aktywator bunkra)
activator_qsos = ActivationLog.objects.filter(activator=user)
stats.activator_points = activator_qsos.count()
stats.total_activator_qso = activator_qsos.count()
stats.unique_activations = activator_qsos.values('bunker').distinct().count()
```

### B2B Points
```python
# 1 punkt za każde QSO B2B (Bunker-to-Bunker)
b2b_qsos = ActivationLog.objects.filter(activator=user, is_b2b=True)
stats.b2b_points = b2b_qsos.count()
stats.activator_b2b_qso = b2b_qsos.count()
stats.total_b2b_qso = b2b_qsos.count()
```

### Total Points
```python
stats.total_points = (
    stats.hunter_points +
    stats.activator_points +
    stats.b2b_points +
    stats.event_points +
    stats.diploma_points
)
```

## Różnice w modelu ActivationLog

**UWAGA**: Model ActivationLog ma dwa pola użytkownika:
- `user` = **HUNTER** (osoba która zrobiła QSO, jest w logu)
- `activator` = **ACTIVATOR** (osoba która aktywowała bunker, uploadowała log)

## Zapobieganie problemom w przyszłości

### 1. Periodic Task
Dodaj cron job lub Celery task do cyklicznego sprawdzania spójności:
```python
# Run weekly
python manage.py recalculate_user_points --dry-run
```

### 2. Post-save Signal
Rozważ dodanie signal do automatycznego update stats po zapisaniu ActivationLog:
```python
@receiver(post_save, sender=ActivationLog)
def update_user_stats(sender, instance, created, **kwargs):
    if created:
        # Update hunter stats
        hunter_stats, _ = UserStatistics.objects.get_or_create(user=instance.user)
        hunter_stats.hunter_points = ActivationLog.objects.filter(user=instance.user).count()
        hunter_stats.save()
        
        # Update activator stats
        if instance.activator:
            activator_stats, _ = UserStatistics.objects.get_or_create(user=instance.activator)
            activator_stats.activator_points = ActivationLog.objects.filter(activator=instance.activator).count()
            activator_stats.save()
```

### 3. Admin Action
Dodać akcję w admin panelu do przeliczania punktów dla wybranych użytkowników.

## Testing

Sprawdź po każdym uploadzię logów czy punkty są poprawne:
```bash
python manage.py shell -c "
from accounts.models import User, UserStatistics
from activations.models import ActivationLog

for user in User.objects.filter(is_active=True):
    stats = UserStatistics.objects.get(user=user)
    expected_hunter = ActivationLog.objects.filter(user=user).count()
    expected_activator = ActivationLog.objects.filter(activator=user).count()
    
    if stats.hunter_points != expected_hunter:
        print(f'{user.callsign}: Hunter mismatch! {stats.hunter_points} vs {expected_hunter}')
    if stats.activator_points != expected_activator:
        print(f'{user.callsign}: Activator mismatch! {stats.activator_points} vs {expected_activator}')
"
```

---

**Status**: ✅ Naprawione dla wszystkich użytkowników
**Command**: `python manage.py recalculate_user_points`
**Date**: 2025-11-05

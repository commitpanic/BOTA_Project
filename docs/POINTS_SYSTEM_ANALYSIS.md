# Analiza systemu punktów - problemy i rozwiązania

## Status Quo - Obecna architektura

### Modele danych

1. **UserStatistics** (accounts/models.py)
   - OneToOne z User
   - Przechowuje zagregowane statystyki:
     - `activator_points` - punkty aktywatora
     - `hunter_points` - punkty huntera
     - `b2b_points` - punkty B2B
     - `total_activator_qso`, `total_hunter_qso`, `total_b2b_qso`
     - `unique_activations`, `unique_bunkers_hunted`

2. **ActivationLog** (activations/models.py)
   - Pojedyncze QSO
   - Pola: user, bunker, activator, activation_date, is_b2b, mode, band
   - **BRAK** pola z przyznawanymi punktami!

3. **DiplomaProgress** (diplomas/models.py)
   - Osobna kopia punktów dla każdego typu dyplomu
   - Duplikuje dane z UserStatistics

### Obecny flow przyznawania punktów

```
Upload ADIF → ADIFParser → LogImportService
                              ↓
                    _award_activator_points()
                    _award_hunter_points()
                    _check_and_award_b2b()
                              ↓
                    UserStatistics.activator_points += 1
                    UserStatistics.hunter_points += 1
                              ↓
              (RĘCZNIE) update_diploma_progress command
                              ↓
                    DiplomaProgress kopiuje punkty
```

## Zidentyfikowane problemy

### 1. **Brak historii transakcji punktów**
- Nie wiemy KIEDY i ZA CO punkty zostały przyznane
- Niemożliwe jest sprawdzenie poprawności obliczeń
- Brak audytu zmian punktów

### 2. **Przyznawanie punktów przy każdym uploaderze (wielokrotne liczenie)**
```python
# activations/log_import_service.py linia 267-270
def _award_hunter_points(self, hunter_user: User):
    stats, _ = UserStatistics.objects.get_or_create(user=hunter_user)
    stats.hunter_points += 1  # ← Zawsze dodaje, nawet jeśli QSO już istnieje!
    stats.total_hunter_qso += 1
```

**Problem**: Jeśli użytkownik wgra ten sam log 2 razy, dostanie podwójne punkty!

### 3. **B2B system nie działa poprawnie**
- Parser sprawdza `SIG == 'WWBOTA'` zamiast `'BOTA'` (naprawione wczoraj)
- Brak trwałego oznaczenia potwierdzonych B2B
- Punkty B2B nie są zapisywane do `b2b_points` (naprawione wczoraj)
- Brak pola `b2b_confirmed` w ActivationLog

### 4. **Duplikacja danych między UserStatistics i DiplomaProgress**
- DiplomaProgress kopiuje punkty z UserStatistics
- Wymaga ręcznego uruchomienia `update_diploma_progress`
- Możliwe rozbieżności między tabelami

### 5. **Przeliczanie na żywo zamiast incrementalnie**
```python
# activations/log_import_service.py linia 271-274
unique_bunkers = ActivationLog.objects.filter(
    user=hunter_user
).values('bunker').distinct().count()  # ← Przelicza WSZYSTKIE za każdym razem!
stats.unique_bunkers_hunted = unique_bunkers
```

**Problem**: Dla użytkownika z 10000 QSO będzie to wolne zapytanie przy każdym uploaderze.

### 6. **Brak walidacji duplikatów**
- Można wgrać ten sam log wielokrotnie
- Brak unique constraint na ActivationLog
- Brak checksumów plików

## Proponowane rozwiązanie

### Architektura: Event Sourcing + Aggregate Table

#### 1. Nowa tabela: **PointsTransaction** (źródło prawdy)

```python
class PointsTransaction(models.Model):
    """
    Immutable history of all points awarded/deducted.
    Single source of truth for points system.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_transactions')
    
    # Transaction type
    TRANSACTION_TYPE_CHOICES = [
        ('activator_qso', 'Activator QSO'),
        ('hunter_qso', 'Hunter QSO'),
        ('b2b_confirmed', 'B2B Confirmed'),
        ('b2b_cancelled', 'B2B Cancelled'),
        ('diploma_bonus', 'Diploma Bonus'),
        ('event_bonus', 'Event Bonus'),
        ('manual_adjustment', 'Manual Adjustment'),
        ('reversal', 'Reversal'),  # Cofnięcie punktów
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    # Points breakdown
    activator_points = models.IntegerField(default=0)  # Może być ujemne przy reversal
    hunter_points = models.IntegerField(default=0)
    b2b_points = models.IntegerField(default=0)
    event_points = models.IntegerField(default=0)
    diploma_points = models.IntegerField(default=0)
    
    # Context
    activation_log = models.ForeignKey('ActivationLog', null=True, blank=True, on_delete=models.SET_NULL)
    bunker = models.ForeignKey('bunkers.Bunker', null=True, blank=True, on_delete=models.SET_NULL)
    diploma = models.ForeignKey('diplomas.Diploma', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Metadata
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Linking for reversals
    reverses = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reversed_by')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
```

#### 2. Rozszerzenie **UserStatistics** - cache/agregat

```python
class UserStatistics(models.Model):
    """
    Cached aggregate of points from PointsTransaction.
    Should be recalculated from transactions if data integrity is questioned.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Cached points (SUM z PointsTransaction)
    activator_points = models.IntegerField(default=0)
    hunter_points = models.IntegerField(default=0)
    b2b_points = models.IntegerField(default=0)
    event_points = models.IntegerField(default=0)
    diploma_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Cached counts (COUNT DISTINCT z ActivationLog)
    total_activator_qso = models.IntegerField(default=0)
    total_hunter_qso = models.IntegerField(default=0)
    total_b2b_qso = models.IntegerField(default=0)
    unique_activations = models.IntegerField(default=0)
    unique_bunkers_hunted = models.IntegerField(default=0)
    
    # Integrity checking
    last_transaction_id = models.IntegerField(default=0)  # Ostatnia przetworzona transakcja
    last_recalculated = models.DateTimeField(null=True, blank=True)
    
    def recalculate_from_transactions(self):
        """Rebuild from PointsTransaction table"""
        from django.db.models import Sum
        transactions = PointsTransaction.objects.filter(user=self.user)
        
        self.activator_points = transactions.aggregate(Sum('activator_points'))['activator_points__sum'] or 0
        self.hunter_points = transactions.aggregate(Sum('hunter_points'))['hunter_points__sum'] or 0
        self.b2b_points = transactions.aggregate(Sum('b2b_points'))['b2b_points__sum'] or 0
        # ... etc
        
        self.last_recalculated = timezone.now()
        self.save()
```

#### 3. Rozszerzenie **ActivationLog**

```python
class ActivationLog(models.Model):
    # ... existing fields ...
    
    # B2B tracking
    b2b_confirmed = models.BooleanField(default=False)
    b2b_confirmed_at = models.DateTimeField(null=True, blank=True)
    b2b_partner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='b2b_partners')
    b2b_partner_log = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Points tracking
    points_awarded = models.BooleanField(default=False, db_index=True)
    points_transaction = models.ForeignKey('PointsTransaction', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Duplicate prevention
    log_upload_checksum = models.CharField(max_length=64, null=True, blank=True)  # SHA256 of upload
    
    class Meta:
        # Prevent same QSO from being logged twice
        unique_together = [
            ['activator', 'user', 'bunker', 'activation_date']
        ]
```

### Nowy flow przyznawania punktów

```
Upload ADIF → Validate checksum (duplicate check)
                ↓
        Parse QSOs with ADIFParser
                ↓
        For each QSO:
            ↓
        Check if exists (unique_together constraint)
            ↓ (new)
        Create ActivationLog (points_awarded=False)
            ↓
        Create PointsTransaction (activator + hunter)
            ↓
        Update ActivationLog.points_awarded=True
        Update ActivationLog.points_transaction=transaction
            ↓
        UserStatistics.activator_points += transaction.activator_points
        UserStatistics.hunter_points += transaction.hunter_points
            ↓
        (Async) Check B2B confirmation
            ↓ (if confirmed)
        Create PointsTransaction (b2b_points)
        Mark both logs as b2b_confirmed=True
            ↓
        Signal → Update DiplomaProgress
            ↓
        Check eligibility → Auto-award diplomas
```

### Korzyści nowego systemu

1. **Audytowalność**: Każda zmiana punktów jest zapisana w PointsTransaction
2. **Brak duplikatów**: `unique_together` + checksum zapobiegają wielokrotnemu wgraniu
3. **Możliwość cofnięcia**: Transakcje mogą być reverse'owane
4. **Szybkie zapytania**: 
   - `SELECT SUM(activator_points) FROM points_transaction WHERE user_id=X`
   - Cache w UserStatistics dla szybkiego dostępu
5. **Łatwe debugowanie**: Widzimy dokładnie kiedy i za co przyznano punkty
6. **Integralność danych**: Możliwość weryfikacji poprzez `recalculate_from_transactions()`

### Implementacja

#### Faza 1: Migracja danych (bez breaking changes)
1. Utworzyć model PointsTransaction
2. Utworzyć migration dodający pola do ActivationLog
3. Skrypt migrujący istniejące punkty do PointsTransaction
4. Testy integracyjne

#### Faza 2: Zmiana logiki przyznawania punktów
1. Refaktoryzacja LogImportService
2. Dodanie transaction-based point awarding
3. Dodanie duplicate detection
4. Testy jednostkowe

#### Faza 3: Automatyzacja aktualizacji DiplomaProgress
1. Django signals na PointsTransaction.post_save
2. Automatyczne przeliczanie progress
3. Auto-awarding diplomas

#### Faza 4: Narzędzia administracyjne
1. Admin panel dla PointsTransaction
2. Command do recalculate stats
3. Command do reverse transactions
4. Raport integralności danych

## Pytania do rozważenia

1. **Czy chcemy możliwość cofania punktów?** (reversal transactions)
2. **Czy punkty B2B powinny być przyznawane dopiero po potwierdzeniu?**
   - Obecnie: punkty activator/hunter natychmiast, B2B po potwierdzeniu ✓
3. **Jak długo przechowywać PointsTransaction?** (archiwizacja?)
4. **Czy dodać rate limiting na upload logów?** (zapobieganie spamowi)
5. **Czy walidować poprawność danych QSO?** (callsign format, date range, etc.)

## Priorytetowe naprawy (quick wins)

### Pilne (do zrobienia natychmiast):
1. ✅ Fix parser B2B detection (`BOTA` vs `WWBOTA`)
2. ✅ Fix B2B points awarding (dodano `b2b_points += 1`)
3. ❌ **Dodać unique_together do ActivationLog** - zapobiegnie duplikatom
4. ❌ **Dodać pole `points_awarded` do ActivationLog** - oznaczanie przetworzonych
5. ❌ **Dodać checksum do LogUpload** - detekcja identycznych plików

### Średnioterminowe (tydzień):
1. Implementacja PointsTransaction
2. Migracja istniejących danych
3. Refactor LogImportService

### Długoterminowe (miesiąc):
1. Django signals dla auto-update
2. Admin tools
3. Monitoring i alerty
4. Performance optimization

## Rekomendacja

**Zacząć od quick wins** (punkty 3-5 z pilnych), następnie zaplanować pełną implementację PointsTransaction w osobnym sprint'cie. To pozwoli na:
- Natychmiastowe rozwiązanie najpoważniejszych bugów
- Czas na testy nowej architektury
- Migrację bez presji czasowej
- Testowanie na kopii produkcyjnej bazy

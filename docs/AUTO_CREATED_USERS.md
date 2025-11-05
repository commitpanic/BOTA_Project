# Auto-Created Users Feature

## Opis problemu
Użytkownicy, którzy byli wymienieni w logach jako hunterzy, byli automatycznie tworzeni z tymczasowym emailem (np. `sp3xxx@temp.bota.invalid`) i nieaktywnym kontem. Kiedy taki użytkownik próbował się zarejestrować, dostawał komunikat "Callsign already taken", co blokowało możliwość rejestracji.

## Rozwiązanie
Dodano mechanizm "przejęcia" (claim) automatycznie utworzonych kont podczas rejestracji.

## Zmiany w kodzie

### 1. Model User (`accounts/models.py`)
Dodano nowe pole:
- `auto_created` (BooleanField) - oznacza czy użytkownik został utworzony automatycznie z importu logów (True) czy przez ręczną rejestrację (False)

### 2. Migracja (`accounts/migrations/0002_user_auto_created.py`)
- Utworzono i zastosowano migrację dla nowego pola
- Domyślna wartość: `False`

### 3. Import logów (`activations/log_import_service.py`)
Zaktualizowano tworzenie użytkowników:
```python
hunter_user, created = User.objects.get_or_create(
    callsign=hunter_callsign,
    defaults={
        'email': f'{hunter_callsign.lower()}@temp.bota.invalid',
        'is_active': False,
        'auto_created': True  # <-- NOWE
    }
)
```

### 4. Rejestracja (`frontend/views.py` - `register_view`)
Nowa logika rejestracji:
1. Sprawdza czy użytkownik o danym callsign istnieje
2. Jeśli TAK i jest `auto_created=True` oraz `is_active=False`:
   - Aktualizuje email, hasło
   - Ustawia `is_active=True`
   - Ustawia `auto_created=False`
   - Loguje użytkownika
   - Pokazuje komunikat o aktywacji i powiązaniu aktywności
3. Jeśli użytkownik istnieje ale jest aktywny/zarejestrowany:
   - Pokazuje błąd "Callsign already taken"
4. Jeśli nie istnieje:
   - Tworzy nowe konto normalnie

### 5. Template rejestracyjny (`templates/register.html`)
Dodano banner informacyjny:
```html
<div class="alert alert-info">
    Jeśli byłeś wcześniej wymieniony w czyimś logu, 
    możesz przejąć swoją istniejącą aktywność 
    rejestrując się z twoim znakiem wywoławczym.
</div>
```

### 6. Tłumaczenia (`locale/pl/LC_MESSAGES/django.po`)
Dodano nowe komunikaty:
- "Account activated successfully! Welcome to BOTA!"
- "Your previous hunting activity has been linked to your account."
- "Error activating account: {}"
- "Callsign already taken"
- "Registration successful! Welcome to BOTA!"
- "Note:"
- Komunikat o możliwości przejęcia konta

### 7. Skrypt migracyjny (`update_auto_created.py`)
Utworzono skrypt do zaktualizowania istniejących użytkowników:
- Oznacza użytkowników z emailem `@temp.bota.invalid` jako `auto_created=True`
- Wynik: Zaktualizowano 6 użytkowników

## Jak to działa?

### Scenariusz 1: Nowy użytkownik
1. SP3XXX rejestruje się po raz pierwszy
2. Konto tworzone normalnie z `auto_created=False`

### Scenariusz 2: Przejęcie konta
1. SP3ABC był wymieniony w logu jako hunter
2. System stworzył konto: `sp3abc@temp.bota.invalid`, `is_active=False`, `auto_created=True`
3. SP3ABC próbuje się zarejestrować
4. System wykrywa istniejące konto z `auto_created=True`
5. Aktualizuje dane: ustawia prawdziwy email, hasło, aktywuje konto
6. SP3ABC automatycznie zalogowany z powiązaną historią QSO

### Scenariusz 3: Callsign zajęty
1. SP3XYZ ma już aktywne konto (`is_active=True` lub `auto_created=False`)
2. Ktoś inny próbuje się zarejestrować jako SP3XYZ
3. Błąd: "Callsign already taken"

## Baza danych

### Stany użytkownika
| auto_created | is_active | Opis |
|--------------|-----------|------|
| False | True | Normalny zarejestrowany użytkownik |
| False | False | Zarejestrowany ale nieaktywny (admin wyłączył) |
| True | False | Automatycznie utworzony, czeka na rejestrację |
| True | True | Niemożliwe (po aktywacji auto_created → False) |

## Testowanie

### Test 1: Sprawdzenie istniejących użytkowników
```bash
python update_auto_created.py
```
Wynik:
- Updated 6 auto-created users
- Total users: 9
- Auto-created (inactive): 6
- Registered (active): 3

### Test 2: Rejestracja nowego użytkownika
1. Wejdź na `/register/`
2. Zarejestruj się nowym callsign
3. Konto powinno być utworzone i aktywne

### Test 3: Przejęcie konta
1. Sprawdź listę auto-created użytkowników w admin
2. Spróbuj zarejestrować się z jednym z tych callsign
3. Konto powinno zostać aktywowane
4. Historia QSO powinna być widoczna w profilu

### Test 4: Callsign zajęty
1. Spróbuj zarejestrować się z callsign aktywnego użytkownika
2. Błąd: "Callsign already taken"

## Bezpieczeństwo

### Ochrona przed przejęciem aktywnego konta
Użytkownik może przejąć TYLKO konta które są:
- `auto_created=True`
- `is_active=False`

Aktywne konta są chronione przed przejęciem.

### Email jako unikalny klucz
Email jest unikalny, więc nawet jeśli ktoś przejmie konto po callsign, nie może użyć już zajętego emaila.

## Przyszłe usprawnienia

1. **Email verification**: Dodać weryfikację emaila po rejestracji
2. **Bulk update**: Skrypt do masowego oznaczania auto-created users
3. **Admin panel**: Lepszy widok auto-created users w Django admin
4. **Statystyki**: Dashboard pokazujący liczbę oczekujących kont do przejęcia
5. **Notification**: Email do użytkowników gdy ich callsign pojawił się w systemie

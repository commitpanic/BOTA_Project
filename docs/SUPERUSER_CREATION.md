# Automatic Superuser Creation with Password Security

## Przegląd

System automatycznego tworzenia superusera z bezpiecznym hasłem tymczasowym i wymuszeniem zmiany przy pierwszym logowaniu.

## Funkcjonalności

### 1. Bezpieczne Generowanie Hasła
- **16 znaków** długości
- Zawiera: małe litery, wielkie litery, cyfry, znaki specjalne
- Używa `secrets` module (kryptograficznie bezpieczne)
- Każde hasło jest unikalne

### 2. Email z Poświadczeniami
- Wysyłany na `j.f.blaszyk@gmail.com` (konfigurowalny)
- Zawiera: callsign, email, tymczasowe hasło
- Ostrzeżenia o bezpieczeństwie
- Informacja o wymuszonej zmianie hasła

### 3. Wymuszona Zmiana Hasła
- Pole `force_password_change` w modelu User
- Custom middleware przechwytuje wszystkie requesty
- Przekierowanie do strony zmiany hasła
- Brak dostępu do aplikacji bez zmiany

## Użycie

### Tworzenie Superusera

```powershell
# Domyślne wartości (SP3JFB, j.f.blaszyk@gmail.com)
python manage.py create_superuser_with_notification

# Własne wartości
python manage.py create_superuser_with_notification --callsign SP1ABC --email admin@example.com
```

### Parametry

| Parametr | Domyślna Wartość | Opis |
|----------|------------------|------|
| `--callsign` | `SP3JFB` | Znak wywoławczy superusera |
| `--email` | `j.f.blaszyk@gmail.com` | Adres email superusera |

### Output

```
Successfully created superuser: SP3JFB
Credentials sent to j.f.blaszyk@gmail.com
Check your email backend (console or SMTP) for the message
```

Jeśli email nie może być wysłany (np. brak konfiguracji SMTP):
```
Failed to send email: [error message]
TEMPORARY PASSWORD: Xk9@mP2#nL7$qR5%
SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN!
```

## Architektura

### 1. Management Command (`accounts/management/commands/create_superuser_with_notification.py`)

```python
class Command(BaseCommand):
    def generate_secure_password(self, length=16):
        """Generate cryptographically secure random password"""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation),
        ]
        password += [secrets.choice(alphabet) for _ in range(length - 4)]
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
```

**Funkcje:**
- Sprawdzenie czy superuser już istnieje
- Generowanie bezpiecznego hasła
- Utworzenie superusera
- Ustawienie `force_password_change = True`
- Wysłanie emaila z poświadczeniami

### 2. Model User (`accounts/models.py`)

```python
class User(AbstractBaseUser, PermissionsMixin):
    # ... existing fields ...
    
    force_password_change = models.BooleanField(
        _('force password change'),
        default=False,
        help_text=_('User must change password on next login')
    )
```

**Dodane pole:**
- `force_password_change` (BooleanField) - flaga wymuszająca zmianę hasła

### 3. Middleware (`accounts/middleware.py`)

```python
class ForcePasswordChangeMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.force_password_change:
                if not any(request.path.startswith(path) for path in self.exempt_paths):
                    messages.warning(request, _('You must change password...'))
                    return redirect('change_password_required')
        return self.get_response(request)
```

**Logika:**
1. Sprawdza czy użytkownik jest zalogowany
2. Sprawdza czy `force_password_change == True`
3. Wyklucza ścieżki: `/change-password-required/`, `/logout/`, `/admin/logout/`, `/static/`, `/media/`
4. Przekierowuje na stronę zmiany hasła
5. Wyświetla komunikat ostrzegawczy

**Konfiguracja (`settings.py`):**
```python
MIDDLEWARE = [
    # ... other middleware ...
    'accounts.middleware.ForcePasswordChangeMiddleware',  # Na końcu
]
```

### 4. View (`frontend/views.py`)

```python
@login_required
def change_password_required(request):
    if not request.user.force_password_change:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.force_password_change = False  # Wyłącz flagę
            user.save()
            update_session_auth_hash(request, user)  # Zachowaj sesję
            messages.success(request, _('Password changed!'))
            return redirect('dashboard')
    else:
        form = SetPasswordForm(request.user)
    
    return render(request, 'change_password_required.html', {'form': form})
```

**Funkcje:**
- Sprawdzenie czy zmiana jest wymagana
- Wyświetlenie formularza Django `SetPasswordForm`
- Walidacja nowego hasła (min 8 znaków, nie za powszechne, etc.)
- Wyłączenie flagi `force_password_change`
- Zachowanie sesji (użytkownik pozostaje zalogowany)
- Przekierowanie na dashboard

### 5. Template (`templates/change_password_required.html`)

**Elementy:**
- Żółta karta z ostrzeżeniem (Bootstrap warning)
- Formularz z 2 polami: nowe hasło + potwierdzenie
- Lista wymagań hasła (8 znaków, nie numeryczne, etc.)
- Przycisk "Zmień Hasło"
- Link "Wyloguj Się Zamiast Tego"
- Sekcja pomocy: "Dlaczego muszę zmienić hasło?"

### 6. URL Configuration (`frontend/urls.py`)

```python
path('change-password-required/', 
     views.change_password_required, 
     name='change_password_required'),
```

## Email Template

**Subject:** SP_BOTA - Admin Account Created

**Body:**
```
Hello SP3JFB,

Your SP_BOTA administrator account has been created successfully!

Login Details:
--------------
Callsign: SP3JFB
Email: j.f.blaszyk@gmail.com
Temporary Password: Xk9@mP2#nL7$qR5%

IMPORTANT SECURITY NOTICE:
- This is a temporary password
- You MUST change it immediately after your first login
- The system will force you to change your password when you log in
- Do not share this password with anyone
- This email will not be sent again - save your new password securely

Login URL: http://localhost:8000/login/

After logging in, you will be prompted to change your password.

73!
SP_BOTA Team
```

## Przepływ Użytkownika

### 1. Admin Tworzy Superusera
```bash
python manage.py create_superuser_with_notification
```

### 2. Email Wysłany
- Development: pojawia się w konsoli/terminalu
- Production: wysłany przez SMTP na j.f.blaszyk@gmail.com

### 3. Pierwsze Logowanie
- Superuser używa tymczasowego hasła z emaila
- Po logowaniu: middleware przechwytuje request

### 4. Przekierowanie na Zmianę Hasła
- URL: `/change-password-required/`
- Wyświetla się formularz z ostrzeżeniem
- Wszystkie inne strony są zablokowane

### 5. Zmiana Hasła
- Użytkownik wprowadza nowe hasło (2x)
- Django waliduje hasło (min 8 znaków, etc.)
- Hasło zostaje zmienione

### 6. Dostęp Odblokowany
- Flaga `force_password_change` ustawiona na `False`
- Przekierowanie na dashboard
- Pełny dostęp do aplikacji

## Bezpieczeństwo

### Generowanie Hasła
✅ **secrets module** - kryptograficznie bezpieczny generator  
✅ **16 znaków** - długość zgodna z best practices  
✅ **4 typy znaków** - małe, wielkie, cyfry, specjalne  
✅ **Randomizacja** - shuffle przy użyciu SystemRandom()

### Przechowywanie
✅ **Nigdy plaintext** - hasło od razu hashowane przez Django  
✅ **Email jednorazowy** - hasło wysłane tylko raz  
✅ **Console output** - tylko jeśli email fail (dev mode)

### Wymuszenie Zmiany
✅ **Middleware** - blokuje cały dostęp do aplikacji  
✅ **Exempt paths** - tylko logout i strona zmiany hasła  
✅ **Session maintained** - użytkownik nie jest wylogowywany po zmianie

### Walidacja Hasła
✅ **Django validators** - min 8 znaków, nie za powszechne  
✅ **Potwierdzenie** - 2 pola muszą się zgadzać  
✅ **Clear error messages** - komunikaty po polsku

## Testowanie

### Test 1: Tworzenie Superusera
```powershell
python manage.py create_superuser_with_notification
```
**Expected:**
- Message: "Successfully created superuser: SP3JFB"
- Message: "Credentials sent to j.f.blaszyk@gmail.com"
- Email w konsoli/terminalu (dev) lub skrzynce (prod)

### Test 2: Pierwsze Logowanie
1. Idź do `/login/`
2. Wprowadź: callsign=SP3JFB, password=tymczasowe hasło z emaila
3. Kliknij "Login"

**Expected:**
- Przekierowanie na `/change-password-required/`
- Żółta karta z ostrzeżeniem
- Formularz zmiany hasła

### Test 3: Próba Obejścia (Bypass Attempt)
1. Zaloguj się jako superuser (z tymczasowym hasłem)
2. Spróbuj wejść na `/dashboard/` lub `/bunkers/`

**Expected:**
- Automatyczne przekierowanie na `/change-password-required/`
- Komunikat: "You must change your password before continuing"
- Brak dostępu do innych stron

### Test 4: Zmiana Hasła
1. Na stronie `/change-password-required/`
2. Wprowadź nowe hasło (2x)
3. Kliknij "Change Password"

**Expected:**
- Success message: "Your password has been changed successfully!"
- Przekierowanie na `/dashboard/`
- Pełny dostęp do aplikacji
- `force_password_change = False` w bazie

### Test 5: Słabe Hasło
1. Spróbuj ustawić hasło "12345678"

**Expected:**
- Error: "This password is too common"
- Error: "This password is entirely numeric"
- Formularz pozostaje na stronie

### Test 6: Niezgodne Hasła
1. Wprowadź różne hasła w obu polach

**Expected:**
- Error: "The two password fields didn't match"
- Formularz pozostaje na stronie

### Test 7: Logout Zamiast Zmiany
1. Na stronie `/change-password-required/`
2. Kliknij "Logout Instead"

**Expected:**
- Wylogowanie
- Przekierowanie na `/login/`
- Przy następnym logowaniu ponownie wymuszenie zmiany

## Konfiguracja Email

### Development (Console Backend)
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Emaile wyświetlają się w konsoli/terminalu.

### Production (SMTP)
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'SP_BOTA <noreply@spbota.pl>'
```

## Migracja

```python
# accounts/migrations/0003_*.py
operations = [
    migrations.AddField(
        model_name='user',
        name='force_password_change',
        field=models.BooleanField(default=False),
    ),
]
```

```powershell
python manage.py makemigrations accounts
python manage.py migrate accounts
```

## Tłumaczenia

Wszystkie komunikaty przetłumaczone na polski:
- Formularz zmiany hasła
- Komunikaty błędów
- Email z poświadczeniami
- Middleware messages

Plik: `locale/pl/LC_MESSAGES/django.po`

## Przyszłe Usprawnienia

- ⏰ **Password expiration** - wymuszenie zmiany co 90 dni
- 📧 **Email verification** - potwierdzenie zmiany hasła emailem
- 🔒 **2FA during change** - dwuetapowa weryfikacja
- 📝 **Password history** - nie pozwalaj na ponowne użycie starych haseł
- 🚨 **Failed attempts log** - logowanie nieudanych prób
- 🔑 **Password strength meter** - wizualny wskaźnik siły hasła (zxcvbn)

---

**Status**: ✅ Implemented and Tested  
**Security**: ✅ Production-Grade  
**Date**: 2025-11-05  
**Version**: 1.0

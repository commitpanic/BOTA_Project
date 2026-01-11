# Instrukcja wdrożenia aplikacji BOTA na CyberFolks

## 📋 Spis treści
1. [Wymagania](#wymagania)
2. [Przygotowanie przed deployment](#przygotowanie-przed-deployment)
3. [Konfiguracja hostingu CyberFolks](#konfiguracja-hostingu-cyberfolks)
4. [Wgranie aplikacji](#wgranie-aplikacji)
5. [Konfiguracja bazy danych](#konfiguracja-bazy-danych)
6. [Konfiguracja zmiennych środowiskowych](#konfiguracja-zmiennych-środowiskowych)
7. [Uruchomienie aplikacji](#uruchomienie-aplikacji)
8. [Konfiguracja domeny i SSL](#konfiguracja-domeny-i-ssl)
9. [Testowanie](#testowanie)
10. [Backup i utrzymanie](#backup-i-utrzymanie)
11. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## 🎯 Wymagania

### Konto CyberFolks
- **Plan**: Minimum **hosting z obsługą Python/Django** (np. Cloud Hosting lub Serwer VPS)
- **Python**: 3.11+ (sprawdź czy twój plan wspiera Django 5.2)
- **Baza danych**: PostgreSQL (zalecane) lub MySQL/MariaDB
- **Pamięć**: Minimum 2GB RAM
- **Dysk**: Minimum 10GB wolnego miejsca

### Lokalne wymagania
- Git
- Python 3.11+
- Dostęp SSH do serwera (dla Cloud Hosting / VPS)
- Skonfigurowane narzędzie FTP/SFTP (np. FileZilla, WinSCP)

---

## 📦 Przygotowanie przed deployment

### 1. Aktualizacja pliku requirements.txt

Upewnij się, że `requirements.txt` zawiera wszystkie niezbędne pakiety:

```bash
# Weryfikacja lokalnie
pip freeze > requirements_check.txt
```

### 2. Utworzenie pliku .env.example

Stwórz szablon zmiennych środowiskowych (bez wartości):

```bash
# .env.example
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Static/Media
STATIC_ROOT=/home/username/domains/domena.pl/public_python/staticfiles
MEDIA_ROOT=/home/username/domains/domena.pl/public_python/media

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 3. Przygotowanie settings.py

Upewnij się, że `bota_project/settings.py` obsługuje zmienne środowiskowe:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')
```

### 4. Test lokalny

```bash
# Testuj czy aplikacja działa z DEBUG=False
python manage.py check --deploy
python manage.py test
```

### 5. Przygotowanie Git

```bash
# Upewnij się, że .env jest w .gitignore
echo ".env" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "db.sqlite3" >> .gitignore
echo "staticfiles/" >> .gitignore
echo "media/" >> .gitignore

git add .
git commit -m "Przygotowanie do deployment na CyberFolks"
git push
```

---

## 🖥️ Konfiguracja hostingu CyberFolks

### OPCJA A: Cloud Hosting z Python (zalecane dla małych/średnich projektów)

#### 1. Zaloguj się do panelu CyberFolks

Wejdź na: https://panel.cyberfolks.pl/

#### 2. Dodaj domenę

1. W panelu przejdź do **Domeny** → **Dodaj domenę**
2. Wpisz swoją domenę (np. `spbota.pl`)
3. Wybierz **Python/Django** jako typ aplikacji
4. Zanotuj ścieżkę do katalogu aplikacji (np. `/home/username/domains/spbota.pl/`)

#### 3. Konfiguracja środowiska Python

1. W panelu przejdź do **Python** → **Ustawienia**
2. Wybierz wersję Python: **3.11** lub nowszą
3. Ustaw katalog aplikacji: `/home/username/domains/spbota.pl/public_python/`
4. Włącz opcję **Passenger** (serwer aplikacji)

### OPCJA B: Serwer VPS (dla większych projektów)

#### 1. Zamów VPS w CyberFolks

- Panel: https://panel.cyberfolks.pl/
- Wybierz plan VPS odpowiedni dla Django (min. 2GB RAM)

#### 2. Dostęp SSH

```bash
# Połącz się przez SSH
ssh username@ip-serwera

# Zaktualizuj system
sudo apt update && sudo apt upgrade -y
```

#### 3. Instalacja wymaganych pakietów

```bash
# Python i narzędzia
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y postgresql postgresql-contrib nginx git

# Utwórz użytkownika dla aplikacji
sudo adduser --system --group --home /home/bota bota
sudo su - bota
```

---

## 📤 Wgranie aplikacji

### Dla Cloud Hosting:

#### 1. Połącz się przez SSH lub SFTP

```bash
# SSH
ssh username@ssh.cyberfolks.pl

# Przejdź do katalogu domeny
cd ~/domains/spbota.pl/
```

#### 2. Sklonuj repozytorium

```bash
# Jeśli repo jest publiczne:
git clone https://github.com/WildRunner2/BOTA_Project.git public_python

# Jeśli repo jest prywatne - użyj Personal Access Token:
git clone https://github_token@github.com/WildRunner2/BOTA_Project.git public_python

cd public_python
```

#### 3. Utwórz wirtualne środowisko

```bash
# Utwórz venv
python3.11 -m venv venv

# Aktywuj venv
source venv/bin/activate

# Zaktualizuj pip
pip install --upgrade pip
```

#### 4. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### Dla VPS:

```bash
# Jako użytkownik 'bota'
cd /home/bota
git clone https://github.com/WildRunner2/BOTA_Project.git
cd BOTA_Project

# Wirtualne środowisko
python3.11 -m venv venv
source venv/bin/activate

# Instalacja zależności
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## 🗄️ Konfiguracja bazy danych

### Dla Cloud Hosting:

#### 1. Utwórz bazę danych w panelu

1. Panel → **Bazy danych** → **PostgreSQL** → **Utwórz bazę**
2. Nazwa bazy: `bota_db`
3. Nazwa użytkownika: `bota_user`
4. Hasło: wygeneruj silne hasło (zapisz!)
5. Zanotuj:
   - Host: `localhost` lub `pgsql.cyberfolks.pl`
   - Port: `5432`

### Dla VPS:

#### 1. Konfiguracja PostgreSQL

```bash
# Przełącz się na użytkownika postgres
sudo -u postgres psql

# W PostgreSQL:
CREATE DATABASE bota_db;
CREATE USER bota_user WITH PASSWORD 'twoje_silne_haslo_123';
ALTER ROLE bota_user SET client_encoding TO 'utf8';
ALTER ROLE bota_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bota_user SET timezone TO 'Europe/Warsaw';
GRANT ALL PRIVILEGES ON DATABASE bota_db TO bota_user;

-- Dla PostgreSQL 15+
\c bota_db
GRANT ALL ON SCHEMA public TO bota_user;

\q
```

#### 2. Test połączenia

```bash
psql -h localhost -U bota_user -d bota_db -W
# Wpisz hasło i sprawdź połączenie
\q
```

---

## 🔐 Konfiguracja zmiennych środowiskowych

### 1. Utwórz plik .env

```bash
cd ~/domains/spbota.pl/public_python/  # lub /home/bota/BOTA_Project/
nano .env
```

### 2. Wypełnij zmienne środowiskowe

```bash
# Django Settings
SECRET_KEY='wygeneruj-długi-losowy-klucz-min-50-znaków-abc123xyz'
DEBUG=False
ALLOWED_HOSTS=spbota.pl,www.spbota.pl

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=bota_db
DB_USER=bota_user
DB_PASSWORD=twoje_haslo_do_bazy
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Gmail - alternatywnie użyj SMTP CyberFolks)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=twoj-email@gmail.com
EMAIL_HOST_PASSWORD=haslo-aplikacji-gmail

# Alternatywnie - SMTP CyberFolks:
# EMAIL_HOST=smtp.cyberfolks.pl
# EMAIL_PORT=587
# EMAIL_HOST_USER=noreply@spbota.pl
# EMAIL_HOST_PASSWORD=haslo-email-cyberfolks

# Static and Media Files
STATIC_ROOT=/home/username/domains/spbota.pl/public_python/staticfiles
MEDIA_ROOT=/home/username/domains/spbota.pl/public_python/media

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Timezone
TIME_ZONE=Europe/Warsaw
```

### 3. Generowanie SECRET_KEY

```bash
source venv/bin/activate
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Skopiuj wygenerowany klucz do pliku `.env`.

### 4. Zabezpieczenie pliku .env

```bash
chmod 600 .env
```

---

## 🚀 Uruchomienie aplikacji

### 1. Utwórz katalogi

```bash
mkdir -p staticfiles media logs
```

### 2. Wykonaj migracje bazy danych

```bash
source venv/bin/activate
python manage.py migrate
```

### 3. Zbierz pliki statyczne

```bash
python manage.py collectstatic --noinput
```

### 4. Skompiluj tłumaczenia

```bash
python manage.py compilemessages
```

### 5. Utwórz superusera

```bash
python manage.py createsuperuser
# Podaj: login, email, hasło
```

### 6. Test aplikacji

```bash
# Test lokalny na serwerze
python manage.py runserver 0.0.0.0:8000

# Sprawdź w przeglądarce: http://ip-serwera:8000
# Naciśnij Ctrl+C aby zatrzymać
```

---

## 🌐 Konfiguracja Passenger (Cloud Hosting)

### 1. Utwórz plik passenger_wsgi.py

W katalogu głównym aplikacji (obok `manage.py`):

```bash
nano ~/domains/spbota.pl/public_python/passenger_wsgi.py
```

Zawartość:

```python
import sys
import os
from pathlib import Path

# Ścieżka do katalogu projektu
INTERP = Path.home() / "domains" / "spbota.pl" / "public_python" / "venv" / "bin" / "python"
if sys.executable != str(INTERP):
    os.execl(str(INTERP), str(INTERP), *sys.argv)

# Dodaj ścieżkę projektu do sys.path
sys.path.append(str(Path(__file__).parent))

# Załaduj zmienne środowiskowe
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

# Import aplikacji Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 2. Restart Passenger

```bash
# W katalogu public_python/
touch tmp/restart.txt

# Lub z poziomu panelu CyberFolks:
# Domeny → Twoja domena → Restart aplikacji
```

---

## 🌐 Konfiguracja Gunicorn + Nginx (dla VPS)

### 1. Konfiguracja Gunicorn

Plik `gunicorn_config.py` jest już w repozytorium. Sprawdź ścieżki:

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3
accesslog = "/home/bota/BOTA_Project/logs/gunicorn_access.log"
errorlog = "/home/bota/BOTA_Project/logs/gunicorn_error.log"
```

### 2. Systemd service dla Gunicorn

```bash
sudo nano /etc/systemd/system/bota.service
```

Zawartość:

```ini
[Unit]
Description=BOTA Django Application
After=network.target

[Service]
Type=notify
User=bota
Group=bota
WorkingDirectory=/home/bota/BOTA_Project
Environment="PATH=/home/bota/BOTA_Project/venv/bin"
ExecStart=/home/bota/BOTA_Project/venv/bin/gunicorn \
    --config /home/bota/BOTA_Project/gunicorn_config.py \
    bota_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Uruchomienie Gunicorn

```bash
sudo systemctl daemon-reload
sudo systemctl enable bota
sudo systemctl start bota
sudo systemctl status bota
```

### 4. Konfiguracja Nginx

```bash
sudo nano /etc/nginx/sites-available/bota
```

Zawartość:

```nginx
upstream bota_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name spbota.pl www.spbota.pl;

    client_max_body_size 20M;

    access_log /var/log/nginx/bota_access.log;
    error_log /var/log/nginx/bota_error.log;

    location /static/ {
        alias /home/bota/BOTA_Project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/bota/BOTA_Project/media/;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://bota_app;
    }
}
```

### 5. Aktywacja i test Nginx

```bash
# Symlink do sites-enabled
sudo ln -s /etc/nginx/sites-available/bota /etc/nginx/sites-enabled/

# Test konfiguracji
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔒 Konfiguracja domeny i SSL

### 1. Konfiguracja DNS

W panelu zarządzania domeną (może być CyberFolks lub zewnętrzny rejestrator):

1. Dodaj rekord **A**:
   - Nazwa: `@` (lub puste)
   - Wartość: IP serwera CyberFolks
   - TTL: 3600

2. Dodaj rekord **A** dla www:
   - Nazwa: `www`
   - Wartość: IP serwera CyberFolks
   - TTL: 3600

**Uwaga:** Propagacja DNS może zająć do 24-48h.

### 2. Instalacja certyfikatu SSL (Let's Encrypt)

#### Dla Cloud Hosting:

W panelu CyberFolks:
1. Przejdź do **Domeny** → Twoja domena
2. Kliknij **SSL/TLS**
3. Wybierz **Let's Encrypt** (darmowy)
4. Kliknij **Zainstaluj certyfikat**

#### Dla VPS:

```bash
# Instalacja Certbot
sudo apt install -y certbot python3-certbot-nginx

# Automatyczna konfiguracja SSL dla Nginx
sudo certbot --nginx -d spbota.pl -d www.spbota.pl

# Odpowiedz na pytania:
# - Podaj email do powiadomień
# - Zaakceptuj ToS
# - Wybierz przekierowanie HTTP → HTTPS

# Test automatycznego odnowienia
sudo certbot renew --dry-run
```

Certyfikat zostanie automatycznie odnowiony przez cron.

---

## 🧪 Testowanie

### 1. Podstawowy test aplikacji

```bash
# Sprawdź czy strona działa
curl -I https://spbota.pl

# Powinieneś zobaczyć: HTTP/2 200
```

### 2. Test panelu admina

1. Otwórz przeglądarkę: `https://spbota.pl/admin/`
2. Zaloguj się jako superuser
3. Sprawdź czy wszystkie sekcje działają

### 3. Test funkcjonalności

- ✅ Rejestracja użytkownika
- ✅ Logowanie/wylogowanie
- ✅ Resetowanie hasła (email)
- ✅ Import logu ADIF
- ✅ Wyświetlanie bunkrów na mapie
- ✅ Wyszukiwanie bunkrów
- ✅ Wyświetlanie dyplomów
- ✅ Tłumaczenia (PL/EN)

### 4. Test plików statycznych

```bash
# Sprawdź czy CSS/JS ładują się poprawnie
curl -I https://spbota.pl/static/css/style.css
# Powinno zwrócić: 200 OK
```

### 5. Sprawdź logi

```bash
# Gunicorn logs
tail -f /home/bota/BOTA_Project/logs/gunicorn_error.log

# Nginx logs
sudo tail -f /var/log/nginx/bota_error.log

# Passenger logs (Cloud Hosting)
tail -f ~/domains/spbota.pl/logs/error.log
```

---

## 💾 Backup i utrzymanie

### 1. Automatyczny backup bazy danych

Utwórz skrypt backup:

```bash
nano ~/backup_bota.sh
```

Zawartość:

```bash
#!/bin/bash

# Konfiguracja
DB_NAME="bota_db"
DB_USER="bota_user"
BACKUP_DIR="/home/bota/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bota_db_$DATE.sql.gz"

# Utwórz katalog jeśli nie istnieje
mkdir -p $BACKUP_DIR

# Backup bazy danych
PGPASSWORD="twoje_haslo" pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE

# Usuń backupy starsze niż 7 dni
find $BACKUP_DIR -name "bota_db_*.sql.gz" -mtime +7 -delete

echo "Backup utworzony: $BACKUP_FILE"
```

Uprawnienia:

```bash
chmod +x ~/backup_bota.sh
```

### 2. Dodaj do cron

```bash
crontab -e
```

Dodaj linię (codziennie o 2:00 w nocy):

```cron
0 2 * * * /home/bota/backup_bota.sh >> /home/bota/logs/backup.log 2>&1
```

### 3. Backup plików media

```bash
# Ręczny backup
tar -czf ~/backups/media_$(date +%Y%m%d).tar.gz ~/domains/spbota.pl/public_python/media/

# Lub rsync do innego serwera
rsync -avz ~/domains/spbota.pl/public_python/media/ user@backup-server:/backups/bota/media/
```

### 4. Aktualizacja aplikacji

```bash
# Przejdź do katalogu aplikacji
cd ~/domains/spbota.pl/public_python/  # lub /home/bota/BOTA_Project/

# Backup przed aktualizacją
./backup_bota.sh

# Pobierz zmiany z repozytorium
git pull origin main

# Aktywuj venv
source venv/bin/activate

# Zaktualizuj zależności
pip install -r requirements.txt --upgrade

# Wykonaj migracje
python manage.py migrate

# Zbierz pliki statyczne
python manage.py collectstatic --noinput

# Skompiluj tłumaczenia
python manage.py compilemessages

# Restart aplikacji
# Dla Passenger (Cloud Hosting):
touch tmp/restart.txt

# Dla Gunicorn (VPS):
sudo systemctl restart bota
```

---

## 🔧 Rozwiązywanie problemów

### Problem 1: 500 Internal Server Error

**Przyczyny:**
- Błędna konfiguracja `.env`
- Brak migracji bazy danych
- Błąd w kodzie Python

**Rozwiązanie:**
```bash
# Sprawdź logi
tail -f logs/gunicorn_error.log

# Sprawdź konfigurację Django
python manage.py check --deploy

# Sprawdź czy migracje są wykonane
python manage.py showmigrations

# Wykonaj migracje jeśli trzeba
python manage.py migrate
```

### Problem 2: Pliki statyczne się nie ładują

**Rozwiązanie:**
```bash
# Ponownie zbierz pliki statyczne
python manage.py collectstatic --clear --noinput

# Sprawdź uprawnienia
chmod -R 755 staticfiles/

# Dla Passenger - restart
touch tmp/restart.txt

# Dla Nginx - sprawdź konfigurację
sudo nginx -t
sudo systemctl restart nginx
```

### Problem 3: Nie można połączyć z bazą danych

**Rozwiązanie:**
```bash
# Test połączenia PostgreSQL
psql -h localhost -U bota_user -d bota_db -W

# Sprawdź czy PostgreSQL działa
sudo systemctl status postgresql

# Sprawdź hasło w .env
cat .env | grep DB_PASSWORD
```

### Problem 4: Email nie działa

**Rozwiązanie:**
```bash
# Test wysyłki email z Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test',
    'Testowa wiadomość',
    'noreply@spbota.pl',
    ['twoj-email@example.com'],
    fail_silently=False,
)

# Sprawdź ustawienia SMTP w .env
cat .env | grep EMAIL
```

### Problem 5: ImportError lub ModuleNotFoundError

**Rozwiązanie:**
```bash
# Upewnij się że venv jest aktywny
source venv/bin/activate

# Zainstaluj ponownie zależności
pip install -r requirements.txt

# Sprawdź zainstalowane pakiety
pip list
```

### Problem 6: Passenger nie uruchamia aplikacji

**Rozwiązanie:**
```bash
# Sprawdź logi Passenger
tail -f ~/domains/spbota.pl/logs/error.log

# Sprawdź ścieżki w passenger_wsgi.py
cat passenger_wsgi.py

# Sprawdź uprawnienia
ls -la passenger_wsgi.py

# Restart Passenger
touch tmp/restart.txt
mkdir -p tmp && touch tmp/restart.txt
```

### Problem 7: "DisallowedHost" error

**Rozwiązanie:**
```bash
# Dodaj domenę do ALLOWED_HOSTS w .env
nano .env

# Przykład:
ALLOWED_HOSTS=spbota.pl,www.spbota.pl,123.456.789.012

# Restart aplikacji
touch tmp/restart.txt  # Passenger
# lub
sudo systemctl restart bota  # Gunicorn
```

---

## 📊 Monitoring produkcji

### 1. Sprawdzanie statusu aplikacji

```bash
# Status Gunicorn (VPS)
sudo systemctl status bota

# Status Nginx
sudo systemctl status nginx

# Status PostgreSQL
sudo systemctl status postgresql
```

### 2. Monitorowanie logów

```bash
# Logi aplikacji w czasie rzeczywistym
tail -f logs/gunicorn_error.log

# Logi Nginx
sudo tail -f /var/log/nginx/bota_error.log

# Logi Django (dodaj logging w settings.py)
tail -f logs/django.log
```

### 3. Konfiguracja Django logging

Dodaj do `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}
```

### 4. Monitorowanie wydajności

```bash
# Zużycie pamięci przez Gunicorn
ps aux | grep gunicorn

# Zużycie dysku
df -h

# Używanie przez bazę danych
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('bota_db'));"
```

---

## 📞 Wsparcie CyberFolks

- **Panel klienta**: https://panel.cyberfolks.pl/
- **Pomoc techniczna**: https://cyberfolks.pl/pomoc/
- **Kontakt**: https://cyberfolks.pl/kontakt/
- **Email**: support@cyberfolks.pl
- **Telefon**: +48 61 624 00 00

---

## ✅ Checklist przed uruchomieniem

- [ ] Konto CyberFolks z odpowiednim planem
- [ ] Domena wykupiona i skonfigurowana
- [ ] Baza danych PostgreSQL utworzona
- [ ] Repozytorium Git zaktualizowane
- [ ] Plik `.env` wypełniony wszystkimi zmiennymi
- [ ] SECRET_KEY wygenerowany i unikatowy
- [ ] DEBUG=False w produkcji
- [ ] ALLOWED_HOSTS zawiera właściwe domeny
- [ ] Migracje wykonane (`migrate`)
- [ ] Pliki statyczne zebrane (`collectstatic`)
- [ ] Tłumaczenia skompilowane (`compilemessages`)
- [ ] Superuser utworzony
- [ ] SSL/HTTPS skonfigurowane
- [ ] Email testowy wysłany pomyślnie
- [ ] Wszystkie funkcje przetestowane
- [ ] Backup skonfigurowany
- [ ] Logi monitorowane

---

## 🎉 Gotowe!

Twoja aplikacja BOTA powinna teraz działać na produkcji pod adresem:
**https://spbota.pl**

Jeśli masz problemy, sprawdź sekcję [Rozwiązywanie problemów](#rozwiązywanie-problemów) lub skontaktuj się z supportem CyberFolks.

**Powodzenia! 73 de SP3JFB**

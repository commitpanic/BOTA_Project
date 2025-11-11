# BOTA Project - Instrukcja Deployment

## Spis treści
1. [Wymagania wstępne](#wymagania-wstępne)
2. [Przygotowanie serwera](#przygotowanie-serwera)
3. [Instalacja aplikacji](#instalacja-aplikacji)
4. [Konfiguracja środowiska produkcyjnego](#konfiguracja-środowiska-produkcyjnego)
5. [Konfiguracja Nginx](#konfiguracja-nginx)
6. [Konfiguracja Gunicorn](#konfiguracja-gunicorn)
7. [Konfiguracja SSL (HTTPS)](#konfiguracja-ssl-https)
8. [Uruchomienie aplikacji](#uruchomienie-aplikacji)
9. [Backup i aktualizacje](#backup-i-aktualizacje)
10. [Monitorowanie i logi](#monitorowanie-i-logi)

---

## Wymagania wstępne

### Serwer
- **OS**: Ubuntu 22.04 LTS lub nowszy (zalecane) / Debian 11+
- **RAM**: Minimum 2GB (zalecane 4GB+)
- **Dysk**: Minimum 20GB wolnego miejsca
- **Procesor**: 2 vCPU minimum
- **Domena**: Wykupiona domena (np. `spbota.pl`)

### Oprogramowanie
- Python 3.11+
- PostgreSQL 14+ (lub SQLite dla małych instalacji)
- Nginx
- Git

---

## Przygotowanie serwera

### 1. Aktualizacja systemu

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalacja wymaganych pakietów

```bash
# Podstawowe narzędzia
sudo apt install -y build-essential python3-pip python3-dev python3-venv
sudo apt install -y libpq-dev nginx curl git supervisor

# PostgreSQL (jeśli chcesz użyć PostgreSQL zamiast SQLite)
sudo apt install -y postgresql postgresql-contrib
```

### 3. Utworzenie użytkownika aplikacji

```bash
# Utwórz dedykowanego użytkownika dla aplikacji
sudo adduser --system --group --home /home/bota bota

# Przełącz się na tego użytkownika
sudo su - bota
```

---

## Instalacja aplikacji

### 1. Klonowanie repozytorium

```bash
# Jako użytkownik 'bota'
cd /home/bota
git clone https://github.com/WildRunner2/BOTA_Project.git
cd BOTA_Project
```

### 2. Utworzenie virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalacja zależności Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # Dodatkowe pakiety dla produkcji
```

### 4. Konfiguracja bazy danych PostgreSQL (opcjonalnie)

```bash
# Wróć do użytkownika root
exit

# Utwórz bazę danych i użytkownika
sudo -u postgres psql
```

W PostgreSQL:

```sql
CREATE DATABASE bota_db;
CREATE USER bota_user WITH PASSWORD 'twoje_silne_haslo';
ALTER ROLE bota_user SET client_encoding TO 'utf8';
ALTER ROLE bota_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bota_user SET timezone TO 'Europe/Warsaw';
GRANT ALL PRIVILEGES ON DATABASE bota_db TO bota_user;
\q
```

---

## Konfiguracja środowiska produkcyjnego

### 1. Utworzenie pliku .env

```bash
# Jako użytkownik 'bota'
cd /home/bota/BOTA_Project
nano .env
```

Zawartość pliku `.env`:

```bash
# Django Settings
SECRET_KEY='twoj-bardzo-długi-losowy-klucz-min-50-znaków'
DEBUG=False
ALLOWED_HOSTS=spbota.pl,www.spbota.pl,twoj-ip-serwera

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=bota_db
DB_USER=bota_user
DB_PASSWORD=twoje_silne_haslo
DB_HOST=localhost
DB_PORT=5432

# Lub dla SQLite (prostsze, ale mniej wydajne):
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=twoj-email@gmail.com
EMAIL_HOST_PASSWORD=twoje-haslo-aplikacji

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Media and Static Files
STATIC_ROOT=/home/bota/BOTA_Project/staticfiles
MEDIA_ROOT=/home/bota/BOTA_Project/media

# Timezone
TIME_ZONE=Europe/Warsaw
```

**Generowanie SECRET_KEY:**

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 2. Modyfikacja settings.py

Edytuj `bota_project/settings.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

Zainstaluj python-dotenv:

```bash
pip install python-dotenv
```

### 3. Utworzenie katalogów

```bash
mkdir -p /home/bota/BOTA_Project/staticfiles
mkdir -p /home/bota/BOTA_Project/media
mkdir -p /home/bota/BOTA_Project/logs
```

### 4. Migracje i zbieranie plików statycznych

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages  # Kompilacja tłumaczeń
```

### 5. Utworzenie superusera

```bash
python manage.py createsuperuser
```

---

## Konfiguracja Gunicorn

### 1. Test Gunicorn

```bash
# Test lokalny
gunicorn --bind 0.0.0.0:8000 bota_project.wsgi:application
```

### 2. Utworzenie pliku konfiguracyjnego Gunicorn

```bash
nano /home/bota/BOTA_Project/gunicorn_config.py
```

Zawartość:

```python
import multiprocessing

# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/bota/BOTA_Project/logs/gunicorn_access.log"
errorlog = "/home/bota/BOTA_Project/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "bota_gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/bota/BOTA_Project/gunicorn.pid"
user = "bota"
group = "bota"
```

### 3. Utworzenie systemd service

```bash
# Wróć do użytkownika root
exit

sudo nano /etc/systemd/system/bota.service
```

Zawartość:

```ini
[Unit]
Description=BOTA Gunicorn daemon
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

[Install]
WantedBy=multi-user.target
```

### 4. Uruchomienie serwisu

```bash
sudo systemctl daemon-reload
sudo systemctl start bota
sudo systemctl enable bota
sudo systemctl status bota
```

---

## Konfiguracja Nginx

### 1. Utworzenie pliku konfiguracyjnego Nginx

```bash
sudo nano /etc/nginx/sites-available/bota
```

Zawartość:

```nginx
upstream bota_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name spbota.pl www.spbota.pl;

    client_max_body_size 20M;

    # Logging
    access_log /var/log/nginx/bota_access.log;
    error_log /var/log/nginx/bota_error.log;

    # Static files
    location /static/ {
        alias /home/bota/BOTA_Project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/bota/BOTA_Project/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://bota_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### 2. Aktywacja konfiguracji

```bash
sudo ln -s /etc/nginx/sites-available/bota /etc/nginx/sites-enabled/
sudo nginx -t  # Test konfiguracji
sudo systemctl restart nginx
```

### 3. Konfiguracja firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## Konfiguracja SSL (HTTPS)

### Użycie Let's Encrypt (Certbot)

```bash
# Instalacja Certbot
sudo apt install -y certbot python3-certbot-nginx

# Automatyczna konfiguracja SSL
sudo certbot --nginx -d spbota.pl -d www.spbota.pl

# Certbot automatycznie:
# 1. Pobierze certyfikat SSL
# 2. Zmodyfikuje konfigurację Nginx
# 3. Ustawi auto-odnowienie certyfikatu
```

### Sprawdzenie auto-odnowienia

```bash
sudo certbot renew --dry-run
```

### Ręczna odnowa (jeśli potrzebna)

```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## Uruchomienie aplikacji

### Sprawdzenie statusu wszystkich serwisów

```bash
# Sprawdź Gunicorn
sudo systemctl status bota

# Sprawdź Nginx
sudo systemctl status nginx

# Sprawdź PostgreSQL (jeśli używasz)
sudo systemctl status postgresql
```

### Restart aplikacji

```bash
# Restart Gunicorn
sudo systemctl restart bota

# Restart Nginx
sudo systemctl restart nginx

# Pełny restart
sudo systemctl restart bota nginx
```

### Dostęp do aplikacji

- **HTTP**: http://spbota.pl (przekieruje na HTTPS)
- **HTTPS**: https://spbota.pl
- **Admin**: https://spbota.pl/admin/

---

## Backup i aktualizacje

### 1. Backup bazy danych

#### PostgreSQL:

```bash
# Backup
sudo -u postgres pg_dump bota_db > /home/bota/backups/bota_db_$(date +%Y%m%d_%H%M%S).sql

# Restore
sudo -u postgres psql bota_db < /home/bota/backups/bota_db_20250111_120000.sql
```

#### SQLite:

```bash
# Backup
cp /home/bota/BOTA_Project/db.sqlite3 /home/bota/backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# Restore
cp /home/bota/backups/db_20250111_120000.sqlite3 /home/bota/BOTA_Project/db.sqlite3
```

### 2. Automatyczny backup (cron)

```bash
sudo crontab -e -u bota
```

Dodaj:

```bash
# Backup bazy danych codziennie o 2:00
0 2 * * * /usr/bin/pg_dump bota_db > /home/bota/backups/bota_db_$(date +\%Y\%m\%d).sql

# Usuwanie backupów starszych niż 30 dni
0 3 * * * find /home/bota/backups/ -name "*.sql" -mtime +30 -delete
```

### 3. Aktualizacja aplikacji

```bash
# 1. Przełącz się na użytkownika bota
sudo su - bota
cd /home/bota/BOTA_Project

# 2. Backup bazy danych
pg_dump bota_db > ../backup_before_update.sql

# 3. Pobierz najnowszy kod
git fetch origin
git pull origin main

# 4. Aktywuj virtual environment
source venv/bin/activate

# 5. Zaktualizuj zależności
pip install -r requirements.txt --upgrade

# 6. Uruchom migracje
python manage.py migrate

# 7. Zbierz pliki statyczne
python manage.py collectstatic --noinput

# 8. Kompiluj tłumaczenia
python manage.py compilemessages

# 9. Wróć do użytkownika root i restart
exit
sudo systemctl restart bota

# 10. Sprawdź logi
sudo journalctl -u bota -f
```

---

## Monitorowanie i logi

### 1. Logi aplikacji (Gunicorn)

```bash
# Access log
tail -f /home/bota/BOTA_Project/logs/gunicorn_access.log

# Error log
tail -f /home/bota/BOTA_Project/logs/gunicorn_error.log
```

### 2. Logi Django

```bash
# Jeśli masz skonfigurowane logowanie Django
tail -f /home/bota/BOTA_Project/logs/django.log
```

### 3. Logi systemd

```bash
# Real-time logs
sudo journalctl -u bota -f

# Ostatnie 100 linii
sudo journalctl -u bota -n 100

# Logs z ostatniej godziny
sudo journalctl -u bota --since "1 hour ago"
```

### 4. Logi Nginx

```bash
# Access log
sudo tail -f /var/log/nginx/bota_access.log

# Error log
sudo tail -f /var/log/nginx/bota_error.log
```

### 5. Monitoring zasobów

```bash
# Użycie CPU/RAM przez Gunicorn
ps aux | grep gunicorn

# Statystyki systemu
htop

# Miejsce na dysku
df -h

# Status wszystkich serwisów
sudo systemctl list-units --type=service --state=running
```

### 6. Sprawdzanie błędów

```bash
# Sprawdź błędy w ostatnich 24h
sudo journalctl -u bota --since "24 hours ago" | grep -i error

# Sprawdź błędy Nginx
sudo grep -i error /var/log/nginx/bota_error.log
```

---

## Troubleshooting

### Problem: Aplikacja nie startuje

```bash
# Sprawdź logi
sudo journalctl -u bota -n 50

# Sprawdź konfigurację
sudo systemctl status bota

# Test ręczny
sudo su - bota
cd /home/bota/BOTA_Project
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 bota_project.wsgi:application
```

### Problem: 502 Bad Gateway

```bash
# Sprawdź czy Gunicorn działa
sudo systemctl status bota

# Sprawdź połączenie
curl http://127.0.0.1:8000

# Sprawdź logi Nginx
sudo tail -f /var/log/nginx/bota_error.log
```

### Problem: Brak plików statycznych

```bash
# Zbierz ponownie pliki statyczne
sudo su - bota
cd /home/bota/BOTA_Project
source venv/bin/activate
python manage.py collectstatic --noinput

# Sprawdź uprawnienia
ls -la /home/bota/BOTA_Project/staticfiles/
```

### Problem: Błędy bazy danych

```bash
# Sprawdź połączenie z PostgreSQL
sudo -u postgres psql -c "SELECT 1;"

# Sprawdź użytkownika
sudo -u postgres psql -c "\du"

# Test połączenia z aplikacji
sudo su - bota
cd /home/bota/BOTA_Project
source venv/bin/activate
python manage.py dbshell
```

---

## Checklist przed uruchomieniem produkcyjnym

- [ ] `DEBUG=False` w `.env`
- [ ] `SECRET_KEY` jest losowy i bezpieczny
- [ ] `ALLOWED_HOSTS` zawiera domenę produkcyjną
- [ ] Baza danych ma silne hasło
- [ ] SSL/HTTPS jest skonfigurowane (certbot)
- [ ] Firewall jest włączony (`ufw`)
- [ ] Backup bazy danych jest skonfigurowany (cron)
- [ ] Wszystkie migracje są wykonane
- [ ] Pliki statyczne są zebrane
- [ ] Superuser jest utworzony
- [ ] Logi są monitorowane
- [ ] Email jest skonfigurowany (do resetowania haseł)
- [ ] Tłumaczenia są skompilowane (`compilemessages`)

---

## Konfiguracja produkcyjna - Opcjonalnie

### 1. Redis dla cache i sesji (opcjonalnie)

```bash
# Instalacja Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server

# Instalacja klienta Python
pip install redis django-redis

# W settings.py dodaj:
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 2. Celery dla zadań w tle (opcjonalnie)

```bash
pip install celery

# Utwórz plik celery.py w bota_project/
# Skonfiguruj broker (RabbitMQ lub Redis)
```

### 3. Monitoring z Sentry (opcjonalnie)

```bash
pip install sentry-sdk

# W settings.py:
import sentry_sdk
sentry_sdk.init(dsn="twój-dsn-url", traces_sample_rate=1.0)
```

---

## Kontakt i wsparcie

- **GitHub**: https://github.com/WildRunner2/BOTA_Project
- **Website**: https://www.spbota.pl

---

**Powodzenia z deploymentem! 73! 📡**

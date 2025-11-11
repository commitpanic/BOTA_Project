# BOTA Project - Deployment na Render.com

## 📋 Spis treści
1. [Przygotowanie](#przygotowanie)
2. [Utworzenie konta Render](#utworzenie-konta-render)
3. [Deployment aplikacji](#deployment-aplikacji)
4. [Konfiguracja zmiennych środowiskowych](#konfiguracja-zmiennych-środowiskowych)
5. [Utworzenie bazy danych PostgreSQL](#utworzenie-bazy-danych-postgresql)
6. [Migracje i superuser](#migracje-i-superuser)
7. [Testowanie aplikacji](#testowanie-aplikacji)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Przygotowanie

### Pliki przygotowane dla Render:

✅ **render.yaml** - konfiguracja infrastruktury (web service + PostgreSQL)
✅ **build.sh** - skrypt budowania (install deps, collectstatic, migrate)
✅ **runtime.txt** - wersja Python (3.11.9)
✅ **requirements.txt** - zaktualizowany o:
  - `psycopg2-binary` (PostgreSQL driver)
  - `dj-database-url` (parser URL bazy danych)
  - `whitenoise` (obsługa plików statycznych)
  - `gunicorn` (WSGI server)

✅ **settings.py** - zaktualizowany o:
  - Zmienne środowiskowe (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
  - PostgreSQL z DATABASE_URL
  - WhiteNoise middleware
  - Security headers dla produkcji

---

## 📝 Krok 1: Utworzenie konta Render

1. Wejdź na https://render.com
2. Kliknij **"Get Started for Free"**
3. Zarejestruj się przez GitHub (zalecane) lub email
4. Potwierdź email

**Plan darmowy (Free):**
- ✅ Web Service: bezpłatny (z limitami)
- ✅ PostgreSQL: 90 dni za darmo, potem $7/miesiąc
- ⚠️ Usypianie po 15 min bezczynności (pierwsze uruchomienie może trwać ~30s)

---

## 🔧 Krok 2: Deployment aplikacji

### Opcja A: Automatyczny deployment (zalecane)

1. **Pushuj kod do GitHub** (jeśli jeszcze nie zrobiłeś):
```bash
git add .
git commit -m "Add Render.com deployment configuration"
git push origin main
```

2. **W panelu Render:**
   - Kliknij **"New +"** → **"Blueprint"**
   - Wybierz **"Connect a repository"**
   - Autoryzuj dostęp do GitHub
   - Wybierz repozytorium **BOTA_Project**
   - Render automatycznie wykryje `render.yaml`
   - Kliknij **"Apply"**

3. **Render automatycznie utworzy:**
   - Web Service (bota-project)
   - PostgreSQL Database (bota-db)

### Opcja B: Ręczny deployment

1. **Utwórz PostgreSQL Database:**
   - Kliknij **"New +"** → **"PostgreSQL"**
   - Name: `bota-db`
   - Database: `bota_db`
   - User: `bota_user`
   - Region: **Frankfurt** (najbliżej Polski)
   - Plan: **Free** (90 dni trial)
   - Kliknij **"Create Database"**

2. **Utwórz Web Service:**
   - Kliknij **"New +"** → **"Web Service"**
   - Connect your GitHub repository
   - Wybierz **BOTA_Project**
   - Name: `bota-project`
   - Region: **Frankfurt**
   - Branch: `main`
   - Runtime: **Python 3**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn bota_project.wsgi:application`
   - Plan: **Free**
   - Kliknij **"Create Web Service"**

---

## 🔐 Krok 3: Konfiguracja zmiennych środowiskowych

W panelu Web Service → **Environment**:

### Wymagane zmienne:

```bash
# 1. SECRET_KEY (wygeneruj nowy!)
SECRET_KEY=twoj-bardzo-długi-losowy-klucz-min-50-znaków

# 2. DEBUG
DEBUG=False

# 3. ALLOWED_HOSTS (zostanie automatycznie uzupełniony po deploymencie)
ALLOWED_HOSTS=bota-project.onrender.com

# 4. DATABASE_URL (połącz z bazą danych)
DATABASE_URL=postgresql://bota_user:haslo@bota-db.render.com/bota_db
```

### Generowanie SECRET_KEY:

Lokalnie uruchom:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Lub użyj: https://djecrety.ir/

### Połączenie z bazą danych:

1. W panelu PostgreSQL Database → **"Info"**
2. Skopiuj **"Internal Database URL"** (szybsze) lub **"External Database URL"**
3. W panelu Web Service → **Environment** → **Add Environment Variable**:
   - Key: `DATABASE_URL`
   - Value: (wklej skopiowany URL)

**Lub połącz przez Blueprint:**
- W `render.yaml` jest już skonfigurowane:
```yaml
fromDatabase:
  name: bota-db
  property: connectionString
```

---

## 🗄️ Krok 4: Uruchomienie migracji

Po pierwszym deploymencie:

1. **Sprawdź logi budowania:**
   - W panelu Web Service → **"Logs"**
   - Poszukaj: `"Running migrations..."` i `"Build completed successfully!"`

2. **Jeśli migracje nie przeszły automatycznie:**
   - Kliknij **"Shell"** (w menu górnym)
   - Uruchom ręcznie:
```bash
python manage.py migrate
```

3. **Utwórz superusera:**
```bash
python manage.py createsuperuser --email admin@bota.com
# Podaj callsign: ADMIN
# Podaj hasło (silne!)
```

4. **Skompiluj tłumaczenia (opcjonalnie):**
```bash
python compile_planned_activations.py
```

---

## 🌐 Krok 5: Dostęp do aplikacji

Twoja aplikacja będzie dostępna pod:
```
https://bota-project.onrender.com
```

**URL zmienia się w zależności od nazwy serwisu.**

### Pierwsze uruchomienie:
- ⏱️ Może trwać **20-30 sekund** (darmowy plan usypia aplikację)
- ✅ Następne żądania będą szybsze (dopóki aplikacja nie zaśnie)

### Dostęp do panelu admin:
```
https://bota-project.onrender.com/admin/
```

---

## 🔍 Krok 6: Testowanie

### Sprawdź czy działa:

1. **Strona główna:**
   - https://bota-project.onrender.com/
   - Powinna załadować się strona główna BOTA

2. **Panel admin:**
   - https://bota-project.onrender.com/admin/
   - Zaloguj się superuserem

3. **Pliki statyczne:**
   - Sprawdź czy CSS i Bootstrap działają
   - Sprawdź logo w nawigacji

4. **Baza danych:**
   - Utwórz testowego użytkownika
   - Dodaj testowy bunker (jeśli masz uprawnienia)

---

## 🐛 Troubleshooting

### Problem 1: "Application error" lub 502 Bad Gateway

**Przyczyna:** Błąd podczas startu aplikacji

**Rozwiązanie:**
1. Sprawdź logi: Web Service → **"Logs"**
2. Szukaj błędów w czerwonym tekście
3. Najczęstsze problemy:
   - Brak zmiennej `DATABASE_URL`
   - Zły `SECRET_KEY`
   - Błąd w `ALLOWED_HOSTS`

### Problem 2: "DisallowedHost at /"

**Przyczyna:** Domena nie jest w `ALLOWED_HOSTS`

**Rozwiązanie:**
```bash
# W Environment variables dodaj/zmień:
ALLOWED_HOSTS=bota-project.onrender.com,.onrender.com
```

### Problem 3: Brak plików statycznych (CSS/JS)

**Przyczyna:** `collectstatic` nie przeszedł

**Rozwiązanie:**
1. Sprawdź logi budowania
2. Ręcznie uruchom w Shell:
```bash
python manage.py collectstatic --no-input
```

### Problem 4: "Relation does not exist" (tabela nie istnieje)

**Przyczyna:** Migracje nie przeszły

**Rozwiązanie:**
```bash
# W Shell:
python manage.py migrate
python manage.py showmigrations  # sprawdź status
```

### Problem 5: Aplikacja się usypia

**Przyczyna:** Darmowy plan usypia po 15 min bezczynności

**Rozwiązanie:**
- Akceptuj 30s delay przy pierwszym żądaniu
- Lub przejdź na płatny plan ($7/miesiąc) dla stałej dostępności

### Problem 6: PostgreSQL "too many connections"

**Przyczyna:** Darmowa baza ma limit 97 połączeń

**Rozwiązanie:**
```python
# W settings.py już dodane:
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,  # Trzymaj połączenia przez 10 min
        conn_health_checks=True,  # Sprawdzaj zdrowie połączeń
    )
}
```

---

## 📊 Monitorowanie

### Logi aplikacji:
- Web Service → **"Logs"**
- Zobacz w czasie rzeczywistym co się dzieje

### Metryki:
- Web Service → **"Metrics"**
- CPU, RAM, Response time

### Alerty:
- Settings → **"Notifications"**
- Email przy błędach deploymentu

---

## 🔄 Aktualizacje aplikacji

Po każdym `git push` do `main`, Render automatycznie:
1. ✅ Pobierze najnowszy kod
2. ✅ Uruchomi `build.sh`
3. ✅ Zrestartuje aplikację

**Ręczny redeploy:**
- Web Service → **"Manual Deploy"** → **"Deploy latest commit"**

---

## 💰 Koszty

### Plan darmowy (Free):
- **Web Service:** Bezpłatny z limitami
  - 750 godzin/miesiąc (wystarczy na jeden serwis 24/7)
  - Usypianie po 15 min bezczynności
  - 512 MB RAM
  - Darmowe SSL/HTTPS

- **PostgreSQL:** 90 dni za darmo
  - Potem: **$7/miesiąc**
  - 1 GB storage
  - 97 połączeń jednocześnie

### Upgrade (jeśli potrzebny):
- **Starter ($7/miesiąc):** Bez usypiania, więcej RAM
- **Standard ($25/miesiąc):** Więcej zasobów, backupy

---

## ✅ Checklist deploymentu

- [ ] Kod wypushowany na GitHub
- [ ] Render Blueprint utworzony lub serwisy ręcznie
- [ ] PostgreSQL database działa
- [ ] `DATABASE_URL` dodany do Environment
- [ ] `SECRET_KEY` wygenerowany i dodany
- [ ] `ALLOWED_HOSTS` zawiera domenę Render
- [ ] `DEBUG=False` ustawiony
- [ ] Migracje przeszły pomyślnie
- [ ] Superuser utworzony
- [ ] Strona główna ładuje się poprawnie
- [ ] Panel admin działa
- [ ] Pliki statyczne (CSS) działają
- [ ] Logowanie użytkownika działa

---

## 🎉 Gotowe!

Twoja aplikacja BOTA jest teraz live na:
```
https://bota-project.onrender.com
```

### Kolejne kroki:
1. Przetestuj wszystkie funkcje
2. Dodaj testowe dane (bunkers, users)
3. Skonfiguruj domenę własną (opcjonalnie)
4. Monitoruj logi przez pierwszy tydzień
5. Rozważ upgrade jeśli potrzebujesz więcej zasobów

---

## 📞 Wsparcie

- **Render Docs:** https://render.com/docs
- **Django on Render:** https://render.com/docs/deploy-django
- **BOTA GitHub:** https://github.com/WildRunner2/BOTA_Project

---

**Powodzenia z deploymentem! 73! 📡**

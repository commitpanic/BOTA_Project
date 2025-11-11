# BOTA Project - Pre-Deployment Checklist

## ✅ Przed wrzuceniem na serwer produkcyjny

### 1. Konfiguracja Django

- [ ] `DEBUG = False` w pliku `.env`
- [ ] `SECRET_KEY` jest losowy i bezpieczny (min. 50 znaków)
- [ ] `ALLOWED_HOSTS` zawiera właściwą domenę (np. `spbota.pl`)
- [ ] Wszystkie wrażliwe dane są w pliku `.env` (nie w `settings.py`)
- [ ] Plik `.env` jest dodany do `.gitignore`

### 2. Baza danych

- [ ] PostgreSQL jest zainstalowana i skonfigurowana
- [ ] Użytkownik bazy danych ma silne hasło
- [ ] Baza danych ma prawidłowe uprawnienia
- [ ] Backup bazy danych jest skonfigurowany (cron)
- [ ] Wszystkie migracje są wykonane (`python manage.py migrate`)

### 3. Pliki statyczne

- [ ] `STATIC_ROOT` jest ustawiony poprawnie
- [ ] `MEDIA_ROOT` jest ustawiony poprawnie
- [ ] Pliki statyczne zostały zebrane (`python manage.py collectstatic`)
- [ ] Uprawnienia katalogów są prawidłowe (user: bota, group: bota)

### 4. Bezpieczeństwo

- [ ] SSL/HTTPS jest skonfigurowane (Let's Encrypt/Certbot)
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] Firewall jest włączony (`ufw`) z odpowiednimi portami
- [ ] Hasło superusera jest silne i bezpieczne

### 5. Serwery

- [ ] Gunicorn jest zainstalowany
- [ ] Systemd service dla Gunicorn jest skonfigurowany (`bota.service`)
- [ ] Nginx jest zainstalowany i skonfigurowany
- [ ] Nginx ma prawidłowe uprawnienia do plików statycznych
- [ ] Wszystkie serwisy startują automatycznie przy restarcie

### 6. Email

- [ ] SMTP jest skonfigurowany w `.env`
- [ ] Email dla resetowania hasła działa
- [ ] Email testowy został wysłany pomyślnie

### 7. Tłumaczenia

- [ ] Wszystkie pliki `.po` są przetłumaczone
- [ ] Pliki `.mo` są skompilowane (`python manage.py compilemessages`)
- [ ] Przełącznik języka działa poprawnie

### 8. Testy

- [ ] Wszystkie testy przechodzą (`python manage.py test`)
- [ ] Aplikacja działa lokalnie bez błędów
- [ ] Wszystkie funkcje zostały przetestowane ręcznie

### 9. Monitoring i logi

- [ ] Katalog `/home/bota/BOTA_Project/logs/` istnieje
- [ ] Gunicorn zapisuje logi dostępu i błędów
- [ ] Nginx zapisuje logi dostępu i błędów
- [ ] Logi są regularnie sprawdzane

### 10. Backup

- [ ] Katalog `/home/bota/backups/` istnieje
- [ ] Automatyczny backup jest skonfigurowany (cron)
- [ ] Backup został przetestowany (restore)
- [ ] Stare backupy są automatycznie usuwane

### 11. DNS i domena

- [ ] Domena jest wykupiona
- [ ] DNS A record wskazuje na IP serwera
- [ ] DNS propagacja została zakończona (może trwać 24-48h)
- [ ] Subdomena `www` jest skonfigurowana (opcjonalnie)

### 12. Performance

- [ ] Indeksy bazy danych są dodane do często zapytywanych pól
- [ ] Pliki statyczne mają cache headers (Nginx)
- [ ] Gzip compression jest włączony (Nginx)
- [ ] Liczba workerów Gunicorn jest odpowiednia (CPU * 2 + 1)

### 13. Dokumentacja

- [ ] `README.md` jest aktualny
- [ ] `DEPLOYMENT.md` jest dostępny
- [ ] Wszystkie zmienne środowiskowe są udokumentowane w `.env.example`
- [ ] Kontakt do administratora jest zaktualizowany

### 14. Git

- [ ] Wszystkie zmiany są zacommitowane
- [ ] Kod jest wypushowany do GitHub
- [ ] `.gitignore` nie ignoruje ważnych plików
- [ ] Wrażliwe dane (hasła, klucze) NIE są w repozytorium

### 15. Ostatnie sprawdzenia

- [ ] Aplikacja odpowiada na `http://localhost:8000` (Gunicorn)
- [ ] Aplikacja odpowiada na `https://twoja-domena.pl` (Nginx + SSL)
- [ ] Admin panel działa (`https://twoja-domena.pl/admin/`)
- [ ] Logowanie użytkownika działa
- [ ] Upload plików działa (ADIF, zdjęcia)
- [ ] Wszystkie strony renderują się poprawnie
- [ ] Mobilna wersja działa poprawnie

---

## 🚀 Gotowe do deploymentu!

Kiedy wszystkie punkty są zaznaczone, możesz uruchomić:

```bash
# Na serwerze jako użytkownik bota
cd /home/bota/BOTA_Project
./deploy.sh
```

Następnie:

```bash
# Jako root/sudo
sudo systemctl restart bota nginx
sudo journalctl -u bota -f  # Sprawdź logi
```

---

## 🔍 Po deploymencie

- [ ] Sprawdź logi przez pierwszą godzinę
- [ ] Monitoruj użycie CPU/RAM
- [ ] Sprawdź czy backup działa następnego dnia
- [ ] Przetestuj wszystkie główne funkcje na produkcji
- [ ] Skonfiguruj monitoring (opcjonalnie: Sentry, Uptime Robot)

---

## 📞 W razie problemów

1. Sprawdź logi: `sudo journalctl -u bota -f`
2. Sprawdź status: `./status.sh`
3. Zobacz [DEPLOYMENT.md](DEPLOYMENT.md) - sekcja Troubleshooting
4. Kontakt: sp3fck@gmail.com

---

**Powodzenia! 73! 📡**

# Static Files Directory

Ten katalog zawiera statyczne pliki aplikacji (CSS, JavaScript, obrazy).

## Struktura:

```
static/
├── images/          # Obrazy, loga, ikony
│   ├── bota_logo.svg    # Logo BOTA (używane w navbar)
│   └── favicon.svg      # Favicon strony
├── css/             # Własne style CSS
└── js/              # Własne skrypty JavaScript
```

## Jak dodać nowe pliki statyczne:

1. Umieść pliki w odpowiednim podkatalogu (images/css/js)
2. W szablonie dodaj: `{% load static %}`
3. Użyj: `{% static 'ścieżka/do/pliku' %}`

Przykład:
```html
{% load static %}
<img src="{% static 'images/moj_obraz.png' %}" alt="Opis">
<link rel="stylesheet" href="{% static 'css/moj_styl.css' %}">
<script src="{% static 'js/moj_skrypt.js' %}"></script>
```

## Tryb produkcyjny:

Przed wdrożeniem na produkcję uruchom:
```bash
python manage.py collectstatic
```

To skopiuje wszystkie pliki statyczne do katalogu `staticfiles/` który powinien być serwowany przez serwer WWW (nginx/Apache).

## Aktualne pliki:

- `images/bota_logo.png` - Logo projektu BOTA (używane w navbar, wysokość 40px)
- `images/favicon.svg` - Favicon strony (32x32px, SVG dla lepszej jakości)

## Jak dodać swoje logo:

1. Skopiuj plik `bota_logo.png` do katalogu `static/images/`
2. Logo powinno mieć przezroczyste tło (PNG z alpha channel)
3. Zalecana wysokość: 40-50px (szerokość proporcjonalna)
4. Restart serwera: `Ctrl+C` i `python manage.py runserver`

**Uwaga:** Nazwa pliku musi być dokładnie `bota_logo.png` lub zaktualizuj nazwę w `templates/base.html`

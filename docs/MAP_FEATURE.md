# Interactive Bunkers Map Feature

## Przegląd

Interaktywna mapa pokazująca wszystkie zweryfikowane bunkry BOTA z kolorowym oznaczeniem statusu dla zalogowanych użytkowników.

## Funkcjonalność

### Dla niezalogowanych użytkowników:
- ✅ Mapa ze wszystkimi bunkremi (czerwone pinezki)
- ✅ Kliknięcie na marker → popup z nazwą i referencją bunkra
- ✅ Link do szczegółów bunkra
- ✅ Informacja o możliwości zalogowania się dla dodatkowych funkcji

### Dla zalogowanych użytkowników:
- ✅ Kolorowe markery według statusu:
  - **🏆 Złoty (Gold)** - Aktywowany AND Złowiony
  - **� Zielony (Green)** - Aktywowany (nie złowiony)
  - **🔵 Niebieski (Blue)** - Złowiony (nie aktywowany)
  - **⚪ Szary (Gray)** - Jeszcze nie pracowany
  - **🟠 Pulsująca pomarańczowa ramka** - W trakcie aktywacji (aktywny spot)
    - Marker zachowuje swój kolor bazowy (gold/green/blue/gray)
    - Dodaje pulsującą pomarańczową ramkę
    - Pokazuje że ktoś TERAZ aktywuje ten bunker

- ✅ Statystyki na górze:
  - Wszystkie bunkry
  - Aktywowane przez Ciebie
  - Złowione przez Ciebie
  - Jeszcze nie pracowane

- ✅ Filtry (wielokrotny wybór):
  - Pokaż tylko złote (oba statusy)
  - Pokaż tylko aktywowane
  - Pokaż tylko złowione
  - Pokaż tylko czekające na odkrycie (nie pracowane)
  - **Pokaż tylko w trakcie aktywacji** (pulsująca ramka) - specjalny filtr
  - Reset - pokaż wszystkie
  - **Możliwość wyboru wielu filtrów jednocześnie!**
  - Przykład: Zaznacz "Activated" + "Under Activation" → pokaż tylko zielone/złote markery z pulsującą ramką

- ✅ Popup z dodatkowymi informacjami:
  - Status badges (Activated/Hunted)
  - Link do szczegółów bunkra

## Technologie

### Backend
- **Django view**: `frontend.views.map_view`
- **URL**: `/map/`
- **Dane**: JSON z wszystkimi bunkerami + status użytkownika

### Frontend
- **Leaflet.js 1.9.4**: Biblioteka do interaktywnych map
- **OpenStreetMap**: Darmowe kafelki mapy
- **Bootstrap 5**: Styling
- **Bootstrap Icons**: Ikony w markerach

## Implementacja

### 1. Model Bunker
Używa pól:
- `latitude` (DecimalField)
- `longitude` (DecimalField)
- `is_verified` (BooleanField)
- `reference_number` (CharField)
- `name_en` (CharField)

### 2. Widok Django (`frontend/views.py`)

```python
def map_view(request):
    # Pobierz wszystkie zweryfikowane bunkry z koordynatami
    bunkers = Bunker.objects.filter(
        is_verified=True,
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    # Pobierz aktywne spoty (obecnie aktywowane bunkry)
    active_spot_bunker_ids = set(
        Spot.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now(),
            bunker__isnull=False
        ).values_list('bunker_id', flat=True).distinct()
    )
    
    if request.user.is_authenticated:
        # Pobierz aktywowane i złowione bunkry użytkownika
        activated_bunker_ids = ActivationLog.objects.filter(
            activator=request.user
        ).values_list('bunker_id', flat=True).distinct()
        
        hunted_bunker_ids = ActivationLog.objects.filter(
            user=request.user
        ).values_list('bunker_id', flat=True).distinct()
        
        # Określ kolor dla każdego bunkra (priorytet: aktywny spot > oba > pojedyncze)
        for bunker in bunkers:
            is_activated = bunker.id in activated_bunker_ids
            is_hunted = bunker.id in hunted_bunker_ids
            is_under_activation = bunker.id in active_spot_bunker_ids
            
            if is_under_activation:
                color = 'orange'  # Obecnie aktywowany
                icon = 'broadcast-pin'
            elif is_activated and is_hunted:
                color = 'gold'
                icon = 'trophy'
            elif is_activated:
                color = 'green'
                icon = 'broadcast'
            elif is_hunted:
                color = 'blue'
                icon = 'binoculars'
            else:
                color = 'gray'
                icon = 'geo-alt'
    
    return render(request, 'map.html', context)
```

### 3. Template (`templates/map.html`)

**Struktura:**
- Statistics card (tylko dla zalogowanych)
- Legend + Filters (tylko dla zalogowanych)
- Mapa (dla wszystkich)

**Leaflet inicjalizacja:**
```javascript
const map = L.map('map').setView([52.0, 19.0], 7); // Polska

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
}).addTo(map);
```

**Custom markers:**
```javascript
function createMarkerIcon(color, iconName) {
    return L.divIcon({
        html: `<div style="background-color: ${colorMap[color]}; ...">
                <i class="bi bi-${iconName}"></i>
               </div>`,
        iconSize: [30, 30],
    });
}
```

**Filtry:**
```javascript
function applyFilter() {
    markers.forEach(item => {
        // Show marker if no filters active OR if marker color is in active filters
        if (activeFilters.size === 0 || activeFilters.has(item.color)) {
            map.addLayer(item.marker);
        } else {
            map.removeLayer(item.marker);
        }
    });
}
```

**Obsługa checkboxów (wielokrotny wybór):**
```javascript
document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const filter = this.value;
        
        if (this.checked) {
            activeFilters.add(filter);
        } else {
            activeFilters.delete(filter);
        }
        
        applyFilter();
    });
});
```

### 4. Nawigacja (`templates/base.html`)

Dodany link w głównym menu nawigacji:
```html
<li class="nav-item">
    <a class="nav-link" href="{% url 'map' %}">
        <i class="bi bi-map"></i> {% trans "Map" %}
    </a>
</li>
```

## Kolory i ikony

| Status | Kolor | Kod | Ikona | Znaczenie |
|--------|-------|-----|-------|-----------|
| Oba | Złoty | #FFD700 | trophy | Aktywowany I Złowiony |
| Tylko Activator | Zielony | #28a745 | broadcast | Tylko Aktywowany |
| Tylko Hunter | Niebieski | #007bff | binoculars | Tylko Złowiony |
| Żaden | Szary | #6c757d | geo-alt | Nie pracowany |
| Niezalogowany | Czerwony | #dc3545 | geo-alt | Domyślny |

**Wizualna wskazówka "Under Activation":**
- **Pulsująca pomarańczowa ramka** (#fd7e14) - dodawana do markera gdy bunker ma aktywny spot
- Marker zachowuje swój bazowy kolor (gold/green/blue/gray/red)
- Animacja pulsowania trwa 2 sekundy i się powtarza
- Pokazuje że ktoś właśnie TERAZ aktywuje ten bunker
- Popup pokazuje badge "W trakcie aktywacji" wraz z innymi statusami (Activated/Hunted)

**Przykłady kombinacji:**
- 🏆 Złoty marker + 🟠 pulsująca ramka = Użytkownik aktywował I złowił, teraz ktoś tam jest
- 🟢 Zielony marker + 🟠 pulsująca ramka = Użytkownik aktywował, teraz ktoś tam jest
- ⚪ Szary marker + 🟠 pulsująca ramka = Użytkownik jeszcze nie pracował, ale ktoś tam jest TERAZ

## Responsywność

- **Desktop**: Pełna wysokość ekranu (calc(100vh - 200px))
- **Mobile**: Minimum 500px wysokości
- **Touch**: Obsługa touch events dla mapy
- **Bootstrap 5**: Responsive grid dla statystyk i legendy

## Wydajność

- ✅ Pojedyncze zapytanie SQL dla bunkrów
- ✅ `select_related()` dla relacji
- ✅ `distinct()` dla unikalnych ID
- ✅ JSON serialization w Django (bezpieczniejsze niż JS)
- ✅ Lazy loading markerów (tylko widoczne na mapie)
- ✅ Batch operations dla dodawania markerów

## Bezpieczeństwo

- ✅ Tylko zweryfikowane bunkry (`is_verified=True`)
- ✅ Tylko bunkry z koordynatami
- ✅ Django template escaping dla JSON
- ✅ CSRF protection dla wszystkich requestów
- ✅ User authentication check w widoku

## Tłumaczenia

Wszystkie teksty przetłumaczone na polski:
- Mapa → Map
- Legenda → Legend
- Filtry → Filters
- Aktywowany → Activated
- Złowiony → Hunted
- etc.

Plik: `locale/pl/LC_MESSAGES/django.po`

## Testowanie

### Test 1: Niezalogowany użytkownik
1. Otwórz `/map/`
2. Sprawdź czy widzisz czerwone markery
3. Kliknij na marker → popup z nazwą i referencją
4. Sprawdź baner z informacją o zalogowaniu

### Test 2: Zalogowany użytkownik bez QSO
1. Zaloguj się
2. Otwórz `/map/`
3. Wszystkie markery powinny być szare
4. Statystyki: 0 aktywowanych, 0 złowionych, wszystkie nie pracowane

### Test 3: Użytkownik z QSO (np. SP3BLZ - hunter)
1. Zaloguj się jako SP3BLZ
2. Otwórz `/map/`
3. Bunkry które złowił powinny być niebieskie
4. Statystyki powinny pokazywać 3 złowione

### Test 4: Użytkownik z aktywacjami (np. SP3FCK)
1. Zaloguj się jako SP3FCK
2. Otwórz `/map/`
3. Bunkry które aktywował powinny być zielone
4. Jeśli jakieś też złowił → złote

### Test 5: Filtry (wielokrotny wybór)
1. Zaznacz "Gold" → pokaż tylko złote
2. Dodatkowo zaznacz "Activated" → pokaż złote I zielone
3. Dodatkowo zaznacz "Under Activation" → pokaż złote, zielone I pomarańczowe
4. Odznacz "Gold" → pokaż tylko zielone I pomarańczowe
5. Kliknij "Show All" → pokaż wszystkie, wyczyść wszystkie checkboxy

### Test 6: Popup
1. Kliknij marker
2. Sprawdź poprawność danych
3. Sprawdź badge "Under Activation" dla aktywnych spotów
4. Kliknij "Details" → przekierowanie do `/bunkers/{ref}/`

### Test 7: Aktywne spoty
1. Utwórz nowy spot w klastrze dla jakiegoś bunkra
2. Odśwież mapę
3. Bunker powinien być pomarańczowy z ikoną broadcast-pin
4. Poczekaj 30 minut (lub zmień `expires_at` w bazie)
5. Odśwież mapę → bunker powinien wrócić do poprzedniego koloru

## Przyszłe usprawnienia

### 1. Clustering
Dla dużej liczby bunkrów (>100):
```javascript
var markers = L.markerClusterGroup();
markers.addLayer(marker);
map.addLayer(markers);
```

### 2. Heatmap
Pokazanie "gorących" obszarów z największą aktywnością:
```javascript
var heat = L.heatLayer(points, {radius: 25});
```

### 3. Routing
Planowanie trasy do odwiedzenia bunkrów:
```javascript
L.Routing.control({
    waypoints: [bunker1, bunker2, bunker3]
}).addTo(map);
```

### 4. Geolocation
Pokazanie aktualnej lokalizacji użytkownika:
```javascript
map.locate({setView: true, maxZoom: 16});
```

### 5. Search
Wyszukiwanie bunkrów na mapie:
```javascript
var searchControl = new L.Control.Search({
    layer: markersLayer,
    propertyName: 'reference'
});
```

### 6. Export
Eksport widocznych bunkrów do GPX/KML:
```javascript
function exportToGPX() {
    // Generate GPX from visible markers
}
```

### 7. Layers
Różne warstwy mapy (satellite, terrain, topo):
```javascript
var layers = {
    "OpenStreetMap": osmLayer,
    "Satellite": satelliteLayer,
    "Terrain": terrainLayer
};
L.control.layers(layers).addTo(map);
```

## Dokumentacja API

### Endpoint: `/map/`
- **Method**: GET
- **Auth**: Optional (lepsze dane dla zalogowanych)
- **Response**: HTML template z mapą

### Context data:
```python
{
    'bunkers_json': '[{id, reference, name, lat, lng, color, icon, is_activated, is_hunted}, ...]',
    'bunkers_count': 123
}
```

---

**Status**: ✅ Implementacja zakończona
**Tested**: ⚠️ Wymaga testów end-to-end
**Version**: 1.0
**Date**: 2025-11-05

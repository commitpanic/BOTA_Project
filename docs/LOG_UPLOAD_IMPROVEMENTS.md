# Log Upload Improvements

## Podsumowanie zmian

Usprawnienie procesu uploadu logów ADIF - eliminacja komunikatów o duplikatach i przekierowanie do historii logów z podświetleniem nowego rekordu.

## Problem

1. ❌ Przy uploadzielogów zduplikowanych QSO, każdy duplikat generował osobny popup na dashboard
2. ❌ Po uploadzię użytkownik był przekierowywany do dashboard, bez informacji gdzie może zobaczyć szczegóły
3. ❌ Brak połączenia między LogUpload a ActivationLog (QSO)

## Rozwiązanie

### 1. Tworzenie LogUpload podczas importu ✅

**Plik**: `activations/log_import_service.py`

```python
# Na początku process_adif_upload
log_upload = LogUpload.objects.create(
    user=uploader_user,
    filename=filename or 'unknown.adi',
    file_format='ADIF',
    status='processing'
)
self.log_upload = log_upload
```

**Linkowanie QSO z uplodem**:
```python
log = ActivationLog.objects.create(
    # ... inne pola ...
    log_upload=self.log_upload  # Link do batcha
)
```

**Aktualizacja statystyk po zakończeniu**:
```python
log_upload.qso_count = total_qsos
log_upload.processed_qso_count = qsos_processed
log_upload.status = 'completed'
log_upload.save()
```

### 2. Ciche pomijanie duplikatów ✅

**Zmiana w `_process_qso()`**:

Przed:
```python
if existing:
    return {
        'success': False, 
        'error': f'Duplicate QSO with {hunter_callsign} at {qso_datetime}'
    }
```

Po:
```python
if existing:
    return {
        'success': False, 
        'error': None,  # Brak komunikatu błędu
        'duplicate': True
    }
```

**Zmiana w `process_adif_upload()`**:

```python
qsos_duplicates = 0

for qso in self.parser.qsos:
    result = self._process_qso(qso)
    if result['success']:
        qsos_processed += 1
        # ...
    else:
        # Tylko prawdziwe błędy dodawaj do warnings
        if result.get('error'):
            self.warnings.append(result['error'])
        elif result.get('duplicate'):
            qsos_duplicates += 1  # Tylko licznik
```

### 3. Przekierowanie do historii logów ✅

**Plik**: `frontend/views.py` - `upload_log()`

```python
# Sukces bez popup dla każdego duplikatu
success_msg = _(f'Successfully processed {result["qsos_processed"]} new QSOs from {result["bunker"]}.')
if result.get('qsos_duplicates', 0) > 0:
    success_msg += _(f' Skipped {result["qsos_duplicates"]} duplicates.')
if result.get('b2b_qsos', 0) > 0:
    success_msg += _(f' B2B QSOs: {result["b2b_qsos"]}.')

messages.success(request, success_msg)

# Przekierowanie z hashem
log_upload_id = result.get('log_upload_id')
return redirect(f"{reverse('log_history')}#upload-{log_upload_id}")
```

### 4. Podświetlenie nowego uploadu ✅

**Plik**: `templates/log_history.html`

**HTML - dodany ID**:
```html
<tr class="upload-row" id="upload-{{ upload.id }}">
```

**CSS - animacja**:
```css
.upload-row.highlight {
    animation: highlight-fade 3s ease-out;
}

@keyframes highlight-fade {
    0% { background-color: #fff3cd; }
    100% { background-color: transparent; }
}
```

**JavaScript - automatyczne akcje**:
```javascript
window.addEventListener('load', function() {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#upload-')) {
        const uploadRow = document.querySelector(hash);
        if (uploadRow) {
            // 1. Dodaj highlight
            uploadRow.classList.add('highlight');
            
            // 2. Scroll do rekordu
            setTimeout(() => {
                uploadRow.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 100);
            
            // 3. Auto-expand QSOs
            const uploadId = hash.replace('#upload-', '');
            const toggleButton = document.querySelector(`[data-upload-id="${uploadId}"]`);
            if (toggleButton) {
                setTimeout(() => {
                    toggleButton.click();
                }, 500);
            }
            
            // 4. Usuń highlight po 3s
            setTimeout(() => {
                uploadRow.classList.remove('highlight');
            }, 3000);
        }
    }
});
```

### 5. Obsługa błędów ✅

Wszystkie błędy aktualizują status LogUpload:

```python
# Walidacja
if not validation['valid']:
    log_upload.status = 'failed'
    log_upload.error_message = '; '.join(validation['errors'])
    log_upload.save()

# Bunker nie znaleziony
log_upload.status = 'failed'
log_upload.error_message = f"Bunker {bunker_ref} not found"
log_upload.save()

# Security check
log_upload.status = 'failed'
log_upload.error_message = "Security: You can only upload logs for your own callsign"
log_upload.save()
```

## Przepływ działania

### Scenariusz 1: Upload z duplikatami

1. Użytkownik uploaduje plik z 100 QSO (50 nowych, 50 duplikatów)
2. System tworzy `LogUpload` ze statusem "processing"
3. Przetwarza QSO:
   - 50 nowych → tworzy ActivationLog z linkiem do LogUpload
   - 50 duplikatów → pomija cicho (bez warnings)
4. Aktualizuje LogUpload:
   - `qso_count = 100`
   - `processed_qso_count = 50`
   - `status = 'completed'`
5. Pokazuje jeden komunikat: "Successfully processed 50 new QSOs from B/SP-0001. Skipped 50 duplicates."
6. Przekierowuje do `/log-history/#upload-123`
7. Strona ładuje się:
   - Scroll do upload-123
   - Podświetlenie żółte (3s)
   - Auto-expand QSO list
8. Użytkownik widzi wszystkie QSO z tego uploadu

### Scenariusz 2: Upload bez duplikatów

1. Upload 50 nowych QSO
2. Komunikat: "Successfully processed 50 new QSOs from B/SP-0039. B2B QSOs: 5."
3. Przekierowanie z podświetleniem
4. Auto-expand QSO list

### Scenariusz 3: Upload z błędem

1. Upload nieprawidłowego pliku (np. brak bunker ref)
2. LogUpload utworzony ze statusem "failed"
3. Error message zapisany w `log_upload.error_message`
4. Użytkownik widzi błąd i zostaje na stronie upload
5. W historii logów widać upload ze statusem Failed

## Statystyki w LogUpload

| Pole | Opis | Przykład |
|------|------|----------|
| `qso_count` | Wszystkie QSO w pliku | 100 |
| `processed_qso_count` | Nowe QSO (pomijając duplikaty) | 50 |
| `status` | completed / failed / processing | completed |
| `error_message` | Jeśli failed, opis błędu | NULL |

## UX Improvements

### Przed
- ❌ 50 popupów "Duplicate QSO with SP3XXX at 2025-01-01 12:00"
- ❌ Przekierowanie do dashboard (brak info gdzie zobaczyć szczegóły)
- ❌ Trzeba ręcznie szukać swojego uploadu w historii

### Po
- ✅ Jeden komunikat: "50 nowych, 50 pominięto"
- ✅ Automatyczne przekierowanie do historii logów
- ✅ Podświetlenie i scroll do nowego rekordu
- ✅ Automatyczne rozwinięcie listy QSO
- ✅ Wizualna animacja (żółte highlight przez 3s)

## Bezpieczeństwo

- ✅ Sprawdzenie czy uploader = activator (lub is_staff)
- ✅ Wszystkie błędy logowane w LogUpload
- ✅ Transaction atomic - rollback w przypadku błędu
- ✅ Walidacja ADIF przed przetwarzaniem

## Testing

### Test 1: Upload z duplikatami
1. Upload tego samego pliku 2 razy
2. Pierwszy: wszystkie QSO przetworzone
3. Drugi: wszystkie QSO jako duplikaty
4. Sprawdź: jeden komunikat, przekierowanie, podświetlenie

### Test 2: Upload nowego pliku
1. Upload nowego pliku
2. Sprawdź: przekierowanie do log_history
3. Sprawdź: scroll do nowego rekordu
4. Sprawdź: auto-expand QSO list
5. Sprawdź: podświetlenie żółte przez 3s

### Test 3: Upload z błędem
1. Upload pliku bez MY_SIG_INFO
2. Sprawdź: pozostanie na upload_log
3. Sprawdź: komunikat o błędzie
4. Sprawdź w historii: status "failed", error_message wypełniony

## Przyszłe usprawnienia

1. **Edycja duplikatów**: Możliwość nadpisania duplikatu jeśli dane się różnią
2. **Dry-run mode**: Podgląd co zostanie zaimportowane przed właściwym importem
3. **Batch operations**: Usuwanie/ponowne przetwarzanie całego uploadu
4. **Export**: Eksport QSO z danego uploadu do ADIF
5. **Email notifications**: Powiadomienie email po zakończeniu przetwarzania
6. **Progress bar**: Real-time progress podczas importu dużych plików

---

**Status**: ✅ Wszystkie funkcje zaimplementowane
**Tested**: ✅ Syntax check passed
**Version**: 1.0
**Date**: 2025-11-05

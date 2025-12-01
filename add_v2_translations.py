#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add missing translations for V2 improvements
"""

# New translations to add
NEW_TRANSLATIONS = """
# V2 Improvements - Public Statistics
msgid "Public Statistics"
msgstr "Statystyki Publiczne"

msgid "Top activators, hunters, and bunker statistics"
msgstr "Top aktywatorzy, łowcy i statystyki bunkerów"

msgid "Search User Statistics"
msgstr "Wyszukaj Statystyki Użytkownika"

msgid "Enter callsign"
msgstr "Wprowadź znak wywoławczy"

msgid "Top 10 Activators"
msgstr "Top 10 Aktywatorów"

msgid "Top 10 Hunters"
msgstr "Top 10 Łowców"

msgid "No data available"
msgstr "Brak danych"

msgid "Most Active Bunkers"
msgstr "Najbardziej Aktywne Bunkry"

msgid "Activations"
msgstr "Aktywacje"

msgid "Registered Users"
msgstr "Zarejestrowani Użytkownicy"

msgid "Total Activations"
msgstr "Wszystkie Aktywacje"

msgid "Total QSOs"
msgstr "Wszystkie QSO"

# V2 Improvements - Bunker Correction Request
msgid "Suggest Bunker Correction"
msgstr "Zasugeruj Korektę Bunkra"

msgid "Suggest Correction"
msgstr "Zasugeruj Korektę"

msgid "You are suggesting corrections for"
msgstr "Sugerujesz poprawki dla"

msgid "Only fill in the fields you want to change. Leave others empty."
msgstr "Wypełnij tylko pola, które chcesz zmienić. Pozostaw inne puste."

msgid "Current Information"
msgstr "Aktualne Informacje"

msgid "Name (Polish):"
msgstr "Nazwa (polska):"

msgid "Name (English):"
msgstr "Nazwa (angielska):"

msgid "Category:"
msgstr "Kategoria:"

msgid "Coordinates:"
msgstr "Współrzędne:"

msgid "Proposed Changes"
msgstr "Proponowane Zmiany"

msgid "New Name (Polish)"
msgstr "Nowa Nazwa (polska)"

msgid "New Name (English)"
msgstr "Nowa Nazwa (angielska)"

msgid "New Description (Polish)"
msgstr "Nowy Opis (polski)"

msgid "New Description (English)"
msgstr "Nowy Opis (angielski)"

msgid "New Latitude"
msgstr "Nowa Szerokość Geograficzna"

msgid "New Longitude"
msgstr "Nowa Długość Geograficzna"

msgid "Poland: 49-55°N"
msgstr "Polska: 49-55°N"

msgid "Poland: 14-24°E"
msgstr "Polska: 14-24°E"

msgid "Leave empty if no change needed"
msgstr "Zostaw puste jeśli nie wymaga zmiany"

msgid "New Category"
msgstr "Nowa Kategoria"

msgid "Reason for Change"
msgstr "Powód Zmiany"

msgid "Explain why this correction is needed"
msgstr "Wyjaśnij dlaczego ta poprawka jest potrzebna"

msgid "Submit Correction Request"
msgstr "Wyślij Prośbę o Korektę"

msgid "Your correction request has been submitted successfully!"
msgstr "Twoja prośba o korektę została pomyślnie wysłana!"

msgid "It will be reviewed by administrators."
msgstr "Zostanie sprawdzona przez administratorów."

msgid "Back to Bunker"
msgstr "Powrót do Bunkra"

# V2 Improvements - Bunker Details
msgid "Activator Details"
msgstr "Szczegóły Aktywatorów"

msgid "Unique activation sessions"
msgstr "Unikalne sesje aktywacyjne"

msgid "Sessions"
msgstr "Sesje"

msgid "Last Activated"
msgstr "Ostatnio Aktywowany"

msgid "Never activated"
msgstr "Nigdy nie aktywowany"

# V2 Improvements - Map Location Search
msgid "Search location (city, address, coordinates)"
msgstr "Szukaj lokalizacji (miasto, adres, współrzędne)"

msgid "Examples: Warsaw, Krakow, ul. Piotrkowska 1 Łódź, 52.2297,21.0122"
msgstr "Przykłady: Warszawa, Kraków, ul. Piotrkowska 1 Łódź, 52.2297,21.0122"

# V2 Improvements - Models verbose names
msgid "Activator Callsign (with prefix/suffix)"
msgstr "Znak Wywoławczy Aktywatora (z prefiksem/sufiksem)"

msgid "Full callsign used during activation (e.g., SP3FCK/P)"
msgstr "Pełny znak wywoławczy użyty podczas aktywacji (np. SP3FCK/P)"

msgid "Bunker Correction Request"
msgstr "Prośba o Korektę Bunkra"

msgid "Bunker Correction Requests"
msgstr "Prośby o Korektę Bunkerów"

msgid "Requested By"
msgstr "Zgłoszono Przez"

msgid "Requested At"
msgstr "Zgłoszono O"

msgid "Status"
msgstr "Status"

msgid "Pending"
msgstr "Oczekujące"

msgid "Approved"
msgstr "Zatwierdzone"

msgid "Rejected"
msgstr "Odrzucone"

msgid "Reviewed By"
msgstr "Sprawdzone Przez"

msgid "Reviewed At"
msgstr "Sprawdzone O"

msgid "Admin Notes"
msgstr "Notatki Admina"

msgid "Internal notes for administrators"
msgstr "Wewnętrzne notatki dla administratorów"

# V2 Improvements - Admin Actions
msgid "Approve selected correction requests"
msgstr "Zatwierdź wybrane prośby o korektę"

msgid "Reject selected correction requests"
msgstr "Odrzuć wybrane prośby o korektę"

msgid "Approved %(count)d correction request(s)"
msgstr "Zatwierdzono %(count)d prośb(ę) o korektę"

msgid "Rejected %(count)d correction request(s)"
msgstr "Odrzucono %(count)d prośb(ę) o korektę"

# V2 Improvements - Validation Messages
msgid "Latitude must be between 49 and 55 degrees (Poland)"
msgstr "Szerokość geograficzna musi być między 49 a 55 stopni (Polska)"

msgid "Longitude must be between 14 and 24 degrees (Poland)"
msgstr "Długość geograficzna musi być między 14 a 24 stopni (Polska)"

msgid "You must provide at least one field to change"
msgstr "Musisz podać przynajmniej jedno pole do zmiany"

msgid "Maximum 3 ADIF references allowed"
msgstr "Maksymalnie 3 referencje ADIF dozwolone"

msgid "ADIF file contains too many references"
msgstr "Plik ADIF zawiera za dużo referencji"

msgid "Found %(count)d references, maximum is 3"
msgstr "Znaleziono %(count)d referencji, maksimum to 3"

# V2 Improvements - Spot Form
msgid "Start typing bunker reference..."
msgstr "Zacznij wpisywać referencję bunkra..."

"""

def add_translations():
    """Add new translations to django.po file"""
    po_file = 'locale/pl/LC_MESSAGES/django.po'
    
    try:
        # Read current file
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if translations already exist
        if "Public Statistics" in content and "Statystyki Publiczne" in content:
            print("✓ Translations appear to already exist")
            return
        
        # Add new translations at the end
        with open(po_file, 'a', encoding='utf-8') as f:
            f.write('\n')
            f.write(NEW_TRANSLATIONS)
        
        print("✓ Successfully added new translations to django.po")
        print("\nNext steps:")
        print("1. Run: python compile_translations.py")
        print("2. Restart Django development server")
        
    except FileNotFoundError:
        print(f"❌ File not found: {po_file}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    add_translations()

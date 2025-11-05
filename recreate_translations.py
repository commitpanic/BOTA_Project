# -*- coding: utf-8 -*-
"""
Recreate django.po with correct translations
NO CURLY QUOTES - only straight quotes properly escaped
"""

# Read the broken file to extract the working base (first ~900 lines before our additions)
with open('locale/pl/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where we added translations (look for "# Cookie Policy")
cookie_start = None
for i, line in enumerate(lines):
    if '# Cookie Policy' in line:
        cookie_start = i
        break

if cookie_start is None:
    print("❌ Could not find Cookie Policy marker")
    exit(1)

# Keep only the original content before our additions
original_content = ''.join(lines[:cookie_start])

# Now add CORRECTED translations with straight quotes only
CORRECT_TRANSLATIONS = '''
# Cookie Policy
msgid "What Are Cookies?"
msgstr "Czym Są Cookies?"

msgid "Cookies are small text files stored on your device when you visit our website. They help us provide you with a better experience by remembering your preferences and keeping you logged in."
msgstr "Cookies to małe pliki tekstowe przechowywane na Twoim urządzeniu podczas odwiedzania naszej strony. Pomagają nam zapewnić lepsze doświadczenie, zapamiętując Twoje preferencje i utrzymując Cię zalogowanym."

msgid "2. Types of Cookies We Use"
msgstr "2. Rodzaje Używanych Cookies"

msgid "Essential Cookies (Strictly Necessary)"
msgstr "Niezbędne Cookies (Ściśle Konieczne)"

msgid "These cookies are required for the website to function properly:"
msgstr "Te pliki cookie są wymagane do prawidłowego funkcjonowania strony:"

msgid "Cookie Name"
msgstr "Nazwa Cookie"

msgid "Purpose"
msgstr "Cel"

msgid "Duration"
msgstr "Czas Trwania"

msgid "Maintains your login session"
msgstr "Utrzymuje sesję logowania"

msgid "2 weeks"
msgstr "2 tygodnie"

msgid "Security protection against CSRF attacks"
msgstr "Ochrona bezpieczeństwa przed atakami CSRF"

msgid "1 year"
msgstr "1 rok"

msgid "Remembers your language preference (PL/EN)"
msgstr "Zapamiętuje preferencję językową (PL/EN)"

msgid "Preference Cookies (Functional)"
msgstr "Cookies Preferencji (Funkcjonalne)"

msgid "These cookies remember your choices and preferences:"
msgstr "Te pliki cookie zapamiętują Twoje wybory i preferencje:"

msgid "Storage Name"
msgstr "Nazwa Przechowywania"

msgid "Type"
msgstr "Typ"

msgid "Remembers that you accepted cookies/terms"
msgstr "Zapamiętuje, że zaakceptowałeś cookies/regulamin"

msgid "Local Storage"
msgstr "Magazyn Lokalny"

msgid "Remembers scroll position on Spots page"
msgstr "Zapamiętuje pozycję przewijania na stronie Spotów"

msgid "Session Storage"
msgstr "Magazyn Sesji"

msgid "3. Cookies We Do NOT Use"
msgstr "3. Cookies Których NIE Używamy"

msgid "We do not use:"
msgstr "Nie używamy:"

msgid "Analytics cookies (Google Analytics, etc.)"
msgstr "Cookies analitycznych (Google Analytics, itp.)"

msgid "Advertising/marketing cookies"
msgstr "Cookies reklamowych/marketingowych"

msgid "Social media tracking cookies"
msgstr "Cookies śledzących mediów społecznościowych"

msgid "Third-party tracking cookies"
msgstr "Cookies śledzących osób trzecich"

msgid "4. Managing Cookies"
msgstr "4. Zarządzanie Cookies"

msgid "You can control cookies through your browser settings. However, disabling essential cookies may affect website functionality (e.g., you won\\'t be able to log in)."
msgstr "Możesz kontrolować cookies poprzez ustawienia swojej przeglądarki. Jednak wyłączenie niezbędnych cookies może wpłynąć na funkcjonalność strony (np. nie będziesz mógł się zalogować)."

msgid "How to Delete Cookies:"
msgstr "Jak Usunąć Cookies:"

msgid "Settings → Privacy and Security → Clear browsing data"
msgstr "Ustawienia → Prywatność i Bezpieczeństwo → Wyczyść dane przeglądania"

msgid "Options → Privacy & Security → Cookies and Site Data"
msgstr "Opcje → Prywatność i Bezpieczeństwo → Cookies i Dane Strony"

msgid "Preferences → Privacy → Manage Website Data"
msgstr "Preferencje → Prywatność → Zarządzaj Danymi Stron"

msgid "5. Local Storage & Session Storage"
msgstr "5. Magazyn Lokalny i Magazyn Sesji"

msgid "We use browser Local Storage and Session Storage for:"
msgstr "Używamy Magazynu Lokalnego i Sesyjnego przeglądarki do:"

msgid "Remembering your consent (cookies/terms acceptance)"
msgstr "Zapamiętywania Twojej zgody (akceptacja cookies/regulaminu)"

msgid "Preserving scroll position during auto-refresh"
msgstr "Zachowania pozycji przewijania podczas auto-odświeżania"

msgid "This data stays on your device and is never transmitted to our servers."
msgstr "Te dane pozostają na Twoim urządzeniu i nigdy nie są przesyłane na nasze serwery."

msgid "6. Your Consent"
msgstr "6. Twoja Zgoda"

msgid "By clicking \\"Accept\\" on the consent banner, you agree to our use of essential and functional cookies. You can withdraw consent at any time by clearing your browser cookies and local storage."
msgstr "Klikając \\"Akceptuję\\" na banerze zgody, wyrażasz zgodę na używanie przez nas niezbędnych i funkcjonalnych plików cookie. Możesz wycofać zgodę w dowolnym momencie, czyszcząc pliki cookie i magazyn lokalny przeglądarki."

msgid "7. Updates to This Policy"
msgstr "7. Aktualizacje Polityki"

msgid "We may update this cookie policy. Check this page periodically for changes."
msgstr "Możemy aktualizować tę politykę cookies. Sprawdzaj tę stronę okresowo, aby być na bieżąco ze zmianami."

msgid "Questions about cookies?"
msgstr "Pytania dotyczące cookies?"

msgid "Email"
msgstr "Email"

# Terms of Service
msgid "1. Acceptance of Terms"
msgstr "1. Akceptacja Warunków"

msgid "By accessing and using BOTA App, you accept and agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use this application."
msgstr "Uzyskując dostęp i korzystając z BOTA App, akceptujesz i zgadzasz się być związany tymi Warunkami Użytkowania. Jeśli nie zgadzasz się z tymi warunkami, prosimy nie korzystać z tej aplikacji."

msgid "2. About BOTA App"
msgstr "2. O BOTA App"

msgid "BOTA App is a supplementary tool for the \\"Bunkers On The Air\\" (SPBOTA) amateur radio program. The main program is managed and coordinated through <a href=\\"https://www.spbota.pl\\" target=\\"_blank\\">www.spbota.pl</a>, which is the authoritative source for all program rules and regulations."
msgstr "BOTA App jest narzędziem uzupełniającym dla programu krótkofalarskiego \\"Bunkers On The Air\\" (SPBOTA). Główny program jest zarządzany i koordynowany przez <a href=\\"https://www.spbota.pl\\" target=\\"_blank\\">www.spbota.pl</a>, który jest autorytatywnym źródłem wszystkich zasad i regulacji programu."

msgid "This application provides:"
msgstr "Ta aplikacja zapewnia:"

msgid "Online log submission (ADIF format)"
msgstr "Przesyłanie logów online (format ADIF)"

msgid "Activity tracking and statistics"
msgstr "Śledzenie aktywności i statystyki"

msgid "Award/diploma progress tracking"
msgstr "Śledzenie postępów w zdobywaniu dyplomów"

msgid "Real-time spotting system"
msgstr "System zgłoszeń w czasie rzeczywistym"

msgid "Bunker database and management"
msgstr "Baza danych i zarządzanie bunkrami"

msgid "3. User Accounts"
msgstr "3. Konta Użytkowników"

msgid "Registration"
msgstr "Rejestracja"

msgid "To use BOTA App, you must:"
msgstr "Aby korzystać z BOTA App, musisz:"

msgid "Be a licensed amateur radio operator"
msgstr "Być licencjonowanym radioamatorem"

msgid "Provide a valid email address and callsign"
msgstr "Podać ważny adres email i znak wywoławczy"

msgid "Create a secure password"
msgstr "Utworzyć bezpieczne hasło"

msgid "Accept these Terms of Service"
msgstr "Zaakceptować te Warunki Użytkowania"

msgid "Account Security"
msgstr "Bezpieczeństwo Konta"

msgid "You are responsible for:"
msgstr "Jesteś odpowiedzialny za:"

msgid "Maintaining the confidentiality of your password"
msgstr "Zachowanie poufności swojego hasła"

msgid "All activities that occur under your account"
msgstr "Wszystkie działania wykonywane na Twoim koncie"

msgid "Notifying us immediately of any unauthorized access"
msgstr "Natychmiastowe powiadomienie nas o nieautoryzowanym dostępie"

msgid "Account Termination"
msgstr "Zakończenie Konta"

msgid "We reserve the right to suspend or terminate accounts that:"
msgstr "Zastrzegamy sobie prawo do zawieszenia lub zakończenia kont, które:"

msgid "Violate these Terms of Service"
msgstr "Naruszają te Warunki Użytkowania"

msgid "Engage in fraudulent activity or data manipulation"
msgstr "Angażują się w oszukańczą działalność lub manipulację danymi"

msgid "Upload false or misleading information"
msgstr "Przesyłają fałszywe lub wprowadzające w błąd informacje"

msgid "Harass or abuse other users"
msgstr "Nękają lub nadużywają innych użytkowników"

msgid "4. User Conduct"
msgstr "4. Zasady Postępowania Użytkowników"

msgid "You agree NOT to:"
msgstr "Zgadzasz się NIE:"

msgid "Upload false QSO logs or manipulate data"
msgstr "Przesyłać fałszywych logów QSO ani manipulować danymi"

msgid "Use another person\\'s callsign without authorization"
msgstr "Używać znaku wywoławczego innej osoby bez autoryzacji"

msgid "Attempt to gain unauthorized access to the system"
msgstr "Próbować uzyskać nieautoryzowany dostęp do systemu"

msgid "Distribute malware or harmful code"
msgstr "Rozpowszechniać złośliwe oprogramowanie lub szkodliwy kod"

msgid "Scrape or harvest data without permission"
msgstr "Zbierać lub wydobywać danych bez pozwolenia"

msgid "Use the service for commercial purposes without authorization"
msgstr "Używać usługi w celach komercyjnych bez autoryzacji"

msgid "5. ADIF Log Uploads"
msgstr "5. Przesyłanie Logów ADIF"

msgid "When uploading ADIF logs:"
msgstr "Podczas przesyłania logów ADIF:"

msgid "You certify that all contacts are genuine and accurate"
msgstr "Poświadczasz, że wszystkie łączności są autentyczne i dokładne"

msgid "Logs must be in standard ADIF format with required fields"
msgstr "Logi muszą być w standardowym formacie ADIF z wymaganymi polami"

msgid "You are responsible for the accuracy of submitted data"
msgstr "Jesteś odpowiedzialny za dokładność przesyłanych danych"

msgid "Duplicate QSOs will be automatically filtered"
msgstr "Duplikaty QSO będą automatycznie filtrowane"

msgid "6. Spotting System"
msgstr "6. System Zgłoszeń"

msgid "The real-time spotting system is for legitimate activity reports only:"
msgstr "System zgłoszeń w czasie rzeczywistym służy wyłącznie do raportowania legalnej aktywności:"

msgid "Spots must represent actual on-air activations"
msgstr "Spoty muszą reprezentować rzeczywiste aktywacje w eterze"

msgid "False or spam spots may result in account suspension"
msgstr "Fałszywe lub spamowe spoty mogą skutkować zawieszeniem konta"

msgid "Spots expire automatically after 30 minutes"
msgstr "Spoty wygasają automatycznie po 30 minutach"

msgid "7. Intellectual Property"
msgstr "7. Własność Intelektualna"

msgid "The SPBOTA program name, logo, and concept are property of the SPBOTA organization. BOTA App source code and design are protected by copyright. You may not:"
msgstr "Nazwa programu SPBOTA, logo i koncepcja są własnością organizacji SPBOTA. Kod źródłowy i projekt BOTA App są chronione prawem autorskim. Nie możesz:"

msgid "Copy, modify, or redistribute the application code"
msgstr "Kopiować, modyfikować ani redystrybuować kodu aplikacji"

msgid "Use SPBOTA branding for unauthorized purposes"
msgstr "Używać brandingu SPBOTA do nieautoryzowanych celów"

msgid "Reverse engineer the application"
msgstr "Dokonywać inżynierii wstecznej aplikacji"

msgid "8. Disclaimer of Warranties"
msgstr "8. Wyłączenie Gwarancji"

msgid "BOTA App is provided \\"AS IS\\" without warranties of any kind. We do not guarantee:"
msgstr "BOTA App jest dostarczana \\"TAK JAK JEST\\" bez gwarancji jakiegokolwiek rodzaju. Nie gwarantujemy:"

msgid "Uninterrupted or error-free service"
msgstr "Nieprzerwanej lub bezbłędnej usługi"

msgid "Accuracy or completeness of data"
msgstr "Dokładności lub kompletności danych"

msgid "That the service will meet your requirements"
msgstr "Że usługa spełni Twoje wymagania"

msgid "9. Limitation of Liability"
msgstr "9. Ograniczenie Odpowiedzialności"

msgid "We are not liable for:"
msgstr "Nie ponosimy odpowiedzialności za:"

msgid "Data loss or corruption"
msgstr "Utratę lub uszkodzenie danych"

msgid "Service interruptions or downtime"
msgstr "Przerwy w działaniu usługi lub przestoje"

msgid "Incorrect award calculations or statistics"
msgstr "Nieprawidłowe obliczenia dyplomów lub statystyki"

msgid "Third-party actions or content"
msgstr "Działania osób trzecich lub treści"

msgid "10. Program Rules"
msgstr "10. Zasady Programu"

msgid "All SPBOTA program rules and regulations are defined on <a href=\\"https://www.spbota.pl\\" target=\\"_blank\\">www.spbota.pl</a>. This application is a tool to support those rules, not to replace them. In case of any conflict, the official SPBOTA rules prevail."
msgstr "Wszystkie zasady i regulacje programu SPBOTA są zdefiniowane na <a href=\\"https://www.spbota.pl\\" target=\\"_blank\\">www.spbota.pl</a>. Ta aplikacja jest narzędziem wspierającym te zasady, a nie ich zastępującym. W przypadku jakiegokolwiek konfliktu, oficjalne zasady SPBOTA mają pierwszeństwo."

msgid "11. Contact & Support"
msgstr "11. Kontakt i Wsparcie"

msgid "Program Questions & Coordination"
msgstr "Pytania o Program i Koordynacja"

msgid "Please refer to contact information at"
msgstr "Prosimy o kontakt zgodnie z informacjami na"

msgid "Technical Issues with BOTA App"
msgstr "Problemy Techniczne z BOTA App"

msgid "12. Governing Law"
msgstr "12. Prawo Właściwe"

msgid "These Terms are governed by the laws of Poland. Any disputes shall be resolved in Polish courts."
msgstr "Te Warunki podlegają prawu polskiemu. Wszelkie spory będą rozstrzygane przed sądami polskimi."

msgid "13. Changes to Terms"
msgstr "13. Zmiany w Warunkach"

msgid "We reserve the right to modify these Terms at any time. Continued use of the service after changes constitutes acceptance of the new terms. Significant changes will be announced via email and on the website."
msgstr "Zastrzegamy sobie prawo do modyfikacji tych Warunków w dowolnym czasie. Kontynuowanie korzystania z usługi po zmianach stanowi akceptację nowych warunków. Istotne zmiany będą ogłaszane za pośrednictwem poczty elektronicznej i na stronie internetowej."

msgid "14. Severability"
msgstr "14. Rozdzielność"

msgid "If any provision of these Terms is found to be unenforceable, the remaining provisions will remain in full effect."
msgstr "Jeśli jakiekolwiek postanowienie tych Warunków zostanie uznane za niewykonalne, pozostałe postanowienia pozostaną w pełni obowiązujące."

msgid "Summary"
msgstr "Podsumowanie"

msgid "By using BOTA App, you agree to use it honestly for legitimate amateur radio activity, follow SPBOTA program rules, and respect other users. We provide this tool as-is to support the ham radio community."
msgstr "Korzystając z BOTA App, zgadzasz się używać jej uczciwie do legalnej działalności krótkofalarskiej, przestrzegać zasad programu SPBOTA i szanować innych użytkowników. Dostarczamy to narzędzie takie jakie jest, aby wspierać społeczność krótkofalowców."

'''

# Combine
final_content = original_content + CORRECT_TRANSLATIONS

# Write
with open('locale/pl/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ Recreated django.po with correct translations!")
print("📝 Used straight quotes with proper escaping")
print("🔄 Ready to compile")

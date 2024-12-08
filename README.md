Menadżer Depozytów Opon
Opis aplikacji
Menadżer Depozytów Opon to aplikacja do zarządzania depozytami opon oraz stanami magazynowymi. 
Umożliwia przechowywanie informacji o klientach, oponach na stanie, zamówieniach oraz generowanie raportów i drukowanie etykiet.

Funkcje aplikacji

Zarządzanie depozytami opon:
Dodawanie, edytowanie i usuwanie depozytów.
Śledzenie stanu technicznego, dat przechowywania i przewidywanych zwrotów.

Opony na stanie:
Zarządzanie stanami magazynowymi (Marka i model, rozmiar, ilość, cena, DOT).
Dodawanie, edytowanie i usuwanie opon.
Możliwość drukowania etykiet.

Zamówienia:
Zarządzanie zamówieniami klientów.
Możliwość przypisania klienta do zamówienia.
Rejestrowanie dat zamówienia i przewidywanej dostawy.

Ustawienia aplikacji:
Konfiguracja folderów kopii zapasowych.
Zarządzanie szablonami e-mail i ustawieniami drukarek.
Import i eksport kopii zapasowych.

Logi i raporty:
Generowanie i przeglądanie raportów.
Logowanie aktywności użytkowników.

Wymagania systemowe
System operacyjny: Windows 10/11
Python: 3.10 lub nowszy (w przypadku uruchamiania bez instalatora)

Zainstalowane biblioteki:
PyQt5
SQLite3
PyInstaller
win32print (dla obsługi drukowania)


Instrukcja instalacji:

Instalacja aplikacji:
- Pobierz instalator z folderu dist.
- Uruchom plik instalacyjny Menadżer Depozytów Opon Setup.exe jako administrator.
- Wybierz lokalizację instalacji (domyślnie: C:\Program Files\Menadżer Depozytów Opon).
Pierwsze uruchomienie:
- Po zainstalowaniu aplikacji, baza danych zostanie automatycznie utworzona w folderze:
C:\Program Files\Menadżer Depozytów Opon\dane\tire_deposits.db.

Instrukcja aktualizacji
- Uruchom instalator nowej wersji aplikacji.
Aplikator zaktualizuje pliki aplikacji, zachowując istniejące dane w folderze dane.

Znane problemy

1.Błąd uprawnień przy zapisywaniu danych:
- Upewnij się, że aplikacja jest uruchamiana jako administrator.
2.Problemy z drukowaniem etykiet:
- Upewnij się, że drukarka NiiMBot B1 jest poprawnie skonfigurowana i działa.
3.Niepoprawne wyświetlanie danych:
- Sprawdź, czy baza danych nie została uszkodzona. Możesz zaimportować kopię zapasową.
